# -*- coding: utf-8 -*-

from .kscreen_input import KScreenParsedState, get_saved_kscreen_state, parse_kscreen_text
from .log_utils import log


def _detect_from_state(
    state: KScreenParsedState,
    f=None,
    source="KScreen",
    enabled_only: bool = False,
):
    connected = [output for output in state.outputs.values() if output.connected]
    enabled = [output for output in connected if output.enabled]
    considered = enabled if enabled_only else connected
    panels = [output for output in considered if output.is_panel]
    external = [output for output in considered if not output.is_panel]

    if f:
        log(f, f"[{source}-DETECT] connected={[o.name for o in connected]}")
        log(f, f"[{source}-DETECT] enabled={[o.name for o in enabled]}")
        log(f, f"[{source}-DETECT] panels={[o.name for o in panels]}")
        log(f, f"[{source}-DETECT] external={[o.name for o in external]}")

    if len(panels) != 1:
        return (
            "ismeretlen",
            "A laptop belső kijelzője nem azonosítható egyértelműen.",
        )

    if len(external) >= 2:
        return (
            "Laptop + TV + Soundbar",
            "Laptop + két külső kijelző elérhető.",
        )

    if len(external) == 1:
        return (
            "Laptop + Soundbar",
            "Laptop + egy külső kijelző elérhető.",
        )

    return (
        "Laptop (csak)",
        "Csak a laptop kijelzője érhető el.",
    )


def detect_saved_kscreen_setup(f=None):
    """A mentett `kscreen-input.txt` alapján választ elérhető profilt."""
    return _detect_from_state(
        get_saved_kscreen_state(),
        f=f,
        source="KSCREEN-FILE",
    )


def detect_current_kscreen_setup(text: str, f=None):
    """Egy friss `kscreen-doctor -o` kimenetből állapítja meg a felállást."""
    return _detect_from_state(
        parse_kscreen_text(text),
        f=f,
        source="KSCREEN-LIVE",
        enabled_only=True,
    )
