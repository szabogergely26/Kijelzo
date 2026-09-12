# -*- coding: utf-8 -*-
"""
A plasmashell biztonságos (race-condition-mentes) újraindítása.

Ezt eredetileg a cli.py tartalmazta privát segédfüggvényként; mivel a GUI
(main_window.py) és a headless CLI (cli.py) is ugyanazt a robusztus
mechanizmust igényli a plasmashell-újraindításhoz (nem csak egy egyszerű
kquitapp+kstart-ot), ide lett kiemelve, hogy egyetlen forrásból éljen.
"""

import shlex
import shutil
import subprocess

from .config import LOG_FILE_PATH
from .log_utils import log


def restart_plasmashell_detached(logf) -> None:
    """
    A plasmashell újraindítása egy, a jelenlegi folyamattól teljesen
    független háttérfolyamatból.

    Ha ezt a widgetből hívjuk, ez a python szkript maga is a plasmashell
    egyik (a "executable" Plasma5Support DataSource által indított)
    gyermekfolyamata. Ha közvetlenül ez a szkript futtatná a
    "kquitapp plasmashell" parancsot, a plasmashell a saját kilépésekor
    megölné a benne még futó gyermek-QProcess-t (ezt a szkriptet) is,
    mielőtt az elérne a "kstart"-ig — így az új plasmashell soha nem
    indulna el.

    Ez a self-kill probléma csak a fél igazság: a start_new_session=True
    (setsid) önmagában NEM elég. A setsid csak a job-control alapú
    (SIGHUP, terminál-leválás) kilövés ellen véd — nem menti ki a
    folyamatot abból a cgroup-ból, amiben elindult. Plasma 6 alatt a
    plasmashell jellemzően egy systemd user unit/scope cgroup-jában fut,
    és ha annak KillMode=control-group (gyakori alapbeállítás), akkor
    amikor a plasmashell a "kquitapp"-tól kilép, a systemd az egész
    cgroup-ot letakarítja — beleértve egy pusztán setsid-elt, de ugyanabban
    a cgroup-ban maradt háttér-scriptet is, MÉG MIELŐTT az elérne a
    "kstart"-ig. Ez okozta az időszakos ("hol jó, hol nem") hibát: a
    plasmashell kilépett, de az új példányt indító script vele együtt
    kimúlt, mielőtt a "kstart"-ot kiadhatta volna, és az asztal üresen
    maradt (csak a már megnyitott ablakok, panel/kompozitor nélkül).

    Ezért, ha elérhető, a "systemd-run --user --scope --collect"-tel egy
    vadonatúj, plasmashell-től teljesen független scope-ba/cgroup-ba
    tesszük a háttér-scriptet — ez már túléli a plasmashell cgroup-jának
    megszűnését is, nem csak a szülő python-folyamat esetleges halálát.
    Ha a "systemd-run" valamiért nem elérhető (pl. nem systemd-es
    rendszer), visszaesünk a korábbi, pusztán setsid-elt megoldásra —
    ez a self-kill esetet még mindig kezeli, csak a cgroup-osat nem.

    Hidegindítású HDMI/TV-profilváltásnál (kikapcsolt -> bekapcsolt) a
    TV-nek időbe telik, amíg a HDMI-jel stabilizálódik (EDID-olvasás,
    módváltás) — ha a plasmashell ez előtt indul újra, a kompozitor egy
    még átmeneti kijelző-konfigurációra csatlakozik rá, ami fekete
    képet ad kurzorral. Ezért előbb egy poll-loop várja meg, amíg a
    "kscreen-doctor -o" kimenete néhány egymást követő olvasás alatt
    nem változik (stabil), timeout-tal biztosítva, hogy sose akadjon be
    örökre, ha a kimenet valamiért sosem állna meg.

    Megjegyzés: a "sleep N,N" (tizedesvessző) alak csak hu_HU locale
    alatt érvényes sleep-parancs — más (pl. C) locale-ban futtatva a
    "sleep" azonnal hibával kilép, és a script érdemi várakozás nélkül
    fut tovább. Mivel ezt a scriptet a plasmashell egy gyermekfolyamata
    (más locale-lal futhat) indítja, itt explicit LC_ALL=C-t állítunk,
    hogy a viselkedés a hívó környezetétől függetlenül kiszámítható
    legyen.
    """
    log_path = shlex.quote(LOG_FILE_PATH)
    script = (
        "export LC_ALL=C; "
        f"bglog() {{ printf '[%s] [PLASMA-BG] %s\\n' \"$(date '+%Y-%m-%d %H:%M:%S')\" \"$1\" >> {log_path}; }}; "
        "bglog 'HDMI stabilizacio varasa inditva'; "
        "prev=''; stable=0; "
        "for i in $(seq 1 20); do "
        "cur=\"$(kscreen-doctor -o 2>/dev/null)\"; "
        "if [ -n \"$cur\" ] && [ \"$cur\" = \"$prev\" ]; then stable=$((stable + 1)); else stable=0; fi; "
        "prev=\"$cur\"; "
        "if [ \"$stable\" -ge 3 ]; then break; fi; "
        "sleep 0.5; "
        "done; "
        "bglog \"HDMI allapot stabil vagy timeout (stable=$stable, i=$i)\"; "
        "sleep 1; "
        "kquitapp5 plasmashell || kquitapp6 plasmashell; "
        "sleep 2; "
        "LC_ALL= LANG=hu_HU.UTF-8 kstart5 plasmashell || LC_ALL= LANG=hu_HU.UTF-8 kstart6 plasmashell; "
        "bglog 'plasmashell ujrainditasa kiadva'"
    )
    systemd_run = shutil.which("systemd-run")
    if systemd_run:
        log(logf, "[PLASMA] leválasztott újraindító háttérfolyamat indítása (systemd-run --scope, cgroup-független)")
        cmd = [
            systemd_run,
            "--user",
            "--scope",
            "--collect",
            "--quiet",
            "--",
            "bash",
            "-c",
            script,
        ]
    else:
        log(logf, "[PLASMA] leválasztott újraindító háttérfolyamat indítása (setsid fallback, systemd-run nem elérhető)")
        cmd = ["bash", "-c", script]

    subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
