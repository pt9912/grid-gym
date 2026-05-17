"""Tests fuer `FakeClock` (M1 Welle 2).

`ClockPort` ist ein reines `typing.Protocol` — strukturelle
Konformitaet liegt bei mypy. Diese Datei testet das konkrete
`FakeClock`-Test-Double aus `_fakes.py` rein per Verhalten.
"""

from __future__ import annotations

import pytest

from tests.unit.hexagon.ports.driven._fakes import FakeClock


def test_fake_clock_starts_at_zero() -> None:
    assert FakeClock().now() == 0


def test_fake_clock_advance_accumulates() -> None:
    clock = FakeClock()
    clock.advance(100)
    clock.advance(50)
    assert clock.now() == 150


def test_fake_clock_advance_rejects_zero() -> None:
    clock = FakeClock()
    with pytest.raises(ValueError, match="delta_ms must be positive"):
        clock.advance(0)


def test_fake_clock_advance_rejects_negative() -> None:
    clock = FakeClock()
    with pytest.raises(ValueError, match="delta_ms must be positive"):
        clock.advance(-1)


def test_fake_clock_now_is_stable_between_advance_calls() -> None:
    """Mehrfaches `now()` zwischen zwei `advance()`-Aufrufen
    liefert denselben Wert — `now()` ist eine reine Frage, kein
    Tick-Treiber."""
    clock = FakeClock()
    clock.advance(42)
    first = clock.now()
    second = clock.now()
    assert first == second == 42
