# -*- coding: utf-8 -*-

from .log_utils import log
from .x11 import x11_active_outputs, x11_connected_outputs


def normalize_connected_outputs(raw_names: set[str]) -> set[str]:
    """
    Különböző rendszerek / driverek eltérő neveit közös logikai nevekre húzza össze.
    """
    norm = set()

    for name in raw_names:
        low = name.lower()

        # belső kijelző
        if low in {"edp", "edp-1", "edp1"}:
            norm.add("eDP")
            continue

        # HDMI
        if (
            low in {"hdmi-a-0", "hdmi-a-1", "hdmi-0", "hdmi-1", "hdmi"}
            or low.startswith("hdmi")
        ):
            norm.add("HDMI")
            continue

        # DP / soundbar
        if (
            low in {"dp-2", "displayport-2", "displayport-1", "dp2", "dp1"}
            or "displayport" in low
            or low.startswith("dp-")
        ):
            norm.add("DP")
            continue

    return norm


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

    if {"eDP", "HDMI", "DP"}.issubset(norm):
        return "Laptop + TV + Soundbar"

    if {"eDP", "HDMI"}.issubset(norm):
        return "Laptop + TV + Soundbar"

    return "ismeretlen"


def detect_current_setup(f=None, is_wayland_func=None):
    """
    Visszaad:
      (profil_név, részletes_szöveg)

    Lenovo LOQ-only fix verzió:
      eDP      = laptop kijelző
      HDMI-1-0 = LG TV
      DP-1-0   = Citation / Soundbar HDMI audio-kijelző
    """
    if is_wayland_func is not None and is_wayland_func():
        return (
            "Laptop (csak)",
            "Wayland jelenleg nincs támogatva ebben a LOQ-only verzióban",
        )

    raw = x11_connected_outputs(f)
    backend = "X11"

    if f:
        log(f, f"[AUTODETECT] backend={backend}")
        log(f, f"[AUTODETECT] raw_connected={sorted(raw)}")

    has_edp = "eDP" in raw
    has_tv = "HDMI-1-0" in raw
    has_soundbar = "DP-1-0" in raw

    if has_edp and has_tv and has_soundbar:
        return (
            "Laptop + TV + Soundbar",
            f"{backend}: LOQ laptop + TV + soundbar csatlakoztatva",
        )

    if has_edp and has_soundbar:
        return (
            "Laptop + Soundbar",
            f"{backend}: LOQ laptop + soundbar csatlakoztatva",
        )

    if has_edp:
        return (
            "Laptop (csak)",
            f"{backend}: LOQ laptop kijelző érzékelve",
        )

    return (
        "Laptop (csak)",
        f"{backend}: nem egyértelmű LOQ felállás, fallback = Laptop",
    )
