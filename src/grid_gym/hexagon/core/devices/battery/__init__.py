"""`hexagon/core/devices/battery/` — Battery-Geraetemodell (M2 Welle 2).

Implementiert `GG-DEV-010` (Battery-Speicher-Geraetetyp) und
`GG-BESS-001..005, 008` (SOC, Lade-/Entladegrenzen, Wirkungsgrade,
Ramp-Limits, Sicherheitsgrenzen-Validierung, Initialparameter-
Validierung). ADR 0014 fixiert das Snapshot-Schema + Command-
Surface.

Modul-Struktur:

- `config.py` — `BatteryConfig` Frozen-Dataclass + Initial-Validator
  (`GG-BESS-008`).
- `commands.py` — `BatteryAlarm` Frozen-Dataclass + Command-Validator
  (`GG-BESS-002`).
- `snapshot.py` — `BatterySnapshot` Frozen-Dataclass + dict-
  Konversion (`from_dict`/`to_dict`).
- `model.py` — `BatteryDevice` (`DeviceModel`-Implementation).

Re-Export: `BatteryDevice` als Top-Level-Symbol des Pakets.
"""

from __future__ import annotations

from grid_gym.hexagon.core.devices.battery.model import BatteryDevice

__all__ = ["BatteryDevice"]
