#!/bin/bash
# Kijelzo (monitor-config) teljes beállítása egy friss/újratelepített
# rendszeren, amíg nincs .deb csomag.
#
# Feltétel: ez a repó már a helyén van (pl. ~/Kijelzo), ebből a mappából
# futtasd: ./install.sh
#
# Sudo-t igényel (rendszercsomagok + /usr alá másolás), ezért valódi
# terminálban futtasd, ne egy automatizált/jelszó nélküli környezetből.
#
# Újrafuttatható (idempotens) — reinstall után is elég csak ezt lefuttatni.
# Ha majd elkészül a .deb csomag, ez a script feleslegessé válik.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "== 1/5: rendszercsomagok =="
sudo apt install -y python3-venv libkscreen-bin libnotify-bin

echo "== 2/5: Python venv + PyQt5 =="
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install PyQt5 -q

echo "== 3/5: plasmoid telepítése (rendszer-szinten, minden felhasználónak) =="
# Ha korábban dev-teszthez kpackagetool6-tal user-szintre lett telepítve,
# azt eltávolítjuk — különben az árnyékolná a most telepített rendszer-szintűt.
rm -rf "$HOME/.local/share/plasma/plasmoids/org.szaboger.kijelzovalto"
sudo mkdir -p /usr/share/plasma/plasmoids
sudo rm -rf /usr/share/plasma/plasmoids/org.szaboger.kijelzovalto
sudo cp -r packaging/deb/root/usr/share/plasma/plasmoids/org.szaboger.kijelzovalto /usr/share/plasma/plasmoids/

echo "== 4/5: edp-blank (automatikus panel-elsötétítés) telepítése =="
# A dev-teszthez ~/.config/systemd/user/-ba tett ideiglenes unitot is eltávolítjuk,
# nehogy az fusson a most telepített rendszer-szintű helyett.
if systemctl --user is-active --quiet edp-blank.service 2>/dev/null; then
    systemctl --user stop edp-blank.service
fi
rm -f "$HOME/.config/systemd/user/edp-blank.service"

sudo mkdir -p /usr/lib/monitor-config
sudo cp packaging/deb/root/usr/lib/monitor-config/edp-blank.sh /usr/lib/monitor-config/edp-blank.sh
sudo chmod +x /usr/lib/monitor-config/edp-blank.sh
sudo mkdir -p /usr/lib/systemd/user
sudo cp packaging/deb/root/usr/lib/systemd/user/edp-blank.service /usr/lib/systemd/user/edp-blank.service

echo "== 5/5: KDE plugin-cache és systemd --user újraolvasása =="
if command -v kbuildsycoca6 >/dev/null 2>&1; then
    kbuildsycoca6 --noincremental
elif command -v kbuildsycoca5 >/dev/null 2>&1; then
    kbuildsycoca5 --noincremental
fi
systemctl --user daemon-reload

echo
echo "Kész."
echo "- Widget hozzáadása: jobbklikk a panelre/asztalra -> Widgetek hozzáadása -> \"Kijelző váltó\"."
echo "  (ha nem jelenne meg azonnal, indítsd újra a plasmashell-t: kquitapp6 plasmashell; kstart6 plasmashell)"
echo "- Az automatikus elsötétítés idle-küszöbét itt állíthatod:"
echo "  ~/.config/monitor-config/edp-blank.conf  (IDLE_THRESHOLD=<mp>, alapérték 300 = 5 perc)"
