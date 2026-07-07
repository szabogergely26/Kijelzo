# -*- coding: utf-8 -*-

import os
import time

from .config import DRY_RUN, LOG_FILE_PATH


def _rotate_log_if_big(path: str, max_bytes: int = 2_000_000):
    try:
        if os.path.exists(path) and os.path.getsize(path) > max_bytes:
            ts = time.strftime("%Y%m%d-%H%M%S")
            os.rename(path, f"{path}.{ts}.1")
    except Exception:
        pass


def _ts():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def log_open():
    _rotate_log_if_big(LOG_FILE_PATH)
    f = open(LOG_FILE_PATH, "a", buffering=1, encoding="utf-8", errors="replace")

    header_1 = f"\n--- Session {_ts()} ---"
    header_2 = (
        f"USER={os.environ.get('USER')}  "
        f"DISPLAY_SERVER={os.environ.get('XDG_SESSION_TYPE')}  "
        f"DRY_RUN={DRY_RUN}"
    )

    f.write(header_1 + "\n")
    f.write(header_2 + "\n")

    print(header_1, flush=True)
    print(header_2, flush=True)

    return f


def log(f, *args):
    try:
        line = " ".join(str(a) for a in args)
        formatted_line = f"[{_ts()}] {line}"

        f.write(formatted_line + "\n")
        print(formatted_line, flush=True)

    except Exception:
        pass
