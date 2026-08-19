# -*- coding: utf-8 -*-

import re
import time

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
    Példa elemek: {'eDP', 'HDMI-1-0', 'DP-1-0'}
    """
    rc, out, err = run_cmd("xrandr --query", f)
    if rc != 0:
        raise RuntimeError(
            f"xrandr lekérdezés sikertelen: {err.strip() or 'ismeretlen hiba'}"
        )

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
    például: '1920x1080+0+0'.
    """
    rc, out, err = run_cmd("xrandr --query", f)
    if rc != 0:
        raise RuntimeError(
            f"xrandr lekérdezés sikertelen: {err.strip() or 'ismeretlen hiba'}"
        )

    active = set()

    for line in out.splitlines():
        if " connected" not in line:
            continue

        if re.search(r"\b\d{3,4}x\d{3,4}\+\d+\+\d+\b", line):
            name = line.split()[0]
            active.add(name)

    return active
