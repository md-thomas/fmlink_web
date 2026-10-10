# OpenWave web interface

A browser interface for one [OpenWave](../openwave) station: chat with the
peer station, watch the link live, and change settings while it runs. It
runs on the station computer and is opened from any browser on the network,
a phone included. Design and plan: [SCOPE.md](SCOPE.md).

**Status (2026-10-09):** backend done; the Svelte frontend has its first
screens - **Chat** (delivery status per message, segment progress),
**Link** (mode, FEC, batching, peer; an SNR chart of received bursts with
the current mode's limit; the radio's receive level; recent bursts) and
**Log**, plus **Callsigns** and **Settings** (mode, FEC, bandwidth, ACK,
auto, batching, lead-in, max transmission, TX level, turnaround - changed
while running; mode/FEC/batching changes reach the peer too), with a TX/RX
indicator, collapsible and resizable panels, a phone layout and dark mode.
The Radio screen comes next.

## Setup

Expects `openwave` and `ota_sim` checked out next to this repo (override
with `OPENWAVE_SRC` / `OTA_SIM_SRC`):

```
Projects/
  openwave/
  ota_sim/
  openwave_web/   <- this repo
```

```bash
cd ~/Projects/openwave_web
python3 -m venv --system-site-packages .venv   # reuses numpy/scipy and the installed ota_sim
.venv/bin/pip install -e '.[test]'
```

## Run

On the radio (the same settings as `ota_station.py`; `--ack` and `--auto`
are on by default here):

```bash
./run.sh --station-id K0MDT-1 --dst K0MDT-2 --radio --tx-level 0.6
```

or over the simulator (start it first, from `openwave`:
`python3 -m ota_sim.simulator --channel fm --port mic`):

```bash
./run.sh --station-id K0MDT-1 --dst K0MDT-2 --sim-host 127.0.0.1
```

Then open `http://<this computer's name or address>:8080`. The station
starts with the server and stops with it (Ctrl-C). `./run.sh --help` lists
every option.

**Anyone on the network can open the page and transmit** (there's no
password, by choice). `--host 127.0.0.1` limits it to this computer; reach
it from elsewhere with an ssh tunnel (`ssh -L 8080:localhost:8080 station`).

## Frontend

`frontend/` is a Svelte 5 + Vite app. The built files (`frontend/dist/`)
are committed, so a station needs only `git pull`, no Node. To work on it
(Node 20+):

```bash
cd frontend
npm install
npm run dev     # hot reload at http://localhost:5173, /api forwarded to a station on :8080
npm run build   # rebuild dist/ - commit it with the source change
```

Without `frontend/dist/` the server falls back to a minimal placeholder
page (`openwave_web/static/index.html`).

## API

| | |
|---|---|
| `GET /api/state` | snapshot: link state, this session's conversation, recent bursts and log |
| `GET /api/options` | what the settings can be set to: every mode (modulation, symbol rate, default FEC) and FEC preset |
| `POST /api/send` `{"text": "..."}` | send a chat line (queued, sent in order) |
| `POST /api/command` `{"line": "/ping"}` | a station command (`/help` for the list; not `/quit`) |
| `PATCH /api/settings` `{"mode_id": 3, ...}` | change settings while running (`mode_id`, `fec_preset`, `bandwidth`, `ack`, `auto`, `lead_in_s`, `tx_level`, `turnaround_s`, `max_tx_s`, `batching`); 400 with every problem if any value is invalid |
| `WS /api/events` | a `snapshot`, then every event: `link`, `message_tx`, `delivery`, `message_rx`, `burst_rx`, `constellation`, `tx`, `level`, `log` (fields: `ota_station.Station._emit`) |

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -t .
```

Two stations, each with its own server, through an in-process FM
simulator, driven through the real HTTP and WebSocket API.

## License

MIT - see [LICENSE](LICENSE).
