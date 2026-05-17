"""Test-Doubles fuer die Driven-Ports (M1 Welle 2).

`FakeClock` ist die einzige `ClockPort`-Implementation, die Welle 2
fuer Tests bereitstellt — eine produktive `SimulationClock` wird in
Welle 4 mit dem TickLoop gebaut.

`MersenneTwisterRandomPort` ist gleichzeitig die produktive
`RandomPort`-Implementation und das, was im ADR-0007-Akzeptanztext
als „FixedSeedRandom"-Test-Helper bezeichnet wird. Wir re-exportieren
ihn unter dem ADR-Namen, damit Tests dem Akzeptanztext folgen
koennen, ohne dass es zwei Klassen mit gleichem Verhalten gibt.
"""

from __future__ import annotations

from dataclasses import dataclass

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.ports.driven.clock import SimulationTime


@dataclass(slots=True)
class FakeClock:
    """`ClockPort`-Implementation, die durch `advance()` getrieben wird.

    Bewusst veraenderlich (`frozen=False`): `advance()` mutiert den
    internen Zaehler. AC-DOMAIN-FROZEN gilt nicht — Tests liegen
    nicht unter `hexagon/core/domain/`.
    """

    _now: SimulationTime = 0

    def now(self) -> SimulationTime:
        return self._now

    def advance(self, delta_ms: int) -> None:
        if delta_ms <= 0:
            raise ValueError(f"delta_ms must be positive, got {delta_ms}")
        self._now += delta_ms


FixedSeedRandom = MersenneTwisterRandomPort
"""ADR-0007-§4a-AC2-Alias fuer den produktiven RandomPort.

Tests konstruieren `FixedSeedRandom(seed=...)`, die Implementierung
ist `MersenneTwisterRandomPort`. Verhindert eine zweite Test-Variante
mit divergentem Verhalten.
"""
