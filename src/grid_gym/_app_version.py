"""Single-Source der App-/Tool-Version aus den Paket-Metadaten (Slice 059).

Loest die zuvor an zwei Stellen (`adapters.driving.http_api.app` und
`composition._demo_scenario_setup`) hart auf `"0.1.0"` gepinnte Version
zentral aus `importlib.metadata` auf — mit Sentinel-Fallback fuer
nicht-installierte Ad-hoc-Laeufe (Praezedenz: `_resolve_tool_version` in
`tests/integration/_constants.py`).

Bewusst ein Leaf-Modul **ohne** interne `grid_gym`-Importe: `app.py`
importiert `composition._demo_scenario_setup`, deshalb darf keine
Version-Quelle aus `app.py` lesen (Cycle-Vermeidung, `AC-NO-CYCLES`).
Beide Verbraucher importieren stattdessen dieses zyklenfreie Leaf.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import Final

_DISTRIBUTION_NAME: Final[str] = "grid-gym"
_FALLBACK_VERSION: Final[str] = "0.0.0+local"


def resolve_app_version() -> str:
    """App-/Tool-Version aus der installierten `grid-gym`-Distribution.

    Der produktive Docker-Stage ruft `uv sync` und traegt immer die
    `pyproject.toml`-Version. Der Sentinel-Fallback `0.0.0+local` greift
    nur in Umgebungen, in denen `grid-gym` nicht als Distribution
    installiert ist (Ad-hoc-`pytest` ohne `uv sync`) — klar als „nicht
    produktiv" erkennbar, auch wenn er in `RunMetadata.tool_version`
    landet.
    """
    try:
        return _pkg_version(_DISTRIBUTION_NAME)
    except PackageNotFoundError:
        return _FALLBACK_VERSION
