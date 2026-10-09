#!/usr/bin/env bash
# Runs one OpenWave station with its web interface (see openwave_web/main.py
# or ./run.sh --help). Works from any directory.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python3"
if [ ! -x "$VENV_PYTHON" ]; then
    echo "error: no venv at $SCRIPT_DIR/.venv - set one up first:" >&2
    echo "  cd $SCRIPT_DIR && python3 -m venv --system-site-packages .venv && .venv/bin/pip install -e ." >&2
    exit 1
fi
cd "$SCRIPT_DIR"
exec "$VENV_PYTHON" -m openwave_web.main "$@"
