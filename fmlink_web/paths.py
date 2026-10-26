"""Puts the fmlink and ota_sim checkouts on sys.path, so ota_station and
its modules import directly (fmlink isn't pip-installed). Must run
before importing any of them.

Defaults to sibling checkouts (fmlink_web, fmlink and ota_sim under
the same parent directory); override with the FMLINK_SRC / OTA_SIM_SRC
environment variables.
"""
import os
import sys
from pathlib import Path

_PARENT = Path(__file__).resolve().parents[2]

# OPENWAVE_SRC is the variable's name from before the FMlink rename.
FMLINK_SRC = Path(os.environ.get('FMLINK_SRC') or os.environ.get('OPENWAVE_SRC')
                  or _PARENT / 'fmlink')
OTA_SIM_SRC = Path(os.environ.get('OTA_SIM_SRC', _PARENT / 'ota_sim'))


def install():
    for src in (FMLINK_SRC, OTA_SIM_SRC):
        if not src.is_dir():
            raise RuntimeError(f"expected {src} to exist - set FMLINK_SRC / OTA_SIM_SRC if your "
                               f"fmlink / ota_sim checkouts aren't next to fmlink_web")
        if str(src) not in sys.path:
            sys.path.insert(0, str(src))
