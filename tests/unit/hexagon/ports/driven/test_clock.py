"""Tests fuer `ClockPort`/`FakeClock` (M1 Welle 2).

ClockPort ist ein reines `typing.Protocol` — strukturelle Pruefung
laeuft ueber `isinstance(fake, ClockPort)`-Vertraglichkeit (mypy
faengt das statisch ueber `runtime_checkable`-Annotation, hier
explizit nur Verhaltens-Tests).
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


def test_fake_clock_now_is_idempotent_without_advance() -> None:
    clock = FakeClock()
    clock.advance(42)
    first = clock.now()
    second = clock.now()
    assert first == second == 42
