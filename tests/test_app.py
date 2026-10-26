"""Two stations, each with its web server, talking through an in-process
ota_sim FM simulator; driven through the real HTTP and WebSocket API.

  .venv/bin/python -m unittest discover -s tests
"""
import asyncio
import json
import unittest

import httpx
import uvicorn
import websockets

from fmlink_web import main as web_main
from fmlink_web.hub import EventHub, json_safe

from ota_sim import FMLink  # noqa: E402  (paths installed by fmlink_web.main)
from ota_sim.simulator import OTASimulator  # noqa: E402


async def start_server(app):
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=0, log_level='warning',
                                           timeout_graceful_shutdown=3))
    task = asyncio.create_task(server.serve())
    for _ in range(200):
        if server.started:
            break
        await asyncio.sleep(0.05)
    port = server.servers[0].sockets[0].getsockname()[1]
    return server, task, f'127.0.0.1:{port}'


async def stop_server(server, task):
    server.should_exit = True
    await asyncio.wait_for(task, timeout=10)


async def next_event(ws, kind, timeout=30, where=lambda e: True):
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        event = json.loads(await asyncio.wait_for(ws.recv(), deadline - loop.time()))
        if event['type'] == kind and where(event):
            return event
    raise AssertionError(f'no {kind} event within {timeout} s')


class HubTests(unittest.TestCase):
    def test_json_safe(self):
        self.assertEqual(json_safe({'snr_db': float('-inf'), 'x': [1.5, float('nan')]}),
                         {'snr_db': None, 'x': [1.5, None]})

    def test_history_and_snapshot(self):
        hub = EventHub()
        hub.publish({'type': 'link', 'mode_id': 2})
        hub.publish({'type': 'message_rx', 'src': 'W1AW', 'text': 'hi'})
        hub.publish({'type': 'burst_rx', 'snr_db': float('-inf')})
        hub.publish({'type': 'constellation', 'points': [[0, 1]]})
        hub.publish({'type': 'constellation', 'points': [[1, 0]]})
        hub.publish({'type': 'constellation', 'points': [[0, -1]]})
        snap = hub.snapshot()
        self.assertEqual([c['points'] for c in snap['constellations']], [[[1, 0]], [[0, -1]]])
        self.assertEqual(snap['link']['mode_id'], 2)
        self.assertEqual([m['text'] for m in snap['messages']], ['hi'])
        self.assertIsNone(snap['bursts'][0]['snr_db'])
        json.dumps(snap)


class WebStationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.sim = await OTASimulator(FMLink('mic', base_cnr_db=25, latency_s=0.01, jitter_s=0.0, seed=9),
                                      log=lambda msg: None).start('127.0.0.1', 0)
        sim_host, sim_port = self.sim.address
        self.servers = {}
        for me, peer in (('K0MDT', 'W1AW'), ('W1AW', 'K0MDT')):
            args = web_main.parse_args(['--station-id', me, '--dst', peer, '--sim-host', sim_host,
                                        '--sim-port', str(sim_port), '--mode', '2', '--no-auto'])
            runner, app = web_main.build(args)
            runner.station._on_log = lambda msg: None
            self.servers[me] = (runner, *await start_server(app))

    async def asyncTearDown(self):
        for runner, server, task, _ in self.servers.values():
            await stop_server(server, task)
        self.sim.close()

    def url(self, who, path, ws=False):
        return f"{'ws' if ws else 'http'}://{self.servers[who][3]}{path}"

    async def test_state_and_snapshot(self):
        async with httpx.AsyncClient() as client:
            state = (await client.get(self.url('K0MDT', '/api/state'))).json()
        self.assertEqual(state['type'], 'snapshot')
        self.assertEqual((state['link']['station_id'], state['link']['dst_id'], state['link']['mode_id']),
                         ('K0MDT', 'W1AW', 2))
        self.assertTrue(state['link']['connected'])
        async with httpx.AsyncClient() as client:
            opts = (await client.get(self.url('K0MDT', '/api/options'))).json()
        self.assertIn({'mode_id': 3, 'modulation': 'qpsk', 'symbol_rate': 2400, 'fec_preset': 'r1_2_k7'},
                      opts['modes'])
        self.assertIn('r1_2_k3', opts['fec_presets'])
        async with httpx.AsyncClient() as client:
            page = await client.get(self.url('K0MDT', '/'))
        self.assertEqual(page.status_code, 200)
        self.assertIn('FMlink station', page.text)

    async def test_a_message_from_one_page_to_the_other(self):
        async with websockets.connect(self.url('K0MDT', '/api/events', ws=True)) as ws_a, \
                websockets.connect(self.url('W1AW', '/api/events', ws=True)) as ws_b:
            self.assertEqual(json.loads(await ws_a.recv())['type'], 'snapshot')
            self.assertEqual(json.loads(await ws_b.recv())['type'], 'snapshot')
            async with httpx.AsyncClient() as client:
                r = await client.post(self.url('K0MDT', '/api/send'), json={'text': 'hello from the web'})
            self.assertEqual(r.status_code, 200)
            sent = await next_event(ws_a, 'message_tx')
            self.assertEqual(sent['text'], 'hello from the web')
            got = await next_event(ws_b, 'message_rx')
            self.assertEqual((got['src'], got['text']), ('K0MDT', 'hello from the web'))
            done = await next_event(ws_a, 'delivery', where=lambda e: e['done'])
            self.assertEqual(done['id'], sent['id'])
            self.assertFalse(done['failed'])
        # A page that connects now catches up from the snapshot.
        async with httpx.AsyncClient() as client:
            state = (await client.get(self.url('W1AW', '/api/state'))).json()
        self.assertIn('hello from the web', [m.get('text') for m in state['messages']])
        self.assertTrue(state['bursts'])

    async def test_settings(self):
        async with websockets.connect(self.url('K0MDT', '/api/events', ws=True)) as ws:
            await ws.recv()   # snapshot
            async with httpx.AsyncClient() as client:
                bad = await client.patch(self.url('K0MDT', '/api/settings'),
                                         json={'max_tx_s': 0, 'nonsense': 1})
                good = await client.patch(self.url('K0MDT', '/api/settings'), json={'max_tx_s': 20})
            self.assertEqual(bad.status_code, 400)
            self.assertIn('max_tx_s', bad.json()['detail'])
            self.assertIn('nonsense', bad.json()['detail'])
            self.assertEqual(good.status_code, 200)
            self.assertEqual(good.json()['max_tx_s'], 20.0)
            async with httpx.AsyncClient() as client:
                bad_call = await client.patch(self.url('K0MDT', '/api/settings'), json={'dst_id': 'K0#DT'})
                rename = await client.patch(self.url('K0MDT', '/api/settings'), json={'dst_id': 'w1aw-2'})
            self.assertEqual(bad_call.status_code, 400)
            self.assertIn("'#' is not allowed", bad_call.json()['detail'])
            self.assertEqual(rename.json()['dst_id'], 'W1AW-2')
            link = await next_event(ws, 'link', where=lambda e: e['max_tx_s'] == 20.0)
            self.assertEqual(link['station_id'], 'K0MDT')

    async def test_commands_and_bad_requests(self):
        async with httpx.AsyncClient() as client:
            quit_ = await client.post(self.url('K0MDT', '/api/command'), json={'line': '/quit'})
            not_cmd = await client.post(self.url('K0MDT', '/api/command'), json={'line': 'hello'})
            empty = await client.post(self.url('K0MDT', '/api/send'), json={'text': '  '})
            modes = await client.post(self.url('K0MDT', '/api/command'), json={'line': '/modes'})
        self.assertEqual((quit_.status_code, not_cmd.status_code, empty.status_code), (400, 400, 400))
        self.assertEqual(modes.status_code, 200)
        async with httpx.AsyncClient() as client:
            test = await client.post(self.url('K0MDT', '/api/radio-test'), json={'kind': 'tone'})
            state = (await client.get(self.url('K0MDT', '/api/state'))).json()
        self.assertEqual(test.status_code, 400)            # the simulator isn't a radio
        self.assertIn('real radio', test.json()['detail'])
        self.assertIsNone(state['link']['radio'])


if __name__ == '__main__':
    unittest.main()
