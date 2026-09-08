#!/bin/bash
# Kijelzo (monitor-config) — csak a Python venv + PyQt5 rész.
#
# .desktop fájlból is indítható (dupla kattintás).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "== Python venv + PyQt5 =="
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install PyQt5 -q

echo
echo "Kész."
read -n 1 -s -r -p "Nyomj meg egy billentyűt a bezáráshoz..."
echo
