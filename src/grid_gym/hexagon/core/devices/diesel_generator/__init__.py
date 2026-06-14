"""`hexagon/core/devices/diesel_generator/` — Dieselgenerator (M8 Welle 2d).

Implementiert `GG-DEV-018` (Dieselgenerator, SOLLTE-Geraet aus Lastenheft
§9.4). Dispatchbarer Generator nach dem Battery-Muster (ADR 0014) mit
endlicher Ressource (Kraftstoff), Verbrauch, Ramp, Anfahr-/Abstell-
Hysterese und `genset_fault`-Schutz. ADR 0058 fixiert das Schema.

Modul-Struktur (Spiegel zu `battery/`):

- `config.py` — `DieselGeneratorConfig` Frozen-Dataclass + Validator.
- `commands.py` — `set_power_kw`-Validator + `DieselGeneratorAlarm`.
- `snapshot.py` — `DieselGeneratorSnapshot` + dict-Konversion.
- `model.py` — `DieselGeneratorDevice` (`DeviceModel` +
  `FaultInjectableDevice`).
"""

from __future__ import annotations

from grid_gym.hexagon.core.devices.diesel_generator.model import DieselGeneratorDevice

__all__ = ["DieselGeneratorDevice"]
