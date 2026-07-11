# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QVBoxLayout,
    QTextBrowser,
)

from .kscreen_input import KSCREEN_INPUT_PATH


class KScreenFirstRunDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Első kijelzőfelvétel")
        self.setModal(True)
        self.setMinimumSize(520, 420)

        text = f"""
<h2>Első kijelzőfelvétel</h2>

<p>A program még nem talál használható <code>kscreen-doctor</code> kimenetet.</p>

<p>Az automatikus profilválasztáshoz először mentsd el a kijelzők aktuális állapotát.</p>

<ol>
  <li>Nyiss egy Terminált.</li>
  <li>Írd be ezt a parancsot:</li>
</ol>

<pre>kscreen-doctor -o</pre>

<ol start="3">
  <li>A teljes kimenetet másold be ebbe a fájlba:</li>
</ol>

<pre>{KSCREEN_INPUT_PATH}</pre>

<p>Ezután nyomd meg újra a <b>Profil felismerése</b> gombot.</p>

<hr/>

<p><b>Tipp:</b> ha később megváltozik a TV, soundbar, kábel vagy driver állapota,
egyszerűen frissítsd újra ezt a fájlt az aktuális
<code>kscreen-doctor -o</code> kimenettel.</p>
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


# Átmeneti kompatibilitás a még régi osztálynevet importáló app.py verziókhoz.
XrandrFirstRunDialog = KScreenFirstRunDialog
