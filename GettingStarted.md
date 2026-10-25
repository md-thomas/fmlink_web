# Getting started

Installing OpenWave's web interface on a new computer (a radio station
or otherwise).

## 1. System packages

ALSA for audio, plus numpy/scipy/pyserial so the venv can reuse the
system copies instead of compiling them:

```bash
sudo apt install python3-venv python3-numpy python3-scipy python3-serial alsa-utils git
```

## 2. Clone the repos

`openwave` and `ota_sim` are expected next to `openwave_web` (override
with the `OPENWAVE_SRC` / `OTA_SIM_SRC` environment variables if not):

```bash
mkdir -p ~/Projects && cd ~/Projects
git clone https://github.com/md-thomas/openwave.git
git clone https://github.com/md-thomas/ota_sim.git
git clone https://github.com/md-thomas/openwave_web.git
```

## 3. Set up the venv

```bash
cd openwave_web
python3 -m venv --system-site-packages .venv   # reuses numpy/scipy/pyserial
.venv/bin/pip install -e '.[test]'
```

## 4. PTT permission

Skip this step for a VOX interface (e.g. SignaLink) - there's no serial
PTT port to permission; it keys itself off the transmitted audio.

The radio interface's serial PTT port (`/dev/ttyACM0` or `/dev/ttyUSB0`)
is owned `root:dialout`, so without this step PTT silently fails to key
(logged as `[radio tx error] ... - burst NOT sent`, nothing sent). Add
yourself to the group, then log out and back in:

```bash
sudo usermod -aG dialout $USER
```

(For the current plug-in only, as a one-off: `sudo chmod a+rw
/dev/ttyACM0`, resets on replug.)

## 5. Set this station's defaults (optional)

So a plain `./run.sh` (or a restart) always starts this station the same
way, without retyping its arguments every time:

```bash
cp station.env.example station.env
```

Edit `station.env`'s `RUN_ARGS` for this station's own `--station-id`,
`--dst`, `--radio`/`--sim-host`, `--tx-level`, etc. It's gitignored - each
station's is different. Any arguments given on the command line override
it entirely rather than merging with it.

## 6. Run it

```bash
./run.sh --station-id K0MDT-1 --dst K0MDT-2 --radio --tx-level 0.6
```

or, with `station.env` set up:

```bash
./run.sh
```

Then open `http://<this computer's name or address>:8080` from any
browser on the network. `./run.sh --help` lists every option; see the
[README](README.md) for the simulator, the API, and more.
