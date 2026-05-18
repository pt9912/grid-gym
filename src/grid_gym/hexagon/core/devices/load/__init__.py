"""`hexagon/core/devices/load/` — Load-Geraetemodell (M2 Welle 3b).

Implementiert `GG-DEV-013` (Lastprofile-Geraetetyp): konstantes
`rated_power_kw`-Verbrauchsmodell mit optionalem `set_power_kw`-
Override. ADR 0016 fixiert das Schema (gemeinsam mit PV).
"""

from __future__ import annotations

from grid_gym.hexagon.core.devices.load.model import LoadDevice

__all__ = ["LoadDevice"]
