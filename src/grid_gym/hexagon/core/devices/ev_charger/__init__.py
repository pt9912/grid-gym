"""`hexagon/core/devices/ev_charger/` — EV-Ladepunkt (M8 Welle 2a).

Implementiert `GG-DEV-015` (EV-Charger, SOLLTE-Geraet aus Lastenheft
§9.4). Kombiniert das Battery-SoC-Muster (endlicher Fahrzeug-Akku) mit
dem GridConnection-Set-Power-Muster (steuerbare, bidirektionale
Leistung) zu einem realistischen Lade-/V2G-Modell mit CC/CV-Kennlinie
und `connection_loss`-Fault. ADR 0055 fixiert das Schema.

Modul-Struktur (Spiegel zu `battery/`, `grid_connection/`):

- `config.py` — `EvChargerConfig` Frozen-Dataclass + Initial-Validator
  + Plug-State-Konstanten.
- `commands.py` — `set_charge_power`/`set_plug_state`-Validatoren +
  `EvChargerAlarm`.
- `snapshot.py` — `EvChargerSnapshot` + dict-Konversion.
- `model.py` — `EvChargerDevice` (`DeviceModel` + `FaultInjectableDevice`).
"""

from __future__ import annotations

from grid_gym.hexagon.core.devices.ev_charger.model import EvChargerDevice

__all__ = ["EvChargerDevice"]
