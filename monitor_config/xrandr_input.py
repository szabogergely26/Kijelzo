# -*- coding: utf-8 -*-

from dataclasses import dataclass
from pathlib import Path
import re


CONFIG_DIR = Path.home() / ".config" / "monitor-config"
XRANDR_INPUT_PATH = CONFIG_DIR / "xrandr-input.txt"


@dataclass(frozen=True)
class XrandrParsedState:
    raw_text: str
    connected_outputs: set[str]
    active_outputs: set[str]


def ensure_xrandr_input_file() -> Path:
    """
    Létrehozza a monitor-config config mappát és az üres xrandr input fájlt,
    ha még nem léteznek.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not XRANDR_INPUT_PATH.exists():
        XRANDR_INPUT_PATH.write_text("", encoding="utf-8")

    return XRANDR_INPUT_PATH


def read_xrandr_input() -> str:
    """
    Beolvassa az xrandr input fájl tartalmát.
    Ha nincs még fájl, előbb létrehozza üresen.
    """
    path = ensure_xrandr_input_file()
    return path.read_text(encoding="utf-8", errors="replace")


def parse_xrandr_text(text: str) -> XrandrParsedState:
    """
    xrandr kimenetből kinyeri:
      - connected outputok
      - aktív outputok

    Aktívnak azt tekintjük, ahol a connected sorban van aktuális mód + pozíció,
    például: 1920x1080+0+0
    """
    connected_outputs: set[str] = set()
    active_outputs: set[str] = set()

    for line in text.splitlines():
        connected_match = re.match(r"^(\S+)\s+connected\b", line)
        if not connected_match:
            continue

        name = connected_match.group(1)
        connected_outputs.add(name)

        if re.search(r"\b\d{3,5}x\d{3,5}\+\d+\+\d+\b", line):
            active_outputs.add(name)

    return XrandrParsedState(
        raw_text=text,
        connected_outputs=connected_outputs,
        active_outputs=active_outputs,
    )


def get_saved_xrandr_state() -> XrandrParsedState:
    """
    Beolvassa és parse-olja a mentett xrandr fájlt.
    """
    return parse_xrandr_text(read_xrandr_input())


def has_usable_xrandr_input() -> bool:
    """
    Akkor használható, ha van legalább egy connected output.
    Üres fájl vagy rossz tartalom esetén False.
    """
    state = get_saved_xrandr_state()
    return bool(state.connected_outputs)


def clear_xrandr_input_file() -> Path:
    """
    Újratanításhoz kiüríti az xrandr input fájlt.
    """
    path = ensure_xrandr_input_file()
    path.write_text("", encoding="utf-8")
    return path
