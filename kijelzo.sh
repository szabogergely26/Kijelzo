#!/bin/bash

exec >> /tmp/monitor-config-shortcut.log 2>&1
echo "---- $(date) ----"

export DISPLAY=:0
export XAUTHORITY="$HOME/.Xauthority"
export XDG_RUNTIME_DIR=/run/user/$(id -u)

cd "$HOME/Kijelzo" || exit 1
"$HOME/Kijelzo/.venv/bin/python" "$HOME/Kijelzo/main.py"
