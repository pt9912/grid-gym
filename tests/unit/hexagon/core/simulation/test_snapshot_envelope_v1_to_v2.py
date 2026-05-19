"""Pflicht-Test fuer ADR 0015 §2.4 (M2 Welle 6a):

`TickLoop.from_snapshot(state)` auf einem v1-TickLoop-Snapshot
wirft typisierten `TickLoopSnapshotVersionError`. Backward-Compat-
Reader ist out-of-scope (M6 `GG-PERSIST-*`-Migrations-Slice).

Separates Test-Modul (statt Verschmelzung in `test_tick_loop.py`),
weil der v1-Reject ein eigener Vertrags-Vertrag ist (ADR 0015 §2.4
Pflicht-Test). Welle 6 / M6 referenzieren diese Datei in der
Closure-Notiz.
"""

from __future__ import annotations

import pytest

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.errors import TickLoopSnapshotVersionError
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import FakeClock


def _v1_state() -> dict[str, object]:
    """Baut ein synthetisches v1-TickLoop-Snapshot-Mapping
    (Welle-4-M1-Format, vor dem Welle-6a-Bump)."""
    return {
        "version": 1,
        "run_id": "legacy-m1-run",
        "simulation_time": 0,
        "tick_count": 0,
        "tick_ms": 100,
        "sub_snapshots": {
            "scheduler": {"version": 1, "pending_events": []},
            "random_root": {
                "version": 1,
                "seed": 0,
                "sub_path": [],
                "rng_version": 3,
                "rng_state": [0] * 625,
            },
        },
    }


def test_from_snapshot_rejects_v1_with_typed_error() -> None:
    """ADR 0015 §2.4 Pflicht-Vertrag: v1-Snapshot -> typisierter
    Fehler. Pflicht-Message-Tokens (Welle-6a-Review M-1):
    - Beide Versionen (`1` und `2`).
    - Verweis auf M6 `GG-PERSIST-*`-Migrations-Slice."""
    state = _v1_state()
    with pytest.raises(TickLoopSnapshotVersionError) as exc_info:
        TickLoop.from_snapshot(
            state,
            clock=FakeClock(),
            random=MersenneTwisterRandomPort(seed=0),
        )
    message = str(exc_info.value)
    assert "1" in message  # gefundene Version
    assert "2" in message  # erwartete Version
    assert "M6" in message  # Migrations-Slice-Pointer
    assert "GG-PERSIST" in message  # Lastenheft-/Roadmap-Token


def test_v1_reject_message_keeps_test_assertion_simple() -> None:
    """Der Test pinnt den Typ + die beiden Versionen in der Message,
    nicht den vollen Wortlaut. Eine spaetere Schaerfung der
    Message-Form (z.B. Hinweis auf M6 GG-PERSIST-*) ist Doku-Sync,
    nicht Vertragsbruch."""
    state = _v1_state()
    with pytest.raises(TickLoopSnapshotVersionError):
        TickLoop.from_snapshot(
            state,
            clock=FakeClock(),
            random=MersenneTwisterRandomPort(seed=0),
        )
