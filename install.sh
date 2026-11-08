#!/usr/bin/env bash
# One-shot setup for a new FMlink station computer: system packages, the
# sibling repos (fmlink, ota_sim), this repo's venv, PTT permission,
# station.env, and (optionally) a systemd user service. See
# GettingStarted.md for what each step does and how to do it by hand
# instead. Safe to re-run (e.g. after a git pull) - it skips anything
# already done.
#
# Verified 2026-11-07 re-run on two already-set-up stations (K0MDT-1,
# K0MDT-2/hampi): every step correctly detected its prior work and
# skipped, and the running station was undisturbed.
#
#   ./install.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "== 1. System packages =="
sudo apt-get update
sudo apt-get install -y python3-venv python3-numpy python3-scipy python3-serial alsa-utils git

echo
echo "== 2. Sibling repos (fmlink, ota_sim) =="
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
for repo in fmlink ota_sim; do
    if [ -d "$PARENT_DIR/$repo" ]; then
        echo "$repo: already at $PARENT_DIR/$repo"
    else
        git clone "https://github.com/md-thomas/$repo.git" "$PARENT_DIR/$repo"
    fi
done

echo
echo "== 3. Python venv =="
if [ -x .venv/bin/python3 ]; then
    echo "venv already set up"
else
    python3 -m venv --system-site-packages .venv
fi
.venv/bin/pip install -e '.[test]'

echo
echo "== 4. PTT permission (dialout group) =="
NEEDS_RELOGIN=0
if groups "$USER" | grep -qw dialout; then
    echo "already in dialout"
else
    sudo usermod -aG dialout "$USER"
    NEEDS_RELOGIN=1
fi

echo
echo "== 5. station.env =="
CALLSIGN_RE='^[A-Za-z0-9/.-]{1,9}$'
if [ -f station.env ]; then
    echo "station.env already exists - leaving it alone"
elif [ -t 0 ]; then
    read -rp "This station's callsign (e.g. K0MDT-1): " STATION_ID
    while ! [[ "$STATION_ID" =~ $CALLSIGN_RE ]]; do
        echo "up to 9 characters: A-Z, 0-9, /, -, . only"
        read -rp "This station's callsign (e.g. K0MDT-1): " STATION_ID
    done
    read -rp "The other station's callsign, --dst (e.g. K0MDT-2): " DST_ID
    while ! [[ "$DST_ID" =~ $CALLSIGN_RE ]]; do
        echo "up to 9 characters: A-Z, 0-9, /, -, . only"
        read -rp "The other station's callsign, --dst (e.g. K0MDT-2): " DST_ID
    done
    cat > station.env <<EOF
RUN_ARGS=(
    --station-id ${STATION_ID^^}
    --dst ${DST_ID^^}
    --radio
    --tx-level 0.6
)
EOF
    echo "Wrote station.env for ${STATION_ID^^} <-> ${DST_ID^^}."
else
    cp station.env.example station.env
    echo "Not an interactive shell - copied station.env.example to station.env." \
         "Edit its RUN_ARGS before running."
fi

echo
echo "== 6. systemd user service (optional) =="
SERVICE_FILE="$HOME/.config/systemd/user/fmlink-station.service"
SERVICE_INSTALLED=0
if [ -f "$SERVICE_FILE" ]; then
    echo "already installed: $SERVICE_FILE"
    SERVICE_INSTALLED=1
elif [ -t 0 ]; then
    read -rp "Start this station on boot/login and restart it if it crashes (systemd --user)? [Y/n] " ANSWER
    if [[ ! "$ANSWER" =~ ^[Nn] ]]; then
        mkdir -p "$HOME/.config/systemd/user"
        sed "s#%INSTALL_DIR%#$SCRIPT_DIR#" systemd/fmlink-station.service.example > "$SERVICE_FILE"
        systemctl --user daemon-reload
        systemctl --user enable --now fmlink-station.service
        loginctl enable-linger "$USER" 2>/dev/null \
            || echo "loginctl enable-linger failed - the service needs you logged in until this is run (as root, or check polkit)"
        echo "Installed, enabled and started: systemctl --user status fmlink-station"
        SERVICE_INSTALLED=1
    fi
else
    echo "Not an interactive shell - skipped. See GettingStarted.md's systemd step to set it up."
fi

echo
echo "================================================================"
echo "Setup done."
[ "$NEEDS_RELOGIN" = 1 ] && echo "- Log out and back in for the dialout group (PTT) to take effect."
echo "- Check the radio interface is found: $PARENT_DIR/fmlink/radio_stations.py"
if [ "$SERVICE_INSTALLED" = 1 ]; then
    echo "- Review station.env, then: systemctl --user restart fmlink-station"
else
    echo "- Review station.env, then run the station: ./run.sh"
fi
