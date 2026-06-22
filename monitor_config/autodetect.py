"""
Automatikus kijelzőprofil-felismerési segédek.

Ez a modul egyelőre csak a tiszta döntési logikát tartalmazza:
- kimenetnevek normalizálása
- profil kiválasztása a csatlakoztatott kijelzők alapján

A tényleges X11 / Wayland lekérdezés még az app.py-ban marad.
"""


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
        if low in {"hdmi-a-0", "hdmi-a-1", "hdmi-0", "hdmi-1", "hdmi"} or low.startswith("hdmi"):
            norm.add("HDMI")
            continue

        # DP / soundbar
        if low in {"dp-2", "displayport-2", "displayport-1", "dp2", "dp1"} or "displayport" in low or low.startswith("dp-"):
            norm.add("DP")
            continue

    return norm


def select_profile_from_outputs(raw_names: set[str], backend: str) -> tuple[str, str, set[str]]:
    """
    A csatlakoztatott kijelzők alapján kiválasztja a legbiztonságosabb profilt.

    Visszatérés:
        profilnév, részletes magyarázat, normalizált kimenetnevek
    """

    norm = normalize_connected_outputs(raw_names)

    has_laptop = "eDP" in norm
    has_tv = "HDMI" in norm
    has_soundbar = "DP" in norm

    if not has_laptop:
        return (
            "Laptop (csak)",
            f"{backend}: laptop kijelző nem egyértelmű, biztonságos fallback = Laptop",
            norm,
        )

    if has_tv and has_soundbar:
        return (
            "Laptop + TV + Soundbar",
            f"{backend}: laptop + TV + soundbar érzékelve",
            norm,
        )

    if has_soundbar:
        return (
            "Laptop + Soundbar",
            f"{backend}: laptop + soundbar érzékelve",
            norm,
        )

    if has_tv:
        return (
            "Laptop (csak)",
            f"{backend}: TV érzékelve, de soundbar nélkül nincs külön TV profil, fallback = Laptop",
            norm,
        )

    return (
        "Laptop (csak)",
        f"{backend}: csak laptop kijelző érzékelve",
        norm,
    )