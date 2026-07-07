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
from .profiles import (
    DP2_NAME,
    EDP_NAME,
    EDP_POS_SOLO,
    EDP_POS_UNDER_TV,
    EDP_RES,
    HDMI_NAME,
    HDMI_POS,
    HDMI_RES,
    SOUNDBAR_NAME,
    X11_PROFILES,
)





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





# ============================== Autodetect ====================================

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

    if {"eDP", "HDMI", "DP"}.issubset(norm):
        return "Laptop + TV + Soundbar"

    if {"eDP", "HDMI"}.issubset(norm):
        return "Laptop + TV + Soundbar"

    return "ismeretlen"















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


def detect_current_setup(f=None):
    """
    Visszaad:
      (profil_név, részletes_szöveg)

    Lenovo LOQ-only fix verzió:
      eDP      = laptop kijelző
      HDMI-1-0 = LG TV
      DP-1-0   = Citation / Soundbar HDMI audio-kijelző
    """
    if is_wayland():
        return (
            "Laptop (csak)",
            "Wayland jelenleg nincs támogatva ebben a LOQ-only verzióban"
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
            f"{backend}: LOQ laptop + TV + soundbar csatlakoztatva"
        )

    if has_edp and has_soundbar:
        return (
            "Laptop + Soundbar",
            f"{backend}: LOQ laptop + soundbar csatlakoztatva"
        )

    if has_edp:
        return (
            "Laptop (csak)",
            f"{backend}: LOQ laptop kijelző érzékelve"
        )

    return (
        "Laptop (csak)",
        f"{backend}: nem egyértelmű LOQ felállás, fallback = Laptop"
    )



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

    run_cmd("kquitapp5 plasmashell || kquitapp6 plasmashell", logf)
    time.sleep(1)
    run_cmd("kstart5 plasmashell || kstart6 plasmashell", logf)

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
<hr/>
<p>Gyors kijelző-profil váltó KDE Wayland/X11 környezethez.</p>
<ul>
  <li>Waylanden: <code>kscreen-doctor</code> (ID-alapú)</li>
  <li>X11-en: <code>xrandr</code></li>
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
        self.b_auto = QPushButton("🪄 Automatikus felismerés")

        self.b1 = QPushButton("💻  Laptop (csak)")
        self.b2 = QPushButton("💻 🔊  Laptop + Soundbar")
        self.b3 = QPushButton("💻 📺 🔊  Laptop + TV + Soundbar")

        auto_row = QHBoxLayout()
        auto_row.addWidget(self.b_auto, 0, Qt.AlignLeft)
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




        self.b_auto.clicked.connect(self.auto_detect_and_apply)
        self.b1.clicked.connect(lambda: self.apply_profile("Laptop (csak)"))
        self.b2.clicked.connect(lambda: self.apply_profile("Laptop + Soundbar"))
        self.b3.clicked.connect(lambda: self.apply_profile("Laptop + TV + Soundbar"))




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
        self.setMinimumSize(400, 300)       # x, y
        self.setFixedSize(400,300)

        # Figyelmeztetés, ha Waylanden nincs kscreen-doctor
        if is_wayland() and not has_kscreen_doctor(self.log_file):
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
        try:
            profile_name = detect_current_active_setup(self.log_file)
            self.sb_msg.setText(f'Aktuális: "{profile_name}"')
            log(self.log_file, f"[STARTUP] current_profile={profile_name}")
        except Exception as e:
            log(self.log_file, f"[STARTUP] detect FAIL: {e}")
            self.sb_msg.setText('Aktuális: "ismeretlen"')




    def auto_detect_and_apply(self):
        self.status_label.setText("Kijelzők automatikus felismerése…")
        QApplication.processEvents()
        self._set_buttons_enabled(False)

        try:
            profile_name, detail = detect_current_setup(self.log_file)
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
            self._set_buttons_enabled(True)

    def _set_buttons_enabled(self, enabled: bool):
        for b in (self.b_auto, self.b1, self.b2, self.b3):
            b.setEnabled(enabled)

    def show_about(self):
        try:
            AboutDialog(self).exec_()
            log(self.log_file, "About opened")
        except Exception as e:
            log(self.log_file, f"About FAIL: {e}")
            notify("Névjegy hiba", str(e), "critical", 6000, self.log_file)

    def apply_profile(self, name: str):
        self.status_label.setText(f"A(z) '{name}' profil alkalmazása…")
        QApplication.processEvents()
        self._set_buttons_enabled(False)
        try:
            # ------------------ X11 ág ------------------
            if not is_wayland():
                profile = X11_PROFILES.get(name)
                if not profile:
                    notify("Infó", "Ehhez az X11 profilhoz nincs parancs definiálva.", "normal", 4000, self.log_file)
                    return

                commands = profile.get("commands")

                if not commands:
                    notify("Kijelző hiba", "Ehhez az X11 profilhoz nincs commands lista.", "critical", 8000, self.log_file)
                    return

                ok, msg = run_x11_commands(commands, self.log_file)

                if not ok:
                    notify("Kijelző hiba", msg or "Ismeretlen hiba", "critical", 8000, self.log_file)
                    return

                self.sb_msg.setText(f'Aktuális: "{name}"')
                time.sleep(1)

                rc2, out2, err2 = run_cmd("xrandr --query", self.log_file)
                if rc2 == 0:
                    log(self.log_file, "X11 POSTCHECK OK")
                else:
                    log(self.log_file, "X11 POSTCHECK FAIL:", err2)

                # Plasma helyrerúgás, ha kell
                run_cmd("kquitapp5 plasmashell || kquitapp6 plasmashell || true", self.log_file)
                time.sleep(1)
                run_cmd("kstart5 plasmashell || kstart6 plasmashell || plasmashell &", self.log_file)

                notify("Kijelző beállítva", "Profil alkalmazva (X11).", "normal", 4000, self.log_file)
                return








            # ---------------- Wayland ág ----------------
            if not has_kscreen_doctor(self.log_file):
                notify("Kijelző hiba", "A 'kscreen-doctor' nem érhető el.", "critical", 8000, self.log_file)
                return

            log(self.log_file, f"apply_profile: name={name}, DRY_RUN={DRY_RUN}, wayland=True")

            if name == "Laptop (csak)":
                ok, msg = wl_apply_laptop_only(self.log_file)
            elif name == "Laptop + Soundbar":
                ok, msg = wl_apply_laptop_soundbar(self.log_file)
            elif name == "Laptop + TV + Soundbar":
                ok, msg = wl_apply_all(self.log_file)
            else:
                notify("Kijelző hiba", f"Nincs profil ehhez: {name}", "critical", 8000, self.log_file)
                return

            if ok:
                notify("Kijelző beállítva", "Profil alkalmazva (Wayland).", "normal", 4000, self.log_file)
            else:
                notify("Kijelző hiba", msg if isinstance(msg, str) else str(msg), "critical", 8000, self.log_file)

        except Exception as e:
            log(self.log_file, "EXC:", repr(e))
            log(self.log_file, traceback.format_exc())
            notify("Kijelző kivétel", str(e), "critical", 8000, self.log_file)
        finally:
            self._set_buttons_enabled(True)
            self.status_label.setText("Válassz profilt a beállításhoz.")

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
