#!/usr/bin/python3
# -*- coding: utf-8 -*-
#########  2026.06.19 ##########

"""
---- Végleges verzió ! ----

 Ha Waylandot is szeretnél használni, ezt javítsd!!!:

  if p.returncode == 0:
 if not is_wayland():
       ...
        p = subprocess.run(...)

"""

import sys
import os
import time
import re
import traceback

from pathlib import Path

# VS Code "Run Python File" / közvetlen app.py indítás támogatása.
# Ha az app.py önálló scriptként indul, beállítjuk a csomag-környezetet,
# hogy a relatív importok működjenek.
if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))
    __package__ = "monitor_config"


from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QDialog, QDialogButtonBox, QTextBrowser, QShortcut, QFrame
)
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt


from .version_info import APP_NAME, APP_VERSION, get_window_title
from .config import DRY_RUN, LOG_FILE_PATH
from .log_utils import log_open, log
from .command_utils import run_cmd
from .notifications import init_notifications, notify
from .setup_dialog import XrandrFirstRunDialog
from .autodetect import detect_current_kscreen_setup, detect_saved_kscreen_setup
from .profiles import (
    KSCREEN_PROFILES,
    PROFILE_ALL,
    PROFILE_LAPTOP,
    PROFILE_LAPTOP_SOUNDBAR,
)
from .kscreen_input import (
    KScreenOutput,
    clear_kscreen_input_file,
    get_saved_kscreen_state,
    has_usable_kscreen_input,
    parse_kscreen_text,
)


def _mode_resolution(token: str) -> tuple[int, int]:
    match = re.match(r"(\d+)x(\d+)@", token)
    if not match:
        return (0, 0)
    return (int(match.group(1)), int(match.group(2)))


def _max_mode_area(output: KScreenOutput) -> int:
    areas = [w * h for w, h in (_mode_resolution(mode.token) for mode in output.modes)]
    return max(areas) if areas else 0


def _pick_target_mode(output: KScreenOutput) -> tuple[str, int, int]:
    """A kimenet célmódja: a jelenleg aktív, majd a preferált mód, a felbontásával együtt."""
    wanted_token = output.active_mode or output.preferred_mode
    mode = None
    if wanted_token:
        mode = next((m for m in output.modes if m.token == wanted_token), None)
    if mode is None:
        mode = next((m for m in output.modes if m.preferred), None)
    if mode is None and output.modes:
        mode = output.modes[0]
    if mode is None:
        raise RuntimeError(f"Nincs elérhető mód ehhez: {output.name}")
    width, height = _mode_resolution(mode.token)
    return mode.mode_id, width, height


def classify_live_outputs(live_state):
    """
    A laptop/tv/soundbar szerepeket a JELENLEG ÉLŐ KScreen állapotból azonosítja,
    a kimenetek maximálisan elérhető felbontása alapján — nem a kimenet nevéből
    és nem egy korábban mentett fájlból. Így akkor is helyesen működik, ha a
    kimenetek neve/sorrendje időközben megváltozik (pl. újracsatlakoztatás után).

    A laptop mindig az egyetlen csatlakoztatott "Panel" típusú kimenet.
    A külső kimenetek közül a nagyobb elérhető felbontású a TV, a kisebb a
    Soundbar (a soundbar egy hangroutáshoz használt ál-kijelző, jellemzően
    nem nagyobb Full HD-nél).

    None-nal tér vissza, ha a laptop kijelző nem azonosítható egyértelműen
    (ekkor a hívó a mentett fájlra eshet vissza).
    """
    connected = [output for output in live_state.outputs.values() if output.connected]
    panels = [output for output in connected if output.is_panel]
    if len(panels) != 1:
        return None

    laptop = panels[0]
    external = [output for output in connected if not output.is_panel]
    ranked = sorted(external, key=_max_mode_area, reverse=True)

    tv = ranked[0] if len(ranked) >= 2 else None
    soundbar = ranked[1] if len(ranked) >= 2 else (ranked[0] if len(ranked) == 1 else None)

    return laptop, tv, soundbar, connected


def live_detection_available(logf=None) -> bool:
    """Igaz, ha a profilgombok élőben (mentett fájl nélkül) is használhatók."""
    rc, live_text, _err = run_cmd("kscreen-doctor -o", logf)
    if rc != 0:
        return False
    return classify_live_outputs(parse_kscreen_text(live_text)) is not None


