"""
Fejnélküli (headless) profilváltás parancssorból.

Ugyanazt a logikát futtatja, mint a GUI "apply_profile" gombjai
(build_kscreen_command + run_sequence, KScreen/kscreen-doctor alapon),
csak QWidget/QApplication nélkül — így külső eszközök (pl. a Kijelző-váltó
plasmoid) is meg tudják hívni ablak megnyitása nélkül.
"""

import subprocess
import sys

from .app import build_kscreen_command, has_kscreen_doctor, run_sequence
from .autodetect import detect_current_kscreen_setup
from .command_utils import run_cmd
from .log_utils import log, log_open
from .notifications import init_notifications, notify
from .profiles import KSCREEN_PROFILES

# Ugyanaz a megjelenítendő névtérkép, mint a GUI állapotsorában (app.py).
DISPLAY_NAMES = {
    "Laptop (csak)": "Laptop mód",
    "Laptop + Soundbar": "Laptop mód + Zene",
    "Laptop + TV + Soundbar": "Film / sorozat mód",
}


def print_current_status() -> int:
    """A jelenleg élő KScreen állapotból megállapított profil nevét írja ki stdout-ra."""
    rc, live_text, err = run_cmd("kscreen-doctor -o")

    if rc != 0:
        print("ismeretlen")
        return 1

    profile_name, _detail = detect_current_kscreen_setup(live_text)
    print(DISPLAY_NAMES.get(profile_name, profile_name))
    return 0


def _restart_plasmashell_detached(logf) -> None:
    """
    A plasmashell újraindítása egy, a jelenlegi folyamattól teljesen
    független (setsid-elt) háttérfolyamatból.

    Ha ezt a widgetből hívjuk, ez a python szkript maga is a plasmashell
    egyik (a "executable" Plasma5Support DataSource által indított)
    gyermekfolyamata. Ha közvetlenül ez a szkript futtatná a
    "kquitapp plasmashell" parancsot, a plasmashell a saját kilépésekor
    megölné a benne még futó gyermek-QProcess-t (ezt a szkriptet) is,
    mielőtt az elérne a "kstart"-ig — így az új plasmashell soha nem
    indulna el. A start_new_session=True miatt ez a háttér-shell
    túléli, még ha ezt a folyamatot időközben megölik is.
    """
    script = (
        "sleep 2; "
        "kquitapp5 plasmashell || kquitapp6 plasmashell; "
        "sleep 2,5; "
        "kstart5 plasmashell || kstart6 plasmashell"
    )
    log(logf, "[PLASMA] leválasztott újraindító háttérfolyamat indítása")
    subprocess.Popen(
        ["bash", "-c", script],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def restart_shell_headless() -> int:
    """
    Önálló asztal-helyreállítás: csak a plasmashell újraindítása, profilváltás
    nélkül. Arra az esetre, ha az asztal-konténer valamiért (KDE/KScreen
    oldali, nem a monitor-config hibája) beragad — fekete asztal, eltűnt
    ikonok, de a panel/menü még működik.
    """
    logf = log_open()
    try:
        log(logf, "[PLASMA] kézi asztal-helyreállítás kérve")
        _restart_plasmashell_detached(logf)
        print("OK")
        return 0
    finally:
        log(logf, "[CLI] restart_shell_headless done")
        logf.close()


def apply_profile_headless(name: str) -> int:
    init_notifications()
    logf = log_open()

    try:
        if name not in KSCREEN_PROFILES:
            available = ", ".join(KSCREEN_PROFILES)
            print(f"Ismeretlen profil: {name!r}. Elérhetők: {available}", file=sys.stderr)
            return 1

        if not has_kscreen_doctor(logf):
            notify("Kijelző hiba", "A 'kscreen-doctor' nem érhető el.", "critical", 8000, logf)
            print("A 'kscreen-doctor' nem érhető el.", file=sys.stderr)
            return 1

        try:
            command = build_kscreen_command(name, logf)
        except Exception as e:
            log(logf, "[CLI] build_kscreen_command EXC:", repr(e))
            notify("Kijelző hiba", str(e), "critical", 8000, logf)
            print(str(e), file=sys.stderr)
            return 1

        log(logf, f"[CLI] generated={command}")

        ok, msg = run_sequence([command], logf)

        if not ok:
            notify("Kijelző hiba", msg or "Ismeretlen hiba", "critical", 8000, logf)
            print(msg, file=sys.stderr)
            return 1

        log(logf, "[PLASMA] újraindítás minden profilváltás után (asztal-konténer hiba elkerülése)")
        _restart_plasmashell_detached(logf)

        notify("Kijelző beállítva", "Profil alkalmazva (KScreen).", "normal", 4000, logf)
        print("OK")
        return 0
    finally:
        log(logf, "[CLI] apply_profile_headless done")
        logf.close()
