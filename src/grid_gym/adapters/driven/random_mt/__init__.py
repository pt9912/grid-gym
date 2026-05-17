"""Mersenne-Twister-Adapter fuer `RandomPort` (`ADR 0007 §5.2`).

Konkrete Driven-Adapter-Implementation des `RandomPort`-Protocols
auf Basis von `random.Random` (stdlib, Mersenne Twister) mit
SHA-256-Sub-Seeding und `canonical_json`-Snapshot-Format.

Modul-Re-Export: `MersenneTwisterRandomPort` ist die einzige
oeffentliche API dieses Pakets. Der `from_snapshot`-Konstruktor
liegt als Klassen-Methode an `MersenneTwisterRandomPort`; das
Port-Modul (`hexagon/ports/driven/random.py`) verzichtet bewusst
auf eine Top-Level-Funktion, um `AC-PORTS-NO-OUT` nicht zu
verletzen.
"""

from __future__ import annotations

from grid_gym.adapters.driven.random_mt.mersenne_twister import (
    MersenneTwisterRandomPort,
)

__all__ = ["MersenneTwisterRandomPort"]
