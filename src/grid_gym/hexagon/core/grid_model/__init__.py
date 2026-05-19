"""`hexagon/core/grid_model/` — Netzbilanzmodell (M2 Welle 5).

Single-Instance-System-Modell **neben** den Geraeten (kein
DeviceModel; siehe ADR 0019 §1 / §3). Implementiert
`GG-GRID-001` (Frequenz) und `GG-GRID-002` (Spannung).

Modul-Struktur (Welle-5a-Stand):

- `config.py` — `GridModelConfig` Frozen-Dataclass mit
  Invarianten (positive Sollwerte/Sensitivitaeten + strikte
  Clamp-Reihenfolge).
- `bilanz.py` — `GridModelBilanz` mit `update(...)` und
  Property-Gettern.
- `snapshot.py` — `GridModelSnapshot` + Welle-0a-Codec-
  basierte dict-Konversion.

Welle 5b ergaenzt `loads.py` (`LoadEvent` + `LoadProfile`
+ CSV/JSON-Loader; ADR 0020).
"""

from __future__ import annotations

from grid_gym.hexagon.core.grid_model.bilanz import GridModelBilanz
from grid_gym.hexagon.core.grid_model.config import (
    GridModelConfig,
    GridModelConfigError,
    GridModelConfigInvalidValueError,
)
from grid_gym.hexagon.core.grid_model.snapshot import (
    CONFIG_FIELD_NAMES,
    MODEL_KIND_SIMPLIFIED_PROPORTIONAL,
    SNAPSHOT_VERSION,
    SUBSYSTEM,
    GridModelSnapshot,
)

# Welle-5a-Review L-1: Welle-4a-Review-L-3-Pattern (Single-Source-
# of-Truth-Konstanten an der obersten Modul-Schnittstelle).
__all__ = [
    "CONFIG_FIELD_NAMES",
    "MODEL_KIND_SIMPLIFIED_PROPORTIONAL",
    "SNAPSHOT_VERSION",
    "SUBSYSTEM",
    "GridModelBilanz",
    "GridModelConfig",
    "GridModelConfigError",
    "GridModelConfigInvalidValueError",
    "GridModelSnapshot",
]
