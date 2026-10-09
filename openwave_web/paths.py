"""Puts the open_wave and ota_sim checkouts on sys.path, so ota_station and
its modules import directly (open_wave isn't pip-installed). Must run
before importing any of them.

Defaults to sibling checkouts (open_wave_web, open_wave and ota_sim under
the same parent directory); override with the OPENWAVE_SRC / OTA_SIM_SRC
environment variables.
"""
import os
import sys
from pathlib import Path

_PARENT = Path(__file__).resolve().parents[2]

OPENWAVE_SRC = Path(os.environ.get('OPENWAVE_SRC', _PARENT / 'open_wave'))
OTA_SIM_SRC = Path(os.environ.get('OTA_SIM_SRC', _PARENT / 'ota_sim'))


def install():
    for src in (OPENWAVE_SRC, OTA_SIM_SRC):
        if not src.is_dir():
            raise RuntimeError(f"expected {src} to exist - set OPENWAVE_SRC / OTA_SIM_SRC if your "
                               f"open_wave / ota_sim checkouts aren't next to open_wave_web")
        if str(src) not in sys.path:
            sys.path.insert(0, str(src))
