"""Kommando-Endstatus (`GG-DATA-004`).

`CommandResult` markiert den End-Status eines Steuerbefehls. Jeder
Befehl endet in genau einem dieser Werte (`GG-DATA-004`). Realisiert
als `StrEnum`, damit `canonical_json` ueber den `str`-Branch
serialisieren kann.

AC-DOMAIN-FROZEN: Enum-Subklassen sind by-construction immutable
(siehe `tools/arch_check.py::_inherits_enum`).
"""

from __future__ import annotations

from enum import StrEnum


class CommandResult(StrEnum):
    """End-Status eines Steuerbefehls (`GG-DATA-004`)."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    LIMITED = "limited"
    EXPIRED = "expired"
    FAILED = "failed"
    IGNORED = "ignored"
