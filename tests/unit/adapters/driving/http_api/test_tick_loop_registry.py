"""Unit-Tests fuer `TickLoopRegistry`-Healthcheck-Mapping
(M5 Welle 4a + M6 Welle 6).

Deckt `register_healthcheck_adapter`/`healthcheck_adapter_for`/
`any_healthcheck_adapter` ab — die Substanz wird sonst nur von
Integration-Smokes getroffen, die nicht ins (`tests/unit`-only)
Coverage-Gate zaehlen. Der Adapter-Wert wird von der Registry nicht
inspiziert, daher reicht ein Duck-Typed-Fake.
"""

from __future__ import annotations

from typing import cast

from grid_gym.adapters.driving.http_api._tick_loop_healthcheck import (
    TickLoopHealthcheckAdapter,
)
from grid_gym.adapters.driving.http_api._tick_loop_registry import TickLoopRegistry


def _fake_adapter() -> TickLoopHealthcheckAdapter:
    return cast(TickLoopHealthcheckAdapter, object())


def test_any_healthcheck_adapter_is_none_when_empty() -> None:
    assert TickLoopRegistry().any_healthcheck_adapter() is None


def test_any_healthcheck_adapter_returns_registered() -> None:
    registry = TickLoopRegistry()
    adapter = _fake_adapter()
    registry.register_healthcheck_adapter("run-1", adapter)

    assert registry.any_healthcheck_adapter() is adapter
    assert registry.healthcheck_adapter_for("run-1") is adapter
    assert registry.healthcheck_adapter_for("missing") is None
