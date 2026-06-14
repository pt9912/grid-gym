"""`hexagon/core/devices/wind_turbine/` — Windkraftanlage (M8 Welle 2c).

Implementiert `GG-DEV-017` (Windkraftanlage, SOLLTE-Geraet aus Lastenheft
§9.4). Command-loser Generator nach dem PV-Muster (ADR 0016) mit
stochastischem seeded `RandomPort`-Windeingang und kubischer
Leistungskennlinie (cut-in/rated/cut-out). ADR 0057 fixiert das Schema.

Modul-Struktur (kein `commands.py`/Alarm — Wind ist stochastisch
getrieben, nimmt keine Steuerbefehle):

- `config.py` — `WindTurbineConfig` Frozen-Dataclass + Initial-Validator.
- `snapshot.py` — `WindTurbineSnapshot` + dict-Konversion.
- `model.py` — `WindTurbineDevice` (`DeviceModel`).
"""

from __future__ import annotations

from grid_gym.hexagon.core.devices.wind_turbine.model import WindTurbineDevice

__all__ = ["WindTurbineDevice"]
