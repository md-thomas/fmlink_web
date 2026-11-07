# Getting started

Installing FMlink's web interface on a new computer (a radio station
or otherwise). For the whole station - checking the interface, setting
the receive level, a no-radio test over the simulator and
troubleshooting - see fmlink's
[INSTALL.md](https://github.com/md-thomas/fmlink/blob/main/INSTALL.md).

Once you've cloned this repo (step 2 still has to happen by hand - it's
what gets you `install.sh`), it does the rest of steps 1-5 for you:
system packages, the sibling repos, the venv, PTT permission and
`station.env`. Safe to re-run, e.g. after a `git pull`:

```bash
./install.sh
```

Or do each step by hand, or to understand what it did:

## 1. System packages

ALSA for audio, plus numpy/scipy/pyserial so the venv can reuse the
system copies instead of compiling them:

```bash
sudo apt install python3-venv python3-numpy python3-scipy python3-serial alsa-utils git
```

## 2. Clone the repos

`fmlink` and `ota_sim` are expected next to `fmlink_web` (override
with the `FMLINK_SRC` / `OTA_SIM_SRC` environment variables if not):

```bash
mkdir -p ~/Projects && cd ~/Projects
git clone https://github.com/md-thomas/fmlink.git
git clone https://github.com/md-thomas/ota_sim.git
git clone https://github.com/md-thomas/fmlink_web.git
```

## 3. Set up the venv

```bash
cd fmlink_web
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
station's ID is different. Any arguments given on the command line override
it entirely rather than merging with it.

## 6. Run it

```bash
./run.sh --station-id <callsign>-1 --dst <callsign>-2 --radio --tx-level 0.6
```

or, with `station.env` set up:

```bash
./run.sh
```

Then open `http://<this computer's name or address>:8080` from any
browser on the network. `./run.sh --help` lists every option; see the
[README](README.md) for the simulator, the API, and more.

## 7. Run it as a systemd user service (optional)

So it starts on boot/login and restarts itself if it ever crashes,
instead of needing a terminal open running `./run.sh`. Needs step 5
(`station.env`) done first - the service runs a bare `./run.sh`, with no
arguments of its own:

```bash
mkdir -p ~/.config/systemd/user
sed "s#%INSTALL_DIR%#$(pwd)#" systemd/fmlink-station.service.example \
    > ~/.config/systemd/user/fmlink-station.service
systemctl --user daemon-reload
systemctl --user enable --now fmlink-station.service
loginctl enable-linger $USER   # keep it running after you log out
```

Check it with `systemctl --user status fmlink-station` and
`journalctl --user -u fmlink-station -f`. `systemctl --user restart
fmlink-station` restarts it (e.g. after `git pull`); `systemctl --user
stop fmlink-station` to run `./run.sh` by hand instead.

If it fails with an ALSA permission error when started this way but
works fine run by hand, this account is probably getting its `/dev/snd`
access from a logged-in desktop session (logind's seat ACL) rather than
the `audio` group - add yourself to it: `sudo usermod -aG audio $USER`,
then log out and back in (or reboot) before relying on this unattended.
