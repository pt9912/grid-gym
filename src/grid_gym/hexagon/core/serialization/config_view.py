"""Versionierte ConfigView fuer `RunMetadata.config_hash`
(Slice 038 / ADR 0073 §2.4).

`config_hash` erfasst die determinismus-relevante Runtime-
Konfiguration **ausserhalb** des Szenarios — exakt die Klasse von
Knobs, die ADR 0052 §2.1 bewusst aus dem Scenario-Schema
herausgehalten hat (`scenario_hash`-Pin-Schutz). Das Verfahren
spiegelt das `scenario_hash`-Praezedenzmuster:
`sha256(canonical_json(payload)).hexdigest()`.

Die ConfigView ist explizit und versioniert (`config_view`-
Schluessel): jedes kuenftige determinismus-relevante Runtime-Knob
ausserhalb des Szenarios MUSS aufgenommen werden (ConfigView-
Versions-Bump; additive ADR-0011-Schaerfung von ADR 0073).
Nicht-determinismus-relevante Knobs (Wall-Clock-Pacing, Ports,
DSNs, Log-Level) bleiben draussen.
"""

from __future__ import annotations

import hashlib
from typing import Final

from grid_gym.hexagon.core.serialization.canonical import canonical_json

CONFIG_VIEW_VERSION: Final[int] = 1
"""Version der ConfigView-Payload (ADR 0073 §2.4). Bump bei jeder
Aufnahme eines neuen determinismus-relevanten Runtime-Knobs."""


def config_hash_for(*, max_age_ms: int | None) -> str:
    """SHA-256-Hexdigest der ConfigView v1 (ADR 0073 §2.4).

    ConfigView v1 traegt genau ein Knob: `max_age_ms` (ADR 0052
    §2.1 `STALE`-Quality-Stage; `None` = Stage aus). Der Hash ist
    deterministisch by-construction (`canonical_json` sortiert
    Schluessel, verbietet float/NaN).
    """
    payload = {"config_view": CONFIG_VIEW_VERSION, "max_age_ms": max_age_ms}
    return hashlib.sha256(canonical_json(payload)).hexdigest()
