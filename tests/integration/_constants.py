"""Eingefrorene Konstanten fuer M2-Welle-6c-Integrationstests.

`M2_DEMO_SEED` ist der frozen Seed fuer das MVP-Demo-Szenario
(`scenarios/mvp_demo.yaml`); zwei Laeufe mit diesem Seed muessen
byte-identische `TickResult.emitted_telemetry` liefern
(`M2-devices.md §3 Welle 6c`, `GG-MVP-002`).
"""

from __future__ import annotations

from importlib.metadata import version as _pkg_version
from pathlib import Path
from typing import Final

M2_DEMO_SEED: Final[int] = 0xC0FFEE
"""Frozen Seed fuer das MVP-Demo-Szenario. Dezimal `12648430`."""

MVP_DEMO_SCENARIO_PATH: Final[Path] = Path(__file__).parent / "scenarios" / "mvp_demo.yaml"
"""Pfad zur YAML-Fixture des MVP-Demo-Szenarios."""

MIN_DETERMINISM_TICKS: Final[int] = 100
"""Mindest-Tick-Anzahl fuer den Determinismus-Vergleich
(`M2-devices.md §3 Welle 6c`)."""

DEMO_TOOL_VERSION: Final[str] = _pkg_version("grid-gym")
"""Tool-Version aus `pyproject.toml` (via `importlib.metadata`).
Welle-6c-Review L-3: ersetzt den hardcoded `"0.1.0"`-Wert, damit
`RunMetadata.tool_version` automatisch mit Versions-Bumps geht."""
