"""Architektur-Check fuer grid-gym (Spike-0 Skelett).

Spike-0-Pfad gemaess ADR 0002 §A-1: dieses Skript implementiert
schrittweise die Contracts, die `import-linter` und `ruff` nicht
abdecken (AC-NO-CYCLES, AC-NO-TIME Aufruf-Sites, AC-NO-RAND Aufruf-
Sites, AC-NO-JSON, AC-DOMAIN-FROZEN, AC-NO-GOD-UTILS,
AC-TYPED-ERRORS, AC-ADAPTER-LIGHTWEIGHT).

Welle 1: Skelett — laedt die Whitelist-Konfiguration aus
`[tool.grid_gym.arch_check]` in `pyproject.toml`, baut den
Import-Graph via `grimp` und gibt eine Zusammenfassung aus.
Contract-Logik kommt in Welle 3.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from typing import Any

import grimp


def main() -> int:
    """Welle-1-Spike-0: liest Config, baut Graph, gibt OK zurueck."""
    config = _load_arch_check_config()
    graph = grimp.build_graph("grid_gym")
    modules = list(graph.modules)
    print(f"[arch_check] grid_gym modules in graph: {len(modules)}")
    print(f"[arch_check] whitelist sections: {sorted(config.keys())}")
    print("[arch_check] Welle 1 Skelett — Contract-Logik folgt in Welle 3.")
    return 0


def _load_arch_check_config() -> dict[str, Any]:
    """Laedt `[tool.grid_gym.arch_check]` aus der Projekt-`pyproject.toml`."""
    project_root = Path(__file__).resolve().parent.parent
    pyproject_path = project_root / "pyproject.toml"
    with pyproject_path.open("rb") as fh:
        data: dict[str, Any] = tomllib.load(fh)
    tool_section: dict[str, Any] = data.get("tool", {})
    grid_gym_section: dict[str, Any] = tool_section.get("grid_gym", {})
    arch_check_section: dict[str, Any] = grid_gym_section.get("arch_check", {})
    return arch_check_section


if __name__ == "__main__":
    sys.exit(main())
