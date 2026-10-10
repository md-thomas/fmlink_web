"""The FastAPI app: REST for actions and settings, a WebSocket for the live
event stream, and the frontend's static files.

  GET   /api/state       snapshot: link state, conversation, bursts, log
  GET   /api/options     what the settings can be set to (modes, FEC presets)
  POST  /api/send        {"text": "..."}  - a chat line (queued, sent in order)
  POST  /api/command     {"line": "/ping"} - a station command
  PATCH /api/settings    {"mode_id": 3, ...} - Station.update_settings();
                         400 with the reason if any value is invalid
  POST  /api/radio-test  {"kind": "carrier"|"tone", "seconds": 1} - key the
                         radio (Station.radio_test); 400 off a radio
  WS    /api/events      a snapshot first, then every event as it happens
"""
import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

HERE = Path(__file__).resolve().parent
FRONTEND_DIST = HERE.parent / 'frontend' / 'dist'   # the built Svelte app (step 3)
PLACEHOLDER = HERE / 'static' / 'index.html'         # until then


class SendBody(BaseModel):
    text: str


class CommandBody(BaseModel):
    line: str


class RadioTestBody(BaseModel):
    kind: str = 'carrier'
    seconds: float = 1.0


def options():
    """Choices for the settings screen: every Waveform Mode (with its
    default FEC preset and symbol rate - link state's max_symbol_rate says
    which this station can use) and every FEC preset."""
    import openwave_fec as fec
    import openwave_link as link
    return {
        'modes': [{'mode_id': mode_id, 'modulation': m['modulation'], 'symbol_rate': m['symbol_rate'],
                   'fec_preset': m['fec_preset']} for mode_id, m in sorted(link.WAVEFORM_MODES.items())],
        'fec_presets': sorted(fec.PRESETS),
    }


def create_app(runner, lifespan=None):
    app = FastAPI(title='OpenWave station', lifespan=lifespan)
    hub = runner.hub

    @app.get('/api/state')
    async def state():
        return hub.snapshot(runner.station.link_state())

    @app.get('/api/options')
    async def get_options():
        return options()

    @app.post('/api/send')
    async def send(body: SendBody):
        text = body.text.strip()
        if not text:
            raise HTTPException(400, 'empty message')
        if text.startswith('/'):
            raise HTTPException(400, 'commands go to /api/command')
        return {'queued': runner.submit(text)}

    @app.post('/api/command')
    async def command(body: CommandBody):
        line = body.line.strip()
        if not line.startswith('/'):
            raise HTTPException(400, "a command starts with '/'")
        if line.split()[0].lower() in ('/quit', '/exit'):
            raise HTTPException(400, 'stop the station from its computer, not the page')
        return {'queued': runner.submit(line)}

    @app.patch('/api/settings')
    async def settings(changes: dict):
        try:
            return await runner.station.update_settings(**changes)
        except ValueError as exc:
            raise HTTPException(400, str(exc))

    @app.post('/api/radio-test')
    async def radio_test(body: RadioTestBody):
        try:
            runner.station.radio_test(body.kind, body.seconds)
        except ValueError as exc:
            raise HTTPException(400, str(exc))
        return {'queued': True}

    @app.websocket('/api/events')
    async def events(websocket: WebSocket):
        await websocket.accept()
        queue = hub.subscribe()

        async def forward():
            await websocket.send_json(hub.snapshot(runner.station.link_state()))
            while True:
                await websocket.send_json(await queue.get())

        async def until_closed():   # pages send nothing; this just notices them leave
            while (await websocket.receive())['type'] != 'websocket.disconnect':
                pass

        tasks = [asyncio.create_task(forward()), asyncio.create_task(until_closed())]
        try:
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            hub.unsubscribe(queue)

    if FRONTEND_DIST.is_dir():
        app.mount('/', StaticFiles(directory=FRONTEND_DIST, html=True), name='frontend')
    else:
        @app.get('/')
        async def placeholder():
            return FileResponse(PLACEHOLDER)

    return app
