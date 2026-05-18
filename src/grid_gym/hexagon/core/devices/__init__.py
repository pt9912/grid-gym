"""`hexagon/core/devices/` — Geraete-Subsysteme (M2).

Modul-Struktur (gewachsen ueber M2-Wellen):

- `_protocol.py` (M2 Welle 1) — `DeviceModel`-Protocol, Vertrag fuer
  jede konkrete Geraete-Implementation (`GG-DEV-001..003`).
- `battery/` (M2 Welle 2) — `BatteryDevice` + Snapshot-Schema
  (`GG-DEV-010`, `GG-BESS-001..005,008`).
- `pv/`, `load/` (M2 Welle 3) — PV- und Last-Geraete
  (`GG-DEV-011`, `GG-DEV-013`).
- `smart_meter/`, `grid_connection/` (M2 Welle 4) — Smart Meter +
  Anschlusspunkt (`GG-DEV-014`, `GG-DEV-012`).

Re-Export von `DeviceModel` als Top-Level-Symbol des Pakets, damit
Geraete-Implementationen kurz importieren koennen:

    from grid_gym.hexagon.core.devices import DeviceModel
"""

from __future__ import annotations

from grid_gym.hexagon.core.devices._protocol import DeviceModel

__all__ = ["DeviceModel"]
