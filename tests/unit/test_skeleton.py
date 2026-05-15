"""Smoke-Test fuer das Spike-0-Skelett.

Stellt sicher, dass das Top-Level-Paket importierbar ist und die
Wurzel-Fehlerklasse `GridGymError` (AC-TYPED-ERRORS) als
Exception-Subklasse verfuegbar ist. Welle 2 ergaenzt echte
Property-Tests fuer die kanonische Serialisierung.
"""

from __future__ import annotations

from grid_gym.hexagon.core.errors import GridGymError


def test_grid_gym_error_is_exception_subclass() -> None:
    assert issubclass(GridGymError, Exception)


def test_grid_gym_error_carries_message_args() -> None:
    err = GridGymError("smoke")
    assert err.args == ("smoke",)
    assert str(err) == "smoke"
