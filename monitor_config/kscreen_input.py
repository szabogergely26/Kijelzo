
from dataclasses import dataclass
from pathlib import Path
import re


CONFIG_DIR = Path.home() / ".config" / "monitor-config"
KSCREEN_INPUT_PATH = CONFIG_DIR / "kscreen-input.txt"


@dataclass(frozen=True)
class KScreenMode:
    mode_id: str
    token: str
    active: bool
    preferred: bool


@dataclass(frozen=True)
class KScreenOutput:
    output_id: str
    name: str
    connected: bool
    enabled: bool
    priority: int
    is_panel: bool
    modes: tuple[KScreenMode, ...]
    active_mode: str | None
    preferred_mode: str | None
    position: tuple[int, int]
    geometry_size: tuple[int, int]


@dataclass(frozen=True)
class KScreenParsedState:
    raw_text: str
    outputs: dict[str, KScreenOutput]

    @property
    def connected_outputs(self) -> set[str]:
        return {name for name, output in self.outputs.items() if output.connected}

    @property
    def active_outputs(self) -> set[str]:
        return {
            name
            for name, output in self.outputs.items()
            if output.connected and output.enabled
        }


OUTPUT_RE = re.compile(r"^Output:\s+(\d+)\s+(\S+)\s*$", re.MULTILINE)
MODE_RE = re.compile(r"(\d+):(\d+x\d+@\d+(?:\.\d+)?)([*!]*)")
GEOMETRY_RE = re.compile(r"^\s*Geometry:\s+(-?\d+),(-?\d+)\s+(\d+)x(\d+)\s*$", re.MULTILINE)
PRIORITY_RE = re.compile(r"^\s*priority\s+(\d+)\s*$", re.MULTILINE)


def ensure_kscreen_input_file() -> Path:
    """Létrehozza a config mappát és az üres KScreen inputfájlt."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not KSCREEN_INPUT_PATH.exists():
        KSCREEN_INPUT_PATH.write_text("", encoding="utf-8")

    return KSCREEN_INPUT_PATH


def read_kscreen_input() -> str:
    """Beolvassa a mentett `kscreen-doctor -o` kimenetet."""
    path = ensure_kscreen_input_file()
    return path.read_text(encoding="utf-8", errors="replace")


def _parse_output_block(output_id: str, name: str, block: str) -> KScreenOutput:
    modes: list[KScreenMode] = []

    modes_line = next(
        (line for line in block.splitlines() if line.strip().startswith("Modes:")),
        "",
    )

    for match in MODE_RE.finditer(modes_line):
        flags = match.group(3)
        modes.append(
            KScreenMode(
                mode_id=match.group(1),
                token=match.group(2),
                active="*" in flags,
                preferred="!" in flags,
            )
        )

    active_mode = next((mode.token for mode in modes if mode.active), None)
    preferred_mode = next((mode.token for mode in modes if mode.preferred), None)

    geometry_match = GEOMETRY_RE.search(block)
    if geometry_match:
        position = (int(geometry_match.group(1)), int(geometry_match.group(2)))
        geometry_size = (int(geometry_match.group(3)), int(geometry_match.group(4)))
    else:
        position = (0, 0)
        geometry_size = (0, 0)

    priority_match = PRIORITY_RE.search(block)
    priority = int(priority_match.group(1)) if priority_match else 0

    lines = {line.strip() for line in block.splitlines()}

    return KScreenOutput(
        output_id=output_id,
        name=name,
        connected="connected" in lines,
        enabled="enabled" in lines,
        priority=priority,
        is_panel="Panel" in lines,
        modes=tuple(modes),
        active_mode=active_mode,
        preferred_mode=preferred_mode,
        position=position,
        geometry_size=geometry_size,
    )


def parse_kscreen_text(text: str) -> KScreenParsedState:
    """A `kscreen-doctor -o` teljes kimenetét strukturált állapottá alakítja."""
    matches = list(OUTPUT_RE.finditer(text))
    outputs: dict[str, KScreenOutput] = {}

    for index, match in enumerate(matches):
        block_start = match.start()
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[block_start:block_end]

        output_id = match.group(1)
        name = match.group(2)
        outputs[name] = _parse_output_block(output_id, name, block)

    return KScreenParsedState(raw_text=text, outputs=outputs)


def get_saved_kscreen_state() -> KScreenParsedState:
    """Beolvassa és feldolgozza a mentett KScreen inputfájlt."""
    return parse_kscreen_text(read_kscreen_input())


def has_usable_kscreen_input() -> bool:
    """Csak egyértelműen felismerhető laptopkijelzővel használható."""
    state = get_saved_kscreen_state()
    connected = [output for output in state.outputs.values() if output.connected]
    panels = [output for output in connected if output.is_panel]
    return bool(connected) and len(panels) == 1


def clear_kscreen_input_file() -> Path:
    """Kiüríti a KScreen inputfájlt az új kijelzőfelvételhez."""
    path = ensure_kscreen_input_file()
    path.write_text("", encoding="utf-8")
    return path