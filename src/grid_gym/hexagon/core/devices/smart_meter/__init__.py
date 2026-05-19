"""`hexagon/core/devices/smart_meter/` — SmartMeter
(M2 Welle 4b).

Implementiert `GG-DEV-014` (Smart-Meter-Geraetetyp): Stateless
Aggregator ueber `aggregate_device_ids: tuple[str, ...]` mit
neuem `attach_sources(...)`-Lifecycle-Hook (Analogie zu
`attach_random`). Snapshot persistiert **keine** Aggregat-Werte
(derived). ADR 0018 fixiert das Schema.

Modul-Struktur (Spiegel zu `battery/`, `pv/`, `load/`,
`grid_connection/`):

- `config.py` — `SmartMeterConfig` Frozen-Dataclass +
  Initial-Validator.
- `commands.py` — `SmartMeterAlarm` (kein produktiver
  Command-Validator in Welle 4b).
- `snapshot.py` — `SmartMeterSnapshot` + dict-Konversion.
- `model.py` — `SmartMeterDevice` + `attach_sources(...)`.
"""

from __future__ import annotations

from grid_gym.hexagon.core.devices.smart_meter.model import SmartMeterDevice

__all__ = ["SmartMeterDevice"]
