"""`hexagon/core/devices/pv/` — PV-Geraetemodell (M2 Welle 3).

Implementiert `GG-DEV-011` (PV-Anlagen-Geraetetyp): konstantes
`rated_power_kw`-Erzeugungsmodell mit optionalem `set_power_kw`-
Override. ADR 0016 fixiert das Schema (gemeinsam mit Load).

Modul-Struktur (spiegel zu `battery/`):

- `config.py` — `PvConfig` Frozen-Dataclass + Initial-Validator.
- `commands.py` — `set_power_kw`-Validator + `PvAlarm`.
- `snapshot.py` — `PvSnapshot` + dict-Konversion.
- `model.py` — `PvDevice`.
"""

from __future__ import annotations

from grid_gym.hexagon.core.devices.pv.model import PvDevice

__all__ = ["PvDevice"]
