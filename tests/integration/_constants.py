"""Eingefrorene Konstanten fuer M2-Welle-6c-Integrationstests.

`M2_DEMO_SEED` ist der frozen Seed fuer das MVP-Demo-Szenario
(`scenarios/mvp_demo.yaml`); zwei Laeufe mit diesem Seed muessen
byte-identische `TickResult.emitted_telemetry` liefern
(`M2-devices.md §3 Welle 6c`, `GG-MVP-002`).
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as _pkg_version
from pathlib import Path
from typing import Final

M2_DEMO_SEED: Final[int] = 0xC0FFEE
"""Frozen Seed fuer das MVP-Demo-Szenario. Dezimal `12648430`."""

MVP_DEMO_SCENARIO_PATH: Final[Path] = Path(__file__).parent / "scenarios" / "mvp_demo.yaml"
"""Pfad zur YAML-Fixture des MVP-Demo-Szenarios."""

MIN_DETERMINISM_TICKS: Final[int] = 100
"""Mindest-Tick-Anzahl fuer den Determinismus-Vergleich
(`M2-devices.md §3 Welle 6c`)."""

FAULT_DEMO_SCENARIO_PATH: Final[Path] = Path(__file__).parent / "scenarios" / "fault_demo.yaml"
"""Pfad zur YAML-Fixture des Fault-Demo-Szenarios (M3-Welle-2 Item 7)."""

FAULT_DEMO_TICKS: Final[int] = 30
"""Tick-Anzahl fuer den Fault-Demo-Lauf — deckt beide
Fault-Windows + Recovery ab."""

_FALLBACK_TOOL_VERSION: Final[str] = "0.0.0+local"
"""Sentinel-Version fuer Test-Umgebungen, in denen `grid-gym` nicht
als Distribution installiert ist (z. B. ad-hoc `pytest`-Lauf ohne
`uv sync`). Klar erkennbar als „nicht produktiv" — landet so auch
im `RunMetadata.tool_version` der Test-Roundtrips."""


def _resolve_tool_version() -> str:
    """Welle-6c-Review-Folge-2 L-3: try/except gegen
    `PackageNotFoundError` schuetzt Test-Module vor Import-Fehlern
    in Runnern, die das Paket nicht als Distribution installiert
    haben. Der produktive Docker-Test-Stage ruft `uv sync` und
    hat den Wert immer; der Fallback greift nur fuer
    Ad-hoc-Lokal-Laeufe."""
    try:
        return _pkg_version("grid-gym")
    except PackageNotFoundError:
        return _FALLBACK_TOOL_VERSION


DEMO_TOOL_VERSION: Final[str] = _resolve_tool_version()
"""Tool-Version aus `pyproject.toml` (via `importlib.metadata`)
mit Sentinel-Fallback, falls die Distribution nicht installiert
ist. Welle-6c-Review L-3 + Review-Folge-2-L-3: ersetzt den
hardcoded `"0.1.0"`-Wert und schuetzt gleichzeitig vor
`PackageNotFoundError` in nicht-installierten Test-Umgebungen."""
