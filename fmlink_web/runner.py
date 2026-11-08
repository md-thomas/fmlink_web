"""StationRunner: one ota_station.Station plus what the web app needs
around it - the event hub and an outbox that sends typed lines one at a
time, the way the command-line station does.
"""
import asyncio
import sys

from . import settings_store


class StationRunner:
    """station: an ota_station.Station constructed with on_event=hub.publish.
    connect: an async callable that connects it (to a radio or the
    simulator) and returns a short description of the link.
    handle_command: ota_station._handle_command, for '/'-lines."""

    def __init__(self, station, hub, connect, handle_command, settings_path=settings_store.DEFAULT_PATH):
        self.station = station
        self.hub = hub
        self._connect = connect
        self._handle_command = handle_command
        self._outbox = asyncio.Queue()
        self._worker = None
        self.link_note = None
        self.settings_path = settings_path

    async def start(self):
        self.link_note = await self._connect()
        self.station._log(f"[web] station {self.station.station_id} connected, {self.link_note}")
        saved = settings_store.load(self.settings_path)
        if saved:
            try:
                await self.station.update_settings(**saved)
                self.station._log(f"[web] restored saved settings: {', '.join(saved)}")
            except (ValueError, TypeError) as exc:
                self.station._log(f"[web] could not restore saved settings: {exc!r}")
        self.hub.publish({'type': 'link', **self.station.link_state()})
        self._worker = asyncio.create_task(self._send_loop())

    async def stop(self):
        if self._worker is not None:
            self._worker.cancel()
            try:
                await self._worker
            except asyncio.CancelledError:
                pass
        self.station.close()

    def submit(self, line):
        """Queue a chat line or a '/'-command; returns how many are queued
        ahead of it plus one."""
        self._outbox.put_nowait(line)
        return self._outbox.qsize()

    async def _send_loop(self):
        while True:
            line = await self._outbox.get()
            try:
                if line.startswith('/'):
                    await self._handle_command(self.station, line)
                else:
                    await self.station.send_text(line)
            except asyncio.CancelledError:
                raise
            except Exception as exc:   # one bad send mustn't stop the outbox
                self.station._log(f"[web] sending {line[:40]!r} failed: {exc!r}")
                print(f"[web] send error: {exc!r}", file=sys.stderr)
