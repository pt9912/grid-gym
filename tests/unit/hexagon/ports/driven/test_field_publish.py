"""Protocol-Shape-Tests fuer `FieldPublishPort` (Field-Server-Surface,
ADR 0075 §2.1).

Muster aus `test_device_protocol.py`:
- Inline-Stub (kein Test-Fake-Modul; der produktive Adapter
  `MqttFieldPublishAdapter` kommt in Slice-073-C3 unter
  `adapters/driven/field_publish_mqtt/`).
- `isinstance(stub, FieldPublishPort)` per `@runtime_checkable`.
- Lifecycle-/Publish-Surface-Aufruf zur Sanity.
- `*Error`-Hierarchie-Verifikation.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.errors import GridGymError
from grid_gym.hexagon.ports.driven.field_publish import (
    FieldPublishPort,
    FieldPublishPortError,
    FieldPublishPortPublishError,
    FieldPublishPortStartError,
    FieldPublishPortStopError,
)


class _RecordingFieldPublishPort:
    """Inline-Stub: zeichnet Lifecycle- und Publish-Aufrufe auf."""

    def __init__(self) -> None:
        self.start_calls: int = 0
        self.stop_calls: int = 0
        self.published: list[TelemetryPoint] = []

    def start(self) -> None:
        self.start_calls += 1

    def publish(self, point: TelemetryPoint) -> None:
        self.published.append(point)

    def stop(self) -> None:
        self.stop_calls += 1


def _point() -> TelemetryPoint:
    return TelemetryPoint(
        run_id="run-1",
        tick=0,
        simulation_time=0,
        device_id="meter-1",
        metric="voltage_v",
        value=Decimal("230"),
        unit="V",
        quality=Quality.VALID,
        source="smart_meter.meter-1",
        sequence=0,
    )


def test_recording_stub_satisfies_field_publish_port_protocol() -> None:
    """`@runtime_checkable` erlaubt isinstance-Check ohne explizite
    Subclass-Deklaration."""
    port = _RecordingFieldPublishPort()
    assert isinstance(port, FieldPublishPort)


def test_lifecycle_methods_record_invocation() -> None:
    """Sanity: start/stop landen im Stub (driver-getrieben,
    ADR 0075 §2.4)."""
    port = _RecordingFieldPublishPort()
    port.start()
    port.stop()
    port.stop()
    assert port.start_calls == 1
    assert port.stop_calls == 2


def test_publish_records_point() -> None:
    """Sanity: `publish` nimmt den Domaenen-`TelemetryPoint`
    (ADR 0075 §2.1 — volle `Decimal`-Fidelity)."""
    port = _RecordingFieldPublishPort()
    point = _point()
    port.publish(point)
    assert port.published == [point]
    assert port.published[0].value == Decimal("230")


# ---------------------------------------------------------------------------
# Error-Hierarchie (ADR 0075 §2.1)
# ---------------------------------------------------------------------------


def test_field_publish_port_error_is_grid_gym_error_subclass() -> None:
    """Pattern-Konsistenz mit anderen Driven-Port-Errors."""
    assert issubclass(FieldPublishPortError, GridGymError)


@pytest.mark.parametrize(
    "subclass",
    [
        FieldPublishPortStartError,
        FieldPublishPortPublishError,
        FieldPublishPortStopError,
    ],
)
def test_typed_errors_inherit_from_field_publish_port_error(
    subclass: type[FieldPublishPortError],
) -> None:
    """Alle typed Sub-Errors erben vom Wurzel-Error (Adapter kann
    pauschal `FieldPublishPortError` catchen)."""
    assert issubclass(subclass, FieldPublishPortError)
