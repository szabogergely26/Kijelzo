"""
X11 / xrandr segédek a Monitor Config alkalmazáshoz.
"""

import re
import time

from .autodetect import normalize_connected_outputs
from .command_utils import run_cmd
from .config import DRY_RUN
from .log_utils import log


def run_x11_commands(commands, logf):
    if DRY_RUN:
        for cmd in commands:
            log(logf, "[DRY] would run X11:", cmd)

        return True, "OK (dry-run)"

    for cmd in commands:
        if cmd.startswith("sleep "):
            try:
                seconds = float(cmd.split()[1])
                time.sleep(seconds)
            except Exception:
                time.sleep(0.5)

            continue

        rc, out, err = run_cmd(cmd, logf)

        if rc != 0:
            return False, (err or out or f"Hiba: {cmd}").strip()

    return True, "OK"


def x11_connected_outputs(f=None):
    """
    X11 alatt visszaadja a csatlakoztatott kimenetek nevét set-ként.
    Példa elemek: {'eDP-1', 'HDMI-A-1', 'DP-2'}
    """

    rc, out, err = run_cmd("xrandr --query", f)

    if rc != 0:
        raise RuntimeError(f"xrandr lekérdezés sikertelen: {err.strip() or 'ismeretlen hiba'}")

    connected = set()

    for line in out.splitlines():
        m = re.match(r"^(\S+)\s+connected\b", line)

        if m:
            connected.add(m.group(1))

    return connected


def x11_active_outputs(f=None):
    """
    X11 alatt visszaadja az AKTÍV kimenetek nevét set-ként.

    Csak az számít aktívnak, ahol a sorban van aktuális mód + pozíció,
    pl. '1920x1200+0+0'.
    """

    rc, out, err = run_cmd("xrandr --query", f)

    if rc != 0:
        raise RuntimeError(f"xrandr lekérdezés sikertelen: {err.strip() or 'ismeretlen hiba'}")

    active = set()

    for line in out.splitlines():
        if " connected" not in line:
            continue

        if re.search(r"\b\d{3,4}x\d{3,4}\+\d+\+\d+\b", line):
            name = line.split()[0]
            active.add(name)

    return active


def detect_current_active_setup(f=None):
    """
    Az aktuálisan AKTÍV X11 elrendezést próbálja profilnévre fordítani.
    """

    raw = x11_active_outputs(f)
    norm = normalize_connected_outputs(raw)

    if f:
        log(f, f"[ACTIVE-DETECT] raw_active={sorted(raw)}")
        log(f, f"[ACTIVE-DETECT] normalized={sorted(norm)}")

    if norm == {"eDP"}:
        return "Laptop (csak)"

    if norm == {"eDP", "DP"}:
        return "Laptop + Soundbar"

    if norm == {"eDP", "HDMI", "DP"}:
        return "Laptop + TV + Soundbar"

    if norm == {"eDP", "HDMI"}:
        return "Köztes állapot: Laptop + TV"

    return "ismeretlen"