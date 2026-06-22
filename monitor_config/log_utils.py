# -*- coding: utf-8 -*-


import os
import time

from .config import DRY_RUN

# ============================== Log beállítások ===============================
LOG_FILE_PATH = "/tmp/monitor_config.log"

# (opcionális) log-rotáció ~2MB felett
def _rotate_log_if_big(path: str, max_bytes: int = 2_000_000):
    try:
        if os.path.exists(path) and os.path.getsize(path) > max_bytes:
            ts = time.strftime("%Y%m%d-%H%M%S")
            os.rename(path, f"{path}.{ts}.1")
    except Exception:
        pass

def _ts():
    return time.strftime("%Y-%m-%d %H:%M:%S")

# Naplózás:
def log_open():
    _rotate_log_if_big(LOG_FILE_PATH)
    f = open(LOG_FILE_PATH, "a", buffering=1, encoding="utf-8", errors="replace")

    header_1 = f"\n--- Session {_ts()} ---"     # Session+Date
    header_2 = f"USER={os.environ.get('USER')}  DISPLAY_SERVER={os.environ.get('XDG_SESSION_TYPE')}  DRY_RUN={DRY_RUN}" # User, Display, DRY_RUN

    # fájl-ba írunk:
    f.write(header_1 + "\n")
    f.write(header_2 + "\n")

    # konsole-ra írunk:
    print(header_1, flush=True)
    print(header_2, flush=True)

    return f


def log(f, *args):
    try:
        line = " ".join(str(a) for a in args)
        formatted_line = f"[{_ts()}] {line}"

        f.write(formatted_line + "\n")  # fájlba ír
        print(formatted_line, flush=True) # konsole-ra ír

    except Exception:
        pass
