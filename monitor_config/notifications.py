# -*- coding: utf-8 -*-

import shlex

from .command_utils import run_cmd
from .version_info import APP_NAME


try:
    import gi  # pyright: ignore[reportMissingImports]

    gi.require_version("Notify", "0.7")
    from gi.repository import Notify  # pyright: ignore[reportMissingImports]

    HAS_GI_NOTIFY = True
except Exception:
    Notify = None
    HAS_GI_NOTIFY = False


def init_notifications():
    if HAS_GI_NOTIFY and Notify is not None:
        try:
            Notify.init(APP_NAME)
        except Exception:
            pass


def notify(
    title: str,
    body: str = "",
    urgency: str = "normal",
    timeout_ms: int = 4000,
    logf=None,
):
    """
    KDE/Plasma alatt libnotify → KNotification.
    urgency: low|normal|critical

    Portal backendnél nincs megbízható app ikon, ezért nem adunk meg ikont.
    """
    if HAS_GI_NOTIFY and Notify is not None:
        try:
            n = Notify.Notification.new(title, body, None)

            try:
                n.set_urgency(
                    {
                        "low": Notify.Urgency.LOW,
                        "normal": Notify.Urgency.NORMAL,
                        "critical": Notify.Urgency.CRITICAL,
                    }.get(urgency, Notify.Urgency.NORMAL)
                )
            except Exception:
                pass

            try:
                n.set_timeout(timeout_ms)
            except Exception:
                pass

            n.show()
            return

        except Exception as e:
            if logf:
                from .log_utils import log

                log(logf, f"notify(libnotify) FAIL: {e}")

    cmd = (
        f"notify-send -a {shlex.quote(APP_NAME)} "
        f"-u {shlex.quote(urgency)} -t {timeout_ms} "
        f"{shlex.quote(title)} {shlex.quote(body)}"
    )

    try:
        run_cmd(cmd, logf)
    except Exception as e:
        if logf:
            from .log_utils import log

            log(logf, f"notify(fallback) FAIL: {e}")
