# Scope: OpenWave web interface

Status: **accepted (2026-10-09). Step 1 done in open_wave (event feed `d639e2a`, live settings `1bb051d`). Step 2 done: the backend (FastAPI app, event hub, outbox, `run.sh`, tests). Step 3 under way: the Svelte frontend's Chat, Link and Log screens work (built files committed in `frontend/dist`); Settings and Radio screens next.**

A browser interface for one OpenWave station: chat, live link status,
settings that change while it runs, the radio's levels, and diagnostics.
It runs on the station computer (a laptop now, maybe a headless Raspberry
Pi later) and is opened from any browser on the home network, including a
phone.

## Decisions so far (2026-10-09)

- **New repo, `open_wave_web`**, next to `open_wave` and `ota_sim` (like
  `ota_sim`, it imports `open_wave`'s modules). `open_wave_ui` (the
  customtkinter desktop GUI, simulator only) stays as it is for now.
- **Frontend: Svelte + Vite**, built once into static files that the
  backend serves.
- **Backend: Python (FastAPI)** in the same process and event loop as the
  station.
- **One station per page.** Each station runs its own server; watch both
  in two browser tabs.
- **Open on the home network, no password.** Anyone on the network who
  opens the page can key the transmitter. The listen address is one
  setting (`--host`, default `0.0.0.0`), so it can be narrowed to
  `127.0.0.1` (plus an ssh tunnel) if that changes.

## Architecture

```
 phone / laptop browser ──HTTP + WebSocket──┐
                                            v
 ┌──────────────── station computer: one Python process ───────────────┐
 │  FastAPI (uvicorn)                                                   │
 │   ├─ static files: the built Svelte app                              │
 │   ├─ REST: actions and settings  (POST /api/send, PATCH /api/settings)│
 │   └─ WebSocket /api/events: live event stream to every open page     │
 │                        │                                             │
 │        ota_station.Station  (+ Tnc in TNC mode)  - same asyncio loop │
 │                        │                                             │
 │        openwave_radio.RadioTransport  ── AIOC/Digirig ── the radio   │
 │        (or ota_sim, for testing without a radio)                     │
 └──────────────────────────────────────────────────────────────────────┘
```

- The backend owns the `Station` exactly as `ota_station.py`'s `run()`
  does today (same arguments: station ID, peer, `--radio`, levels,
  turnaround, batching...). Starting the server starts the station.
- Every connected page gets the same event stream; any page can act.
- A page that connects late gets a snapshot (current settings, link
  state, the last N messages and bursts) and then the live stream.

## Changes needed in `open_wave`

1. **A structured event feed.** Today the station reports through log
   text (`on_log`), `on_message` and `on_symbols`. Add one optional
   `on_event(dict)` callback with typed events (the CLI ignores it):

   | Event | Fields |
   |---|---|
   | `message_rx` | from, text, segments |
   | `message_tx` | id, to, text, segments, batches |
   | `delivery` | id, acked segments / total, done, failed |
   | `burst_rx` | mode, modulation, symbol rate, status, SNR, sync quality, fading, peak |
   | `tx` | keyed / released, airtime, bursts batched |
   | `link` | mode, FEC, batching on/off, peer, last negotiation result |
   | `level` | receive audio rms and peak (dBFS), a few times a second |
   | `log` | the existing log lines, for the log view |
   | `constellation` | a decimated set of symbol points per burst |

2. **Settings that change while running**, through methods rather than
   typed `/commands`: mode, FEC, bandwidth, lead-in, transmit level,
   turnaround, max transmission time, batching, ACK, auto-negotiate. Most
   exist as `/commands` already (`_handle_command`); transmit level,
   turnaround and max transmission time need small setters.
3. **A receive-level tap** in `RadioTransport`'s capture loop (rms and
   peak per chunk), replacing `level_meter.py`'s separate recording,
   which can't run while a station holds the sound card.

## Screens

1. **Chat** - the conversation with the peer; each sent message shows its
   delivery progress (segments acknowledged, batches), then delivered or
   failed. Commands (`/ping`, ...) can still be typed.
2. **Link** - current mode, FEC, batching, peer; SNR of each received
   burst over time (with mode 2/3 cliffs marked); TX / RX indicator;
   negotiation history.
3. **Settings** - everything in item 2 above, applied immediately and
   remembered for the next start.
4. **Radio** - the detected interface (AIOC / Digirig, PTT line), the live
   receive-level meter with the target zone, a PTT test button (keys for
   one second, with a confirmation).
5. **Diagnostics** - constellation of the last bursts, the log (filterable),
   and later the test tools (`radio_link_test`, `radio_response`).
6. **TNC** (when started as a KISS TNC) - connected KISS hosts, AX.25
   frames each way, the pty path for `kissattach`.

Mobile layout: chat and link status first; the rest behind tabs.

## Plan

1. **Event feed + settings setters + level tap** in `open_wave` (tests
   first; the CLI unchanged).
2. **Backend skeleton** in `open_wave_web`: FastAPI app that starts a
   station, REST for send and settings, WebSocket events; tested against
   the simulator.
3. **MVP frontend:** Chat and Link screens. Try it over the radios.
4. Settings and Radio screens (level meter).
5. Diagnostics, then the TNC screen.

## Running it (planned)

```bash
cd ~/Projects/open_wave_web
./run.sh --station-id K0MDT-1 --dst K0MDT-2 --radio --tx-level 0.6
# then open http://<station computer>:8080 from any browser on the network
```

## Decided (2026-10-09, cont.)

1. Port **8080**.
2. The station **starts with the server and runs until it stops**; the
   page doesn't start/stop it or switch to TNC mode (later, maybe).
3. Message history is kept **for the running session only**.
