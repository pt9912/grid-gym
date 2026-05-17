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

from enum import StrEnum


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
