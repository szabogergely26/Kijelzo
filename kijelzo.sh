#!/bin/bash

exec >> /tmp/monitor-config-shortcut.log 2>&1
echo "---- $(date) ----"

export DISPLAY=:0
export XAUTHORITY=/home/szaboger/.Xauthority
export XDG_RUNTIME_DIR=/run/user/$(id -u)

cd /home/szaboger/Kijelzo || exit 1
exec /home/szaboger/Kijelzo/.venv/bin/python /home/szaboger/Kijelzo/monitor_config.py
