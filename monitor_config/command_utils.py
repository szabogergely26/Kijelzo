"""
Általános parancsfuttató segédek a Monitor Config alkalmazáshoz.
"""

import os
import re
import subprocess

from .log_utils import log


ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s or "")


def run_cmd(cmd: str, f=None):
    env = os.environ.copy()
    env.setdefault("TERM", "dumb")

    if f:
        log(f, "$", cmd)

    p = subprocess.run(
        cmd,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    out = strip_ansi(p.stdout)
    err = strip_ansi(p.stderr)

    if f:
        if (p.stdout or "").strip():
            log(f, "STDOUT_RAW:", out.rstrip())

        if (p.stderr or "").strip():
            log(f, "STDERR_RAW:", err.rstrip())

        log(f, f"RC={p.returncode}")

    return p.returncode, out, err