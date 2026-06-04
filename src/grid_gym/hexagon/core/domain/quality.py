"""Telemetrie-Qualitaetsstatus (`GG-DATA-003`).

`Quality` markiert den Vertrauenswert eines Telemetriepunkts. Die
Werte folgen dem Lastenheft (`GG-DATA-003`) und sind als `StrEnum`
realisiert, damit `canonical_json` sie ueber den `str`-Branch
emittieren kann — ohne zusaetzliche Konversion an der Domain-
Eingangsgrenze.

AC-DOMAIN-FROZEN: Enum-Subklassen sind in Python by-construction
immutable (siehe `tools/arch_check.py::_inherits_enum`).
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Final


class Quality(StrEnum):
    """Qualitaetsstatus eines Telemetriepunkts (`GG-DATA-003`)."""

    VALID = "valid"
    STALE = "stale"
    ESTIMATED = "estimated"
    LIMITED = "limited"
    INVALID = "invalid"
    NAN = "nan"
    MISSING = "missing"
    FAULT_INJECTED = "fault_injected"


QUALITY_SEVERITY: Final[Mapping[Quality, int]] = {
    Quality.VALID: 0,
    Quality.ESTIMATED: 1,
    Quality.LIMITED: 2,
    Quality.STALE: 3,
    Quality.FAULT_INJECTED: 4,
    Quality.INVALID: 5,
    Quality.NAN: 6,
    Quality.MISSING: 7,
}
"""M5-Welle-6b-Review F15: worst-case-Severity-Ranking neben der
`Quality`-Enum. Hoeherer Wert = schlechter. Decision-21-fixierte
Ordnung (`MISSING > NAN > INVALID > FAULT_INJECTED > VALID`);
STALE/ESTIMATED/LIMITED haben aktuell keine MVP-Geraete-Emitter,
stehen aber als Forward-Compat-Defense zwischen VALID und FAULT_
INJECTED (softere Degradierungen, kein semantischer Fault).

Co-Lokation mit dem Enum: jeder Welle, der eine neue Quality-
Variante einfuehrt, sieht direkt darunter die Severity-Pflicht-
Erweiterung. Adapter-Layer-Code (HTTP-Devices-Endpunkt, Welle-3-
Dashboard-Chart-Farben) konsumiert diese Mapping read-only.
"""
