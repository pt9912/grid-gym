"""`hexagon/core/devices/grid_connection/` — Netzanschlusspunkt
(M2 Welle 4a).

Implementiert `GG-DEV-012` (Netzanschlusspunkt-Geraetetyp):
Stateful Anschlusspunkt mit kumulativen `import_kwh` /
`export_kwh`-Summen. Sign-Konvention: `power_kw > 0` = Import
(Energie ins lokale System), `< 0` = Export (Energie ins Netz).
ADR 0017 fixiert das Schema.

Modul-Struktur (Spiegel zu `battery/`, `pv/`, `load/`):

- `config.py` — `GridConnectionConfig` Frozen-Dataclass +
  Initial-Validator.
- `commands.py` — `set_power_kw`-Validator + `GridConnectionAlarm`.
- `snapshot.py` — `GridConnectionSnapshot` + dict-Konversion.
- `model.py` — `GridConnectionDevice`.
"""

from __future__ import annotations

from grid_gym.hexagon.core.devices.grid_connection.model import (
    GridConnectionDevice,
)

__all__ = ["GridConnectionDevice"]
