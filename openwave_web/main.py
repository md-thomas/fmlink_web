"""Run one OpenWave station with its web interface.

  ./run.sh --station-id K0MDT-1 --dst K0MDT-2 --radio --tx-level 0.6
  ./run.sh --station-id K0MDT-1 --dst K0MDT-2 --sim-host 127.0.0.1   # the simulator

Then open http://<this computer>:8080 from a browser on the network. The
station starts with the server and stops with it (Ctrl-C). It runs with
--ack and --auto on (turn them off with --no-ack / --no-auto) and the
audio PHY on the mic port, as on the radios. Anyone on the network can
open the page and transmit; --host 127.0.0.1 keeps it to this computer.
"""
import argparse
import asyncio
import contextlib
import os
import sys

from . import paths

paths.install()

import openwave_audio as audio_phy  # noqa: E402
import openwave_link as link  # noqa: E402
import ota_station  # noqa: E402
import uvicorn  # noqa: E402

from .app import create_app  # noqa: E402
from .hub import EventHub  # noqa: E402
from .runner import StationRunner  # noqa: E402


def build(args):
    """(runner, app) for these arguments; nothing is connected yet."""
    hub = EventHub()
    station = ota_station.Station(
        station_id=args.station_id, dst_id=args.dst, mode_id=args.mode,
        use_fec=True, fec_preset=args.fec_preset, use_ack=not args.no_ack, auto=not args.no_auto,
        bandwidth=args.bandwidth, verbose=args.verbose, phy='audio', audio_port=args.audio_port,
        lead_in_s=args.lead_in_ms / 1000, max_tx_s=args.max_tx_s, batching=not args.no_batch,
        on_event=hub.publish)
    if args.log_file:
        station.open_log_file(args.log_file)
    runner = StationRunner(station, hub, lambda: ota_station.connect_from_args(station, args),
                           ota_station._handle_command)

    @contextlib.asynccontextmanager
    async def lifespan(app):
        try:
            await runner.start()
        except SystemExit as exc:
            # connect_from_args() reports a bad radio/sim setup (e.g. no
            # audio device found) this way; let it through as a clean
            # one-line error instead of the traceback Starlette's own
            # lifespan handling would otherwise log it as.
            print(exc.code, file=sys.stderr)
            os._exit(1)
        try:
            yield
        finally:
            await runner.stop()

    return runner, create_app(runner, lifespan=lifespan)


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--station-id', required=True, help="this station's callsign")
    p.add_argument('--dst', required=True, help="the peer station's callsign")
    p.add_argument('--radio', nargs='?', const='', default=None, metavar='INTERFACE',
                   help='use a real radio (aioc, digirig, ... - see openwave/radio_stations.py)')
    p.add_argument('--sim-host', help='use the ota_sim simulator at this address instead '
                                      '(run it with --channel fm --port mic)')
    p.add_argument('--sim-port', type=int, default=9500)
    p.add_argument('--ptt-line', choices=('dtr', 'rts'), help="override the interface's PTT line")
    p.add_argument('--tx-level', type=float, default=0.5, help='transmit audio level (default 0.5)')
    p.add_argument('--turnaround-ms', type=float, default=None,
                   help='wait after receiving before keying up (default 600)')
    p.add_argument('--audio-port', choices=sorted(audio_phy.PORT_PROFILES), default='mic')
    p.add_argument('--mode', type=int, default=0, choices=sorted(link.WAVEFORM_MODES),
                   help='starting mode (--auto negotiates on the first message)')
    p.add_argument('--fec-preset', help="FEC preset (default: the mode's own)")
    p.add_argument('--bandwidth', choices=('narrow', 'wide'), default='wide')
    p.add_argument('--no-ack', action='store_true', help="don't request ACKs / retry")
    p.add_argument('--no-auto', action='store_true', help="don't negotiate the mode")
    p.add_argument('--no-batch', action='store_true', help="don't offer burst batching")
    p.add_argument('--max-tx-s', type=float, default=ota_station.DEFAULT_MAX_TX_S)
    p.add_argument('--lead-in-ms', type=float, default=audio_phy.DEFAULT_LEAD_IN_S * 1000)
    p.add_argument('--log-file', metavar='PATH', help="the station's per-burst log")
    p.add_argument('--host', default='0.0.0.0',
                   help='address to listen on (default 0.0.0.0: the whole network; '
                        '127.0.0.1: this computer only)')
    p.add_argument('--port', type=int, default=8080)
    p.add_argument('--verbose', '-v', action='store_true')
    args = p.parse_args(argv)
    try:
        link.pack_callsign(args.station_id)
        link.pack_callsign(args.dst)
    except ValueError as exc:
        p.error(str(exc))
    if (args.radio is None) == (args.sim_host is None):
        p.error('give --radio (a real radio) or --sim-host (the simulator)')
    return args


def main(argv=None):
    args = parse_args(argv)
    runner, app = build(args)
    print(f"[web] OpenWave station {args.station_id} - open http://{args.host}:{args.port} "
          f"(0.0.0.0 = any address of this computer)", file=sys.stderr)
    server = uvicorn.Server(uvicorn.Config(app, host=args.host, port=args.port, log_level='warning',
                                           timeout_graceful_shutdown=3))
    try:
        asyncio.run(server.serve())
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