def _classify_saved_outputs():
    state = get_saved_kscreen_state()
    connected = [output for output in state.outputs.values() if output.connected]
    panels = [output for output in connected if output.is_panel]
    if len(panels) != 1:
        raise RuntimeError("A mentett fájlban pontosan egy Panel típusú kijelző szükséges.")

    laptop = panels[0]
    external = [output for output in connected if not output.is_panel]
    ranked = sorted(
        external,
        key=lambda output: output.geometry_size[0] * output.geometry_size[1],
        reverse=True,
    )
    tv = ranked[0] if ranked else None
    soundbar = ranked[1] if len(ranked) > 1 else None
    return laptop, tv, soundbar, connected


def build_kscreen_command(profile_name: str, logf=None) -> str:
    if profile_name not in KSCREEN_PROFILES:
        raise RuntimeError(f"Ismeretlen profil: {profile_name}")

    rc, live_text, err = run_cmd("kscreen-doctor -o", logf)
    if rc != 0:
        raise RuntimeError(err.strip() or "A kscreen-doctor -o lekérdezés sikertelen.")

    live_state = parse_kscreen_text(live_text)

    # Elsődlegesen élőben azonosítjuk, melyik kimeneten milyen eszköz van
    # (max. felbontás alapján). A mentett kscreen-input.txt csak akkor kell,
    # ha ez az élő azonosítás nem egyértelmű (pl. a laptop-panel nem
    # ismerhető fel) — így a kézi/mentett-fájlos beállítás opcióként megmarad.
    classification = classify_live_outputs(live_state)
    if classification is not None:
        if logf:
            log(logf, "[KSCREEN-CLASSIFY] szerepek forrása: élő állapot (max. felbontás)")
        laptop, tv, soundbar, connected = classification
    else:
        if logf:
            log(logf, "[KSCREEN-CLASSIFY] élő azonosítás nem egyértelmű, mentett fájl (kscreen-input.txt) alapján")
        saved_laptop, saved_tv, saved_soundbar, _saved_connected = _classify_saved_outputs()
        laptop = live_state.outputs.get(saved_laptop.name)
        tv = live_state.outputs.get(saved_tv.name) if saved_tv else None
        soundbar = live_state.outputs.get(saved_soundbar.name) if saved_soundbar else None
        connected = [output for output in live_state.outputs.values() if output.connected]
        if laptop is None:
            raise RuntimeError(
                f"A mentett fájl szerinti laptop-kijelző ({saved_laptop.name}) jelenleg nincs csatlakoztatva."
            )

    if profile_name == PROFILE_LAPTOP:
        enabled = [laptop]
    elif profile_name == PROFILE_LAPTOP_SOUNDBAR:
        if soundbar is None:
            raise RuntimeError("Nem található külön Soundbar-kimenet.")
        enabled = [laptop, soundbar]
    else:
        if tv is None or soundbar is None:
            raise RuntimeError("Nem található külön TV- és Soundbar-kimenet.")
        enabled = [laptop, soundbar, tv]

    # A célmódokat (és azok WxH felbontását) még a pozíciószámítás előtt
    # meghatározzuk — a pozíciók a TÉNYLEGES célfelbontásból számolnak,
    # nem egy esetleg elavult/letiltott Geometry mezőből.
    target_modes = {output.name: _pick_target_mode(output) for output in enabled}

    if profile_name == PROFILE_LAPTOP:
        positions = {laptop.name: (0, 0)}
    elif profile_name == PROFILE_LAPTOP_SOUNDBAR:
        _, laptop_w, _ = target_modes[laptop.name]
        positions = {
            laptop.name: (0, 0),
            soundbar.name: (laptop_w, 0),
        }
    else:
        _, tv_w, tv_h = target_modes[tv.name]
        _, laptop_w, _ = target_modes[laptop.name]
        laptop_pos = ((tv_w - laptop_w) // 2, tv_h)
        # A soundbar (ál-kijelző, csak audio-útvonalhoz kell) a laptopra
        # pozícionálva — a pontos hely vizuálisan nem számít.
        positions = {
            tv.name: (0, 0),
            laptop.name: laptop_pos,
            soundbar.name: laptop_pos,
        }

    enabled_names = {output.name for output in enabled}
    parts = ["kscreen-doctor"]

    for output in enabled:
        mode_id, _, _ = target_modes[output.name]
        x, y = positions[output.name]
        parts.extend(
            [
                f"output.{output.output_id}.enable",
                f"output.{output.output_id}.mode.{mode_id}",
                f"output.{output.output_id}.position.{x},{y}",
                f"output.{output.output_id}.scale.1",
            ]
        )
        if output.name == laptop.name:
            parts.append(f"output.{output.output_id}.primary")

    for output in connected:
        if output.name in enabled_names:
            continue
        parts.append(f"output.{output.output_id}.disable")

    return " ".join(parts)

def wl_connected_outputs(f=None):
    """
    Wayland/KDE alatt visszaadja a csatlakoztatott kimenetek LOGIKAI neveit set-ként.
    Példa: {'eDP-1', 'HDMI-A-1', 'DP-2'}
    """
    pairs, _ = parse_outputs(f)
    connected = set()

    for oid, name in pairs:
        try:
            if output_connected(oid, f):
                connected.add(name)
        except Exception:
            pass

    return connected









# Wayland segédek
_MODE_RE = re.compile(r"(\d{3,4}x\d{3,4}@\d+(?:\.\d+)?)")




def is_wayland() -> bool:
    return False    # False = Nincs Wayland működés

def has_kscreen_doctor(f=None) -> bool:
    rc, _, _ = run_cmd("command -v kscreen-doctor", f)
    return rc == 0

def ksd(*parts: str) -> str:
    return "kscreen-doctor " + " ".join(parts)

def parse_outputs(f=None):
    """Visszaad [(id, name)] a kscreen-doctor -o kimenetből (ANSI nélkül)."""
    rc, out, err = run_cmd("kscreen-doctor -o", f)
    if rc != 0:
        raise RuntimeError(f"Nem sikerült lekérni a kimeneteket: {err.strip() or 'ismeretlen hiba'}")
    pairs = []
    for m in re.finditer(r"^\s*Output:\s+(\d+)\s+(\S+)", out, re.MULTILINE):
        pairs.append((m.group(1), m.group(2)))
    return pairs, out

def resolve_output_id(name: str, f=None) -> str:
    pairs, out = parse_outputs(f)
    for oid, n in pairs:
        if n == name:
            return oid
    lname = name.lower()
    for oid, n in pairs:
        if n.lower() == lname:
            return oid
    for oid, n in pairs:
        if lname in n.lower():
            return oid
    available = ", ".join(f"{n}(id={oid})" for oid, n in pairs) or "nincs kimenet"
    raise RuntimeError(f"Nem találom az '{name}' kimenetet. Elérhetők: {available}\n\n--RAW(clean)--\n{out}")

def output_connected(output_id: str, f=None) -> bool:
    rc, out, _ = run_cmd("kscreen-doctor -o", f)
    if rc != 0:
        return False
    block = re.search(rf"(?s)^Output:\s+{re.escape(output_id)}\s+.*?(?=^Output:|\Z)", out, re.MULTILINE)
    return bool(block and ("connected" in block.group(0)))

def detect_mode_token_by_res(output_id: str, wanted_res: str, f=None) -> str:
    """Teljes mód string (pl. '1920x1200@60') az adott Output ID-hoz. A preferred ('*!') előnyt élvez."""
    rc, out, _ = run_cmd("kscreen-doctor -o", f)
    if rc != 0:
        raise RuntimeError("Nem tudtam lekérni a módlistát (kscreen-doctor -o).")
    block = re.search(rf"(?s)^Output:\s+{re.escape(output_id)}\s+.*?(?=^Output:|\Z)", out, re.MULTILINE)
    if not block:
        raise RuntimeError(f"Nem találom az Output: {output_id} blokkot.")
    cands = []
    for line in block.group(0).splitlines():
        if wanted_res in line:
            m = _MODE_RE.search(line)
            if m:
                tok = m.group(1)
                preferred = (("preferred" in line.lower()) or ("*!" in line) or ("*" in line))
                cands.append((preferred, tok))
    if not cands:
        raise RuntimeError(f"Nincs '{wanted_res}@..' mód az Output {output_id}-on.\nBlokk:\n{block.group(0)}")
    cands.sort(key=lambda x: (not x[0], x[1]))
    return cands[0][1]

# Wayland profilok
def wl_apply_laptop_only(logf):
    log(logf, "wl_apply_laptop_only: building commands…")
    edp_id = resolve_output_id(EDP_NAME, logf)
    edp_mode = detect_mode_token_by_res(edp_id, EDP_RES, logf)
    cmds = [
        ksd(f"output.{edp_id}.enable",
            f"output.{edp_id}.mode.{edp_mode}",
            f"output.{edp_id}.position.{EDP_POS_SOLO[0]},{EDP_POS_SOLO[1]}",
            f"output.{edp_id}.scale.1",
            f"output.{edp_id}.primary"),
    ]
    for name in (HDMI_NAME, DP2_NAME):
        try:
            oid = resolve_output_id(name, logf)
            cmds.append(ksd(f"output.{oid}.disable"))
        except Exception:
            pass
    return run_sequence(cmds, logf)

def wl_apply_laptop_tv(logf):
    log(logf, "wl_apply_laptop_tv: building commands…")
    edp_id  = resolve_output_id(EDP_NAME, logf)
    hdmi_id = resolve_output_id(HDMI_NAME, logf)
    if not output_connected(hdmi_id, logf):
        return False, "A HDMI kijelző nincs csatlakoztatva."
    edp_mode  = detect_mode_token_by_res(edp_id,  EDP_RES,  logf)
    hdmi_mode = detect_mode_token_by_res(hdmi_id, HDMI_RES, logf)
    cmds = [
        ksd(f"output.{hdmi_id}.enable",
            f"output.{hdmi_id}.mode.{hdmi_mode}",
            f"output.{hdmi_id}.position.{HDMI_POS[0]},{HDMI_POS[1]}",
            f"output.{hdmi_id}.scale.1"),
        ksd(f"output.{edp_id}.enable",
            f"output.{edp_id}.mode.{edp_mode}",
            f"output.{edp_id}.position.{EDP_POS_UNDER[0]},{EDP_POS_UNDER[1]}",
            f"output.{edp_id}.scale.1",
            f"output.{edp_id}.primary"),
    ]
    try:
        dp2_id = resolve_output_id(DP2_NAME, logf)
        cmds.append(ksd(f"output.{dp2_id}.disable"))
    except Exception:
        pass
    return run_sequence(cmds, logf)

def wl_apply_laptop_soundbar(logf):
    log(logf, "wl_apply_laptop_soundbar: building commands…")
    edp_id  = resolve_output_id(EDP_NAME, logf)
    edp_mode = detect_mode_token_by_res(edp_id, EDP_RES, logf)
    dp2_id = resolve_output_id(DP2_NAME, logf)
    if not output_connected(dp2_id, logf):
        return False, "A Soundbar kijelző (DP-2) nincs csatlakoztatva."
    dp2_mode = detect_mode_token_by_res(dp2_id, "1280x800", logf)

    cmds = []
    try:
        hdmi_id = resolve_output_id(HDMI_NAME, logf)
        cmds.append(ksd(f"output.{hdmi_id}.disable"))
    except Exception:
        pass

    cmds.append(
        ksd(f"output.{edp_id}.enable",
            f"output.{edp_id}.mode.{edp_mode}",
            f"output.{edp_id}.position.0,0",
            f"output.{edp_id}.scale.1",
            f"output.{edp_id}.primary")
    )
    cmds.append(
        ksd(f"output.{dp2_id}.enable",
            f"output.{dp2_id}.mode.{dp2_mode}",
            f"output.{dp2_id}.position.0,0",
            f"output.{dp2_id}.scale.1.5")
    )
    return run_sequence(cmds, logf)

def wl_apply_all(logf):
    log(logf, "wl_apply_all: building commands…")
    edp_id  = resolve_output_id(EDP_NAME, logf)
    hdmi_id = resolve_output_id(HDMI_NAME, logf)
    if not output_connected(hdmi_id, logf):
        return False, "A HDMI kijelző nincs csatlakoztatva."
    edp_mode  = detect_mode_token_by_res(edp_id,  EDP_RES,  logf)
    hdmi_mode = detect_mode_token_by_res(hdmi_id, HDMI_RES, logf)

    cmds = [
        ksd(f"output.{hdmi_id}.enable",
            f"output.{hdmi_id}.mode.{hdmi_mode}",
            f"output.{hdmi_id}.position.{HDMI_POS[0]},{HDMI_POS[1]}",
            f"output.{hdmi_id}.scale.1"),
        ksd(f"output.{edp_id}.enable",
            f"output.{edp_id}.mode.{edp_mode}",
            f"output.{edp_id}.position.{EDP_POS_UNDER[0]},{EDP_POS_UNDER[1]}",
            f"output.{edp_id}.scale.1",
            f"output.{edp_id}.primary"),
    ]
    try:
        dp2_id = resolve_output_id(DP2_NAME, logf)
        if output_connected(dp2_id, logf):
            dp2_mode = detect_mode_token_by_res(dp2_id, "1280x800", logf)
            cmds.append(
                ksd(f"output.{dp2_id}.enable",
                    f"output.{dp2_id}.mode.{dp2_mode}",
                    f"output.{dp2_id}.position.{EDP_POS_UNDER[0]},{EDP_POS_UNDER[1]}",
                    f"output.{dp2_id}.scale.1.5")
            )
    except Exception as e:
        log(logf, "DP-2 kezelés kihagyva:", e)

    return run_sequence(cmds, logf)

# A parancssorozatok végrehajtása
def run_sequence(cmds, logf):
    # DRY mód: csak logolunk
    if DRY_RUN:
        for c in cmds:
            log(logf, "[DRY] would run:", c)
        return True, "OK (dry-run)"

    # Éles mód: első hibánál megáll
    for c in cmds:
        rc, out, err = run_cmd(c, logf)
        if rc != 0:
            try:
                _, dump, _ = run_cmd("kscreen-doctor -o", logf)
                log(logf, "--- kscreen-doctor -o dump ---\n" + dump.rstrip())
            except Exception:
                pass
            return False, (out + err).strip() or f"Hiba (rc={rc})"

    return True, "OK"


# ============================= Névjegy QDialog ================================
class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Névjegy – {APP_NAME}")
        self.setModal(True)
        self.setMinimumSize(420, 380)   # x, y

        text = f"""
<h2 style="margin-bottom:0">{APP_NAME}</h2>
<div>Verzió: <b>{APP_VERSION}</b></div>
<p><b>Lenovo-LOQ</b> laptop-hoz tartozik</p>
<hr/>
<p>Gyors kijelző-profil váltó KDE Wayland/X11 környezethez.</p>

<ul>
  <li>KDE X11/Wayland: <code>kscreen-doctor</code> (ID-alapú)</li>
  <li>Értesítés: libnotify/KNotification</li>
  <p> </p>
  <li>Autómatikus felismerés</li>
  <li>Téma</li>
  <li>Állapotsor: aktuális állapotra frissítéssel...</li>


  <li>Napló: <code>{LOG_FILE_PATH}</code></li>
</ul>
<small>&copy; 2026. április – saját használatra</small>
"""
        view = QTextBrowser(self)
        view.setOpenExternalLinks(True)
        view.setHtml(text)
        view.setFrameShape(QFrame.NoFrame)

        btns = QDialogButtonBox(QDialogButtonBox.Close, parent=self)
        btns.button(QDialogButtonBox.Close).setText("Bezárás")
        btns.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addWidget(view)
        lay.addWidget(btns)






# ================================ GUI =========================================
class MonitorSetupApp(QWidget):
    def __init__(self):
        super().__init__()
        self.log_file = log_open()
        self.display_server = (os.environ.get("XDG_SESSION_TYPE") or "x11").lower()
        log(self.log_file, f"Display Server: {self.display_server}")


        # Címsor
        self.setWindowTitle(get_window_title(DRY_RUN))

        # Fő layout (csak egyszer!)
        existing = self.layout()
        if existing is None:
            self.lay = QVBoxLayout(self)
            self.lay.setContentsMargins(12, 12, 12, 12)
            self.lay.setSpacing(8)
        else:
            self.lay = existing

        # --- FELSŐ SÁV: cím + súgó ikon ---
        top = QWidget(self)
        top_lay = QHBoxLayout(top)
        top_lay.setContentsMargins(0, 0, 0, 0)
        top_lay.setSpacing(8)

        title_lbl = QLabel("Gyors kijelző-profil váltó", top)
        title_lbl.setStyleSheet("font-weight:600;")

        help_btn = QPushButton(top)
        help_btn.setFlat(True)
        help_btn.setToolTip("Névjegy")
        ico = QIcon.fromTheme("help-about")
        if not ico.isNull():
            help_btn.setIcon(ico)
        else:
            help_btn.setText("ℹ")
        help_btn.clicked.connect(self.show_about)

        top_lay.addWidget(title_lbl, 1, alignment=Qt.AlignVCenter)
        top_lay.addWidget(help_btn, 0, alignment=Qt.AlignRight | Qt.AlignVCenter)
        self.lay.addWidget(top)



        # --- /FELSŐ SÁV ---

        # Infó címke
        self.status_label = QLabel("Válassz profilt a beállításhoz.")
        self.lay.addWidget(self.status_label)




        # --- Gombok:
        # -------------
        self.b_auto = QPushButton()
        self.b_relearn = QPushButton("🔄 Kijelzők újrafelvétele")
        self.b_relearn.setToolTip("Mentett KScreen bemenet törlése és új kijelzőfelvétel indítása.")

        self.b1 = QPushButton("💻  Laptop mód")
        self.b2 = QPushButton("💻 🔊  Laptop mód + Zene")
        self.b3 = QPushButton("💻 📺 🔊  Film / Sorozat mód")

        self.b_restart_shell = QPushButton("🔧 Asztal helyreállítása")
        self.b_restart_shell.setToolTip(
            "Csak a plasmashell újraindítása, kijelző-profilváltás nélkül — akkor "
            "hasznos, ha az asztal (háttér/ikonok) elszállt, de a panel még megy."
        )

        self._refresh_auto_button_text()

        auto_row = QHBoxLayout()
        auto_row.addWidget(self.b_auto, 0, Qt.AlignLeft)
        auto_row.addWidget(self.b_relearn, 0, Qt.AlignLeft)
        auto_row.addStretch()

        self.lay.addLayout(auto_row)

        self.lay.addSpacing(15)


        for b in (self.b1, self.b2, self.b3):
            b.setMinimumHeight(40)
            b.setFixedWidth(220)

            row = QHBoxLayout()
            row.addStretch()
            row.addWidget(b)
            row.addStretch()

            self.lay.addLayout(row)

        restart_row = QHBoxLayout()
        restart_row.addStretch()
        restart_row.addWidget(self.b_restart_shell)
        restart_row.addStretch()
        self.lay.addLayout(restart_row)



        # Signálok:

        self.b_auto.clicked.connect(self.auto_detect_and_apply)
        self.b_relearn.clicked.connect(self.relearn_displays)
        self.b1.clicked.connect(lambda: self.apply_profile(PROFILE_LAPTOP))
        self.b2.clicked.connect(lambda: self.apply_profile(PROFILE_LAPTOP_SOUNDBAR))
        self.b3.clicked.connect(lambda: self.apply_profile(PROFILE_ALL))
        self.b_restart_shell.clicked.connect(self.restart_shell)




        self._build_statusbar()
        self._init_current_status()

        # - Style:
        self.b_auto.setStyleSheet("""
            QPushButton {
                background-color: #5c92d1;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #6ea0da;
            }
            QPushButton:pressed {
                background-color: #4f84c2;
            }
        """)





        #  - Ablakméret:
        # -----------------
        self.setMinimumSize(400, 340)       # x, y
        self.setFixedSize(400, 340)

        # A profilalkalmazás minden támogatott munkamenetben KScreenen keresztül történik.
        if not has_kscreen_doctor(self.log_file):
            self.status_label.setText("HIBA: 'kscreen-doctor' nem érhető el (KDE/Plasma szükséges).")

        # F1 = Névjegy
        QShortcut(QKeySequence.HelpContents, self, activated=self.show_about)




    def _build_statusbar(self):
        self.status_wrap = QWidget(self)
        self.status_wrap.setObjectName("statusWrap")

        row = QHBoxLayout(self.status_wrap)
        row.setContentsMargins(8, 6, 8, 6)

        # BAL oldal → fő státusz
        self.sb_msg = QLabel("Aktuális: lekérdezés...")

        # JOBB oldal → rendszer infók
        self.sb_session = QLabel(f"Session: {self.display_server.upper()}")
        self.sb_mode = QLabel("DRY RUN" if DRY_RUN else "")

        row.addWidget(self.sb_msg)
        row.addStretch()
        row.addWidget(self.sb_session)
        row.addWidget(self.sb_mode)

        self.lay.addSpacing(6)
        self.lay.addWidget(self.status_wrap)



    def _init_current_status(self):
        """
        Induláskori státusz a pillanatnyi, engedélyezett KScreen-kimenetekből.

        A jelenlegi állapot mindig élőben kerül lekérdezésre — nem függ a
        mentett kscreen-input.txt fájltól (az csak a profilalkalmazásnál
        esetleges fallback, ha az élő laptop-panel azonosítás nem egyértelmű).
        """
        try:
            log(self.log_file, "[DETECT] aktuális profil forrása: élő KScreen állapot")

            rc, live_text, err = run_cmd("kscreen-doctor -o", self.log_file)
            if rc != 0:
                raise RuntimeError(err.strip() or "A kscreen-doctor -o lekérdezés sikertelen.")

            profile_name, detail = detect_current_kscreen_setup(live_text, self.log_file)
            
            display_name = {
                "Laptop (csak)": "Laptop mód",
                "Laptop + Soundbar": "Laptop mód + Zene",
                "Laptop + TV + Soundbar": "Film / sorozat mód",
            }.get(profile_name, profile_name)


            self.sb_msg.setText(f'Aktuális: "{display_name}"')
            self.status_label.setText(f"Aktuális KScreen állapot: {detail}")
            log(self.log_file, f"[STARTUP] current_profile={profile_name}")
            log(self.log_file, f"[STARTUP] current_detail={detail}")

        except Exception as e:
            log(self.log_file, f"[STARTUP] saved detect FAIL: {e}")
            self.sb_msg.setText('Aktuális: "ismeretlen"')



    def restart_shell(self):
        """
        Önálló asztal-helyreállítás: csak a plasmashell újraindítása,
        kijelző-profilváltás nélkül. Arra az esetre, ha a KDE/KScreen
        asztal-konténere magától beragad (fekete asztal, eltűnt ikonok,
        de a panel/menü még megy) — ez ismert KDE/KScreen oldali hiba,
        nem a monitor-config logikájáé.
        """
        self.status_label.setText("Asztal helyreállítása (plasmashell újraindítása)…")
        QApplication.processEvents()
        self.b_restart_shell.setEnabled(False)
        try:
            log(self.log_file, "[PLASMA] kézi asztal-helyreállítás kérve (GUI)")
            run_cmd("kquitapp5 plasmashell || kquitapp6 plasmashell", self.log_file)
            time.sleep(1)
            run_cmd("kstart5 plasmashell || kstart6 plasmashell", self.log_file)
            notify("Asztal helyreállítva", "A plasmashell újraindult.", "normal", 4000, self.log_file)
        finally:
            self.b_restart_shell.setEnabled(True)
            self.status_label.setText("Válassz profilt a beállításhoz.")

    def relearn_displays(self):
        try:
            path = clear_kscreen_input_file()
            log(self.log_file, f"[KSCREEN-INPUT] mentett KScreen bemeneti fájl előkészítve: {path}")

            self.status_label.setText("Mentett KScreen bemenet előkészítve. Másold be a kscreen-doctor -o teljes kimenetét a fájlba.")
            self._refresh_auto_button_text()

            XrandrFirstRunDialog(self).exec_()

            self._refresh_auto_button_text()

        except Exception as e:
            log(self.log_file, f"[KSCREEN-INPUT] újrafelvétel hiba: {e}")
            notify("Kijelzők újrafelvétele hiba", str(e), "critical", 6000, self.log_file)



    def auto_detect_and_apply(self):
        self._refresh_auto_button_text()

        self.status_label.setText("Kijelzők felismerése…")
        QApplication.processEvents()
        self._set_buttons_enabled(False)

        try:
            rc, live_text, err = run_cmd("kscreen-doctor -o", self.log_file)
            if rc != 0:
                raise RuntimeError(err.strip() or "A kscreen-doctor -o lekérdezés sikertelen.")

            if classify_live_outputs(parse_kscreen_text(live_text)) is not None:
                profile_name, detail = detect_current_kscreen_setup(live_text, self.log_file)
                log(self.log_file, "[AUTODETECT] forrás: élő KScreen állapot")
            elif has_usable_kscreen_input():
                profile_name, detail = detect_saved_kscreen_setup(self.log_file)
                log(self.log_file, "[AUTODETECT] forrás: mentett KScreen bemenet (élő azonosítás nem egyértelmű)")
            else:
                raise RuntimeError(
                    "A laptop-kijelző élőben nem azonosítható, és nincs használható mentett KScreen bemenet sem."
                )

            log(self.log_file, f"[AUTODETECT] selected_profile={profile_name}")
            log(self.log_file, f"[AUTODETECT] detail={detail}")

            notify("Autodetect", f"{detail}\n→ {profile_name}", "normal", 3500, self.log_file)

            # ugyanazt a meglévő logikát használjuk
            self.apply_profile(profile_name)

        except Exception as e:
            log(self.log_file, "AUTODETECT EXC:", repr(e))
            log(self.log_file, traceback.format_exc())
            notify("Autodetect hiba", str(e), "critical", 8000, self.log_file)
            self.status_label.setText("Autodetect hiba történt.")
        finally:
            self._refresh_auto_button_text()


    def _refresh_auto_button_text(self):
        try:
            has_live = live_detection_available(self.log_file)
            has_saved = has_usable_kscreen_input()
            can_apply = has_live or has_saved

            if has_live:
                self.b_auto.setText("🪄 Automatikus felismerés")
                self.b_auto.setToolTip(
                    "Profil felismerése és alkalmazása a jelenleg csatlakoztatott kijelzők "
                    "élő állapota (max. felbontás) alapján."
                )
                self.status_label.setText("Élő kijelző-felismerés elérhető. A profilgombok használhatók.")
            elif has_saved:
                self.b_auto.setText("🪄 Felismerés fájlból")
                self.b_auto.setToolTip(
                    "Élő felismerés nem egyértelmű (pl. a laptop-panel nem azonosítható). "
                    "Profil felismerése a mentett kscreen-input.txt fájlból."
                )
                self.status_label.setText("Élő felismerés nem egyértelmű — mentett fájl alapján működik.")
            else:
                self.b_auto.setText("🪄 Kijelző nem azonosítható")
                self.b_auto.setToolTip(
                    "Sem élőben, sem mentett fájlból nem azonosítható egyértelműen a laptop-kijelző. "
                    "Használd a \"Kijelzők újrafelvétele\" gombot."
                )
                self.status_label.setText("A laptop-kijelző nem azonosítható. A profilgombok inaktívak.")

            for b in (self.b_auto, self.b1, self.b2, self.b3):
                b.setEnabled(can_apply)

            # Az újrafelvétel / bemeneti fájl előkészítése mindig maradjon elérhető.
            self.b_relearn.setEnabled(True)

        except Exception as e:
            log(self.log_file, f"[KSCREEN-INPUT] button refresh FAIL: {e}")
            self.b_auto.setText("🪄 Kijelző nem azonosítható")
            for b in (self.b_auto, self.b1, self.b2, self.b3):
                b.setEnabled(False)
            self.b_relearn.setEnabled(True)



    def _set_buttons_enabled(self, enabled: bool):
        for b in (self.b_auto, self.b1, self.b2, self.b3):
            b.setEnabled(enabled)
        self.b_relearn.setEnabled(True)

    def show_about(self):
        try:
            AboutDialog(self).exec_()
            log(self.log_file, "About opened")
        except Exception as e:
            log(self.log_file, f"About FAIL: {e}")
            notify("Névjegy hiba", str(e), "critical", 6000, self.log_file)

    def apply_profile(self, name: str):
        if not live_detection_available(self.log_file) and not has_usable_kscreen_input():
            log(self.log_file, "[KSCREEN-INPUT] profil alkalmazása tiltva: sem élőben, sem mentett fájlból nem azonosítható a laptop-kijelző")
            self.status_label.setText("A laptop-kijelző nem azonosítható. Profil alkalmazása letiltva.")
            notify(
                "Kijelző nem azonosítható",
                "Sem élőben, sem a mentett kscreen-input.txt-ből nem azonosítható egyértelműen a laptop-kijelző.",
                "normal",
                4000,
                self.log_file,
            )
            self._refresh_auto_button_text()
            return

        self.status_label.setText(f"A(z) '{name}' profil alkalmazása…")
        QApplication.processEvents()
        self._set_buttons_enabled(False)
        try:
            if not has_kscreen_doctor(self.log_file):
                notify("Kijelző hiba", "A 'kscreen-doctor' nem érhető el.", "critical", 8000, self.log_file)
                return

            log(self.log_file, f"[APPLY] profile={name}, DRY_RUN={DRY_RUN}, backend=kscreen-doctor")
            command = build_kscreen_command(name, self.log_file)
            log(self.log_file, f"[APPLY] generated={command}")
            ok, msg = run_sequence([command], self.log_file)

            if ok:
                log(self.log_file, "[PLASMA] újraindítás minden profilváltás után (asztal-konténer hiba elkerülése)")
                run_cmd(
                    "kquitapp5 plasmashell || kquitapp6 plasmashell",
                    self.log_file,
                )
                time.sleep(1)
                run_cmd(
                    "kstart5 plasmashell || kstart6 plasmashell",
                    self.log_file,
                )

                display_name = {
                    "Laptop (csak)": "Laptop mód",
                    "Laptop + Soundbar": "Laptop mód + Zene",
                    "Laptop + TV + Soundbar": "Film / sorozat mód",
                }.get(name, name)


                self.sb_msg.setText(f'Aktuális: "{display_name}"')
                self.status_label.setText(f"A(z) '{display_name}' profil alkalmazva.")
                notify("Kijelző beállítva", "Profil alkalmazva (KScreen).", "normal", 4000, self.log_file)
            else:
                notify("Kijelző hiba", msg if isinstance(msg, str) else str(msg), "critical", 8000, self.log_file)

        except Exception as e:
            log(self.log_file, "EXC:", repr(e))
            log(self.log_file, traceback.format_exc())
            notify("Kijelző kivétel", str(e), "critical", 8000, self.log_file)
        finally:
            self._refresh_auto_button_text()

    def closeEvent(self, ev):
        try:
            self.log_file.close()
        except Exception:
            pass
        super().closeEvent(ev)


        
# ================================= main =======================================
def main():
    app = QApplication(sys.argv)

    init_notifications()

    w = MonitorSetupApp()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
