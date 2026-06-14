"""`hexagon/core/devices/transformer/` — Transformator (M8 Welle 2b).

Implementiert `GG-DEV-016` (Transformator, SOLLTE-Geraet aus Lastenheft
§9.4). Folgt dem GridConnection-Set-Power-Muster (ADR 0017) mit
Wandlungsverhaeltnis, Eisen-/Kupferverlusten, Saettigungs-Hard-Cap und
`winding_fault`-Schutzausloesung. ADR 0056 fixiert das Schema.

Modul-Struktur (Spiegel zu `grid_connection/`, `ev_charger/`):

- `config.py` — `TransformerConfig` Frozen-Dataclass + Initial-Validator.
- `commands.py` — `set_power_kw`-Validator + `TransformerAlarm`.
- `snapshot.py` — `TransformerSnapshot` + dict-Konversion.
- `model.py` — `TransformerDevice` (`DeviceModel` + `FaultInjectableDevice`).
"""

from __future__ import annotations

from grid_gym.hexagon.core.devices.transformer.model import TransformerDevice

__all__ = ["TransformerDevice"]
