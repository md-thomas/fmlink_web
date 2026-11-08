"""Persists PATCH /api/settings changes across restarts, so a station
remembers what was set in the web UI instead of reverting to station.env's
launch-time defaults every time it's restarted. settings.json lives next
to station.env (same machine-specific, gitignored state - run.sh always
cd's to the repo root first, so this relative path lands there).
"""
import json
from pathlib import Path

DEFAULT_PATH = Path('settings.json')


def load(path=DEFAULT_PATH):
    path = Path(path)
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save(changes, path=DEFAULT_PATH):
    """changes merged onto whatever's already saved - a settings change
    updates just the keys it touches, not the whole file."""
    path = Path(path)
    current = load(path)
    current.update(changes)
    path.write_text(json.dumps(current, indent=2) + '\n')
