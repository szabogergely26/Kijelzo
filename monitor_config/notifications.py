"""
Értesítési segédek a Monitor Config alkalmazáshoz.

Elsődleges backend:
- libnotify / GObject Introspection

Fallback:
- notify-send parancs
"""

import shlex

from .command_utils import run_cmd
from .log_utils import log


try:
    import gi   #type: ignore

    gi.require_version("Notify", "0.7")

    from gi.repository import Notify    #type: ignore

    HAS_GI_NOTIFY = True

except Exception:
    Notify = None
    HAS_GI_NOTIFY = False


def init_notifications(app_name: str) -> None:
    """
    Értesítési backend inicializálása.

    Ha nincs GI/libnotify, csendben fallback módba kerülünk.
    """

    if not HAS_GI_NOTIFY or Notify is None:
        return

    try:
        Notify.init(app_name)
    except Exception:
        pass


def notify(
    title: str,
    body: str = "",
    urgency: str = "normal",
    timeout_ms: int = 4000,
    logf=None,
    app_name: str = "Monitor Config",
):
    """
    KDE/Plasma alatt libnotify → KNotification.

    urgency: low | normal | critical

    Portal backendnél nem adunk meg app ikont, mert az zavaró lehet.
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

            if logf:
                log(logf, f"notify(libnotify): {title} | {body}")

            return

        except Exception as e:
            if logf:
                log(logf, f"notify(libnotify) FAIL: {e}")

    # fallback: notify-send
    cmd = (
        f"notify-send -a {shlex.quote(app_name)} "
        f"-u {shlex.quote(urgency)} -t {timeout_ms} "
        f"{shlex.quote(title)} {shlex.quote(body)}"
    )

    try:
        run_cmd(cmd, logf)
    except Exception as e:
        if logf:
            log(logf, f"notify(fallback) FAIL: {e}")