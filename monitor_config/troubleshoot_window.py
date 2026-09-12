# -*- coding: utf-8 -*-
"""
Hibaelhárítás ablak — külön, a főablak "Hibaelhárítás" gombjával nyitható.

Felül egy sor diagnosztikai/javító gomb, alatta egy nagy, beágyazott
log/CLI-kimenet terület — a gombokra kattintva a parancsok kimenete
ide íródik ki, nem egy külön Konsole ablakba.
"""

from __future__ import annotations

import time

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .command_utils import run_cmd
from .log_utils import log


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


class TroubleshootWindow(QWidget):
    def __init__(self, log_file, parent=None):
        super().__init__(parent)
        self.log_file = log_file

        self.setWindowTitle("Hibaelhárítás")
        self.setMinimumSize(680, 460)
        # Önálló ablakként nyíljon meg, ne a főablakba ágyazva.
        self.setWindowFlag(Qt.WindowType.Window, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(12)

        # -- Akció gombok sora --------------------------------------------- #
        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)

        self.b_diagnostics = QPushButton("Diagnosztika")
        self.b_diagnostics.setObjectName("secondaryButton")
        self.b_diagnostics.clicked.connect(self.run_diagnostics)

        self.b_autofix = QPushButton("Automatikus javítás")
        self.b_autofix.setObjectName("secondaryButton")
        self.b_autofix.setToolTip(
            "PipeWire/WirePlumber újraindítása és az audio-profil ellenőrzése."
        )
        self.b_autofix.clicked.connect(self.run_autofix)

        self.b_clear = QPushButton("Kimenet törlése")
        self.b_clear.setObjectName("tertiaryButton")
        self.b_clear.clicked.connect(lambda: self.output.clear())

        actions_row.addWidget(self.b_diagnostics)
        actions_row.addWidget(self.b_autofix)
        actions_row.addStretch(1)
        actions_row.addWidget(self.b_clear)
        root.addLayout(actions_row)

        # -- Beágyazott kimeneti terület ------------------------------------ #
        self.output = QTextEdit()
        self.output.setObjectName("logOutput")
        self.output.setReadOnly(True)
        mono = QFont("Monospace")
        mono.setStyleHint(QFont.StyleHint.TypeWriter)
        mono.setPointSize(10)
        self.output.setFont(mono)
        self.output.setPlaceholderText(
            "A diagnosztikai parancsok kimenete itt jelenik meg…"
        )
        root.addWidget(self.output, 1)

        self.setStyleSheet(QSS)

    # ----------------------------------------------------------------- #
    # Segédek
    # ----------------------------------------------------------------- #

    def _append_html(self, html: str):
        self.output.append(html)
        scrollbar = self.output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _append(self, text: str):
        """Sima, nem kiemelt szöveg (pl. szakasz-fejlécek) hozzáfűzése."""
        self._append_html(_escape_html(text).replace("\n", "<br>"))

    def _run_and_show(self, label: str, cmd: str):
        # A parancssor félkövéren, kék akcent-színnel — jól elkülönül a
        # felette/alatta lévő parancsok kimenetétől.
        self._append_html(
            f'<div style="margin-top:6px;">'
            f'<span style="color:#2563eb; font-weight:600;">$ {_escape_html(cmd)}</span>'
            f'</div>'
        )
        log(self.log_file, f"[TROUBLESHOOT] {label}: $ {cmd}")
        rc, out, err = run_cmd(cmd, self.log_file)
        if out.strip():
            self._append_html(
                f'<pre style="margin:2px 0; white-space:pre-wrap;">{_escape_html(out.rstrip())}</pre>'
            )
        if err.strip():
            self._append_html(
                f'<pre style="margin:2px 0; white-space:pre-wrap; color:#c0392b;">{_escape_html(err.rstrip())}</pre>'
            )
        exit_color = "#1f9d55" if rc == 0 else "#c0392b"
        self._append_html(
            f'<span style="color:{exit_color};">(kilépőkód: {rc})</span>'
        )
        return rc, out, err

    # ----------------------------------------------------------------- #
    # Akciók
    # ----------------------------------------------------------------- #

    def _append_section(self, text: str):
        self._append_html(
            f'<div style="margin-top:10px; color:#6b7280; font-weight:600;">{_escape_html(text)}</div>'
        )

    def run_diagnostics(self):
        self._set_buttons_enabled(False)
        try:
            self._append_section("=== Diagnosztika indítva ===")
            self._run_and_show("kscreen", "kscreen-doctor -o")
            self._run_and_show("wpctl", "wpctl status")
            self._run_and_show("pactl-sinks", "pactl list short sinks")
            self._append_section("=== Diagnosztika kész ===")
        finally:
            self._set_buttons_enabled(True)

    def run_autofix(self):
        self._set_buttons_enabled(False)
        try:
            self._append_section("=== Automatikus javítás indítva ===")
            self._run_and_show("wireplumber-restart", "systemctl --user restart wireplumber")
            time.sleep(1)
            self._run_and_show("pipewire-restart", "systemctl --user restart pipewire pipewire-pulse")
            time.sleep(1)
            self._run_and_show("wpctl-status", "wpctl status")
            self._append_section("=== Automatikus javítás kész ===")
        finally:
            self._set_buttons_enabled(True)

    def _set_buttons_enabled(self, enabled: bool):
        self.b_diagnostics.setEnabled(enabled)
        self.b_autofix.setEnabled(enabled)


QSS = """
QWidget            { background: #eef0f2; color: #1b1e24;
                     font-family: "Noto Sans"; font-size: 12.5px; }

QPushButton#secondaryButton {
    background: #ffffff; border: 1px solid #d7dbe0; border-radius: 8px;
    padding: 9px 12px;
}
QPushButton#secondaryButton:hover  { background: #f5f8fc; border-color: #b9c4d4; }
QPushButton#secondaryButton:pressed { background: #e8ecf0; }

QPushButton#tertiaryButton {
    background: transparent; border: 1px solid #d7dbe0; border-radius: 8px;
    padding: 9px 12px; color: #6b7280;
}
QPushButton#tertiaryButton:hover { background: #e4e7eb; color: #1b1e24; }

QTextEdit#logOutput {
    background: #ffffff; border: 1px solid #d7dbe0; border-radius: 8px;
    padding: 8px;
}
"""
