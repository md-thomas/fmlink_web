#!/usr/bin/env bash
# Runs one FMlink station with its web interface (see fmlink_web/main.py
# or ./run.sh --help). Works from any directory.
#
# With no arguments, uses station.env's RUN_ARGS if that file exists (copy
# station.env.example to station.env and fill in this station's own
# --station-id/--dst/--radio/--tx-level, etc. - it's gitignored, since
# every station's is different). Any argument on the command line is a
# full override of station.env, not a merge with it.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python3"
if [ ! -x "$VENV_PYTHON" ]; then
    echo "error: no venv at $SCRIPT_DIR/.venv - set one up first:" >&2
    echo "  cd $SCRIPT_DIR && python3 -m venv --system-site-packages .venv && .venv/bin/pip install -e ." >&2
    exit 1
fi
cd "$SCRIPT_DIR"
if [ "$#" -eq 0 ] && [ -f station.env ]; then
    RUN_ARGS=()
    source station.env
    set -- "${RUN_ARGS[@]}"
fi
exec "$VENV_PYTHON" -m fmlink_web.main "$@"
