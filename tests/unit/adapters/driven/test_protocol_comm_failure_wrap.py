"""Cross-Adapter-Comm-Failure-Wrap-Tests (M7 Welle 3b, ADR 0053;
`GG-SAFE-003`).

Verifiziert dass der `CommFailureGuardedDeviceProtocolPort`-
Composition-Wrapper:

- typisierte `read()`-Fehler aller Adapter-Familien (Modbus/
  OPC-UA/DNP3/IEC-61850-ConnectionLost + generische
  `DeviceProtocolPortReadError`) auf einen synthetisierten
  `Quality.MISSING`-Point (ADR 0053 §2.6 Feld-Vertrag) plus
  einen `adapter_communication_lost`-Alarm mit den drei
  Akzeptanz-Pflichtfeldern Ziel/Startzeit/Ursache mappt
  (§2.3/§2.4).
- `read() → None` (MQTT-leere-Queue-Familie) und erfolgreiche
  Reads unveraendert durchreicht — kein Point, kein Alarm.
- Nicht-Read-Fehler (`write`/`start`) NICHT faengt
  (Pass-Through fail-fast, §2.3/§7).
- Alarm-Nebenkanal-Fehler (werfender `on_alarm` UND werfender
  `alarm_id_source` — Review-Folge F1: der gesamte Nebenkanal
  inkl. Alarm-Konstruktion) Best-Effort schluckt — der
  `MISSING`-Point hat Vorrang (§2.4; 3b-R3).
- pro gefangenem Fehler die Sim-Zeit genau einmal liest —
  Point und Alarm tragen denselben Zeitstempel (Review-Folge
  F2).
- mit dem OTel-Wrapper komponiert (Comm-Failure aussen, OTel
  innen) — der innere Span sieht den Original-Fehler als
  `error`-Event, der aeussere Wrapper liefert den
  `MISSING`-Point (§2.2; 3b-R2).

Tests verwenden `MagicMock(spec=DeviceProtocolPort)`
(Slice-034-F7-Pattern: Protocol-Surface-Drift wird erkannt)
+ `FakeClock` + geteilten `RecordingTracePort` (`_fakes.py`,
Review-Folge F3) + Listen-Collector als `on_alarm`-Senke.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from grid_gym.adapters.driven._protocol_comm_failure_wrap import (
    ADAPTER_COMMUNICATION_LOST_CODE,
    CommFailureGuardedDeviceProtocolPort,
)
from grid_gym.adapters.driven._protocol_otel_wrap import (
    OtelSpanWrappedDeviceProtocolPort,
)
from grid_gym.adapters.driven.protocol_dnp3 import Dnp3PortReadFailedError
from grid_gym.adapters.driven.protocol_iec61850 import (
    Iec61850PortReadConnectionLostError,
)
from grid_gym.adapters.driven.protocol_modbus import ModbusPortReadFailedError
from grid_gym.adapters.driven.protocol_opcua import OpcuaPortReadFailedError
from grid_gym.hexagon.core.domain.alarm import Alarm
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPort,
    DeviceProtocolPortReadError,
    DeviceProtocolPortStartError,
    DeviceProtocolPortWriteError,
)
from tests.unit.hexagon.ports.driven._fakes import FakeClock, RecordingTracePort

_RUN_ID = "welle-3b-comm-failure-test"


# ---------------------------------------------------------------------------
# Test-Helpers
# ---------------------------------------------------------------------------


def _make_wrapper(
    adapter: DeviceProtocolPort,
    *,
    alarms: list[Alarm],
    now_ms: int = 5000,
) -> CommFailureGuardedDeviceProtocolPort:
    clock = FakeClock()
    clock.advance(now_ms)
    return CommFailureGuardedDeviceProtocolPort(
        adapter,
        run_id=_RUN_ID,
        clock=clock,
        on_alarm=alarms.append,
        alarm_id_source=lambda: f"alarm-{len(alarms)}",
    )


def _make_failing_adapter(exc: BaseException) -> DeviceProtocolPort:
    adapter = MagicMock(spec=DeviceProtocolPort)
    adapter.read.side_effect = exc
    return adapter


def _make_command(target: str) -> Command:
    return Command(
        command_id=f"cmd-{target}",
        simulation_time=0,
        target_device_id=target,
        type="set",
        payload={"value": 1.0},
        validation_status="validated",
        result=CommandResult.ACCEPTED,
    )


def _make_point(target: str) -> TelemetryPoint:
    return TelemetryPoint(
        run_id="",
        tick=0,
        simulation_time=0,
        device_id=target,
        metric="power_kw",
        value=Decimal("42"),
        unit="kW",
        quality=Quality.VALID,
        source=f"protocol_test.{target}",
        sequence=0,
    )


class _CountingClock:
    """`ClockPort`-Double, das `now()`-Calls zaehlt — pinnt
    Review-Folge F2 (genau ein Sim-Zeit-Read pro gefangenem
    Fehler; Point und Alarm teilen den Zeitstempel)."""

    def __init__(self, now_ms: int) -> None:
        self._now = now_ms
        self.now_calls = 0

    def now(self) -> int:
        self.now_calls += 1
        return self._now

    def advance(self, delta_ms: int) -> None:
        self._now += delta_ms


# ---------------------------------------------------------------------------
# Read-Fehler → MISSING + Alarm (pro Adapter-Familie)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("family", "exc"),
    [
        ("modbus", ModbusPortReadFailedError("t-modbus", 40001, "connection reset")),
        ("opcua", OpcuaPortReadFailedError("t-opcua", "ns=2;i=2", "BadSessionClosed")),
        ("dnp3", Dnp3PortReadFailedError("t-dnp3", 30, 5, 0, "poll timeout")),
        (
            "iec61850",
            Iec61850PortReadConnectionLostError("t-iec", "IED1/LD0/MMXU1.TotW", "MX"),
        ),
        ("generic", DeviceProtocolPortReadError("raw read failure")),
    ],
)
def test_read_error_yields_missing_point_and_alarm(
    family: str, exc: DeviceProtocolPortReadError
) -> None:
    """ADR 0053 §2.3/§2.4: jede `DeviceProtocolPortReadError`-
    Subklasse (alle Adapter-Familien; die MQTT-Familie hat keine —
    ihr leere-Queue-Pfad ist der None-Test unten) wird auf
    `Quality.MISSING` + `adapter_communication_lost`-Alarm
    gemappt."""
    alarms: list[Alarm] = []
    wrapper = _make_wrapper(_make_failing_adapter(exc), alarms=alarms)

    point = wrapper.read("target-1")

    assert point is not None, f"{family}: MISSING-Point statt Exception erwartet"
    assert point.quality is Quality.MISSING
    assert len(alarms) == 1, f"{family}: genau ein Alarm pro gefangenem Read-Fehler"
    alarm = alarms[0]
    assert alarm.code == ADAPTER_COMMUNICATION_LOST_CODE
    assert alarm.severity == "warning"
    assert alarm.target == "target-1", "Akzeptanz-Pflichtfeld Ziel"
    assert alarm.simulation_time_ms == 5000, "Akzeptanz-Pflichtfeld Startzeit (Sim-Zeit)"
    assert alarm.message.startswith(f"{exc.__class__.__name__}: "), (
        "Akzeptanz-Pflichtfeld Ursache — Exception-Klassenname maschinenlesbar praefixt"
    )
    assert alarm.run_id == _RUN_ID
    assert alarm.status == "active"
    assert alarm.fault_id is None
    assert alarm.alarm_id == "alarm-0", "injizierter alarm_id_source-Stub (ADR 0040 D-16)"


def test_missing_point_field_contract() -> None:
    """ADR 0053 §2.6: vollstaendiger Feld-Vertrag des
    synthetisierten Points — Wrapper-Kontext (run_id/Sim-Zeit) +
    Platzhalter-Konvention (tick/sequence) + leere metric/unit
    (keine Codec-Introspektion) + `comm_failure.`-source-Praefix."""
    alarms: list[Alarm] = []
    wrapper = _make_wrapper(
        _make_failing_adapter(DeviceProtocolPortReadError("boom")),
        alarms=alarms,
        now_ms=7777,
    )

    point = wrapper.read("meter-9")

    assert point == TelemetryPoint(
        run_id=_RUN_ID,
        tick=0,
        simulation_time=7777,
        device_id="meter-9",
        metric="",
        value=Decimal("0"),
        unit="",
        quality=Quality.MISSING,
        source="comm_failure.meter-9",
        sequence=0,
    )


# ---------------------------------------------------------------------------
# Pass-Through-Pfade
# ---------------------------------------------------------------------------


def test_none_read_is_not_a_failure() -> None:
    """ADR 0053 §2.3: `read() → None` (MQTT-leere Queue,
    regulaerer Non-Blocking-Poll) ist KEIN Ausfall — bleibt
    `None`, kein Point, kein Alarm."""
    alarms: list[Alarm] = []
    adapter = MagicMock(spec=DeviceProtocolPort)
    adapter.read.return_value = None
    wrapper = _make_wrapper(adapter, alarms=alarms)

    assert wrapper.read("t-mqtt") is None
    assert alarms == []


def test_successful_read_passes_point_through_unchanged() -> None:
    """Erfolgs-Pfad: der Original-Point des Adapters wird
    identisch durchgereicht — kein Alarm, keine Mutation."""
    alarms: list[Alarm] = []
    original = _make_point("t-ok")
    adapter = MagicMock(spec=DeviceProtocolPort)
    adapter.read.return_value = original
    wrapper = _make_wrapper(adapter, alarms=alarms)

    assert wrapper.read("t-ok") is original
    assert alarms == []


def test_non_read_errors_propagate_uncaught() -> None:
    """ADR 0053 §2.3/§7: `write`-/`start`-Fehler bleiben
    fail-fast — kein Mapping, kein Alarm (der Command-Pfad ist
    Device-Domaene; ein Lauf ohne Verbindung startet nicht still
    mit MISSING)."""
    alarms: list[Alarm] = []
    adapter = MagicMock(spec=DeviceProtocolPort)
    adapter.write.side_effect = DeviceProtocolPortWriteError("write boom")
    adapter.start.side_effect = DeviceProtocolPortStartError("start boom")
    wrapper = _make_wrapper(adapter, alarms=alarms)

    with pytest.raises(DeviceProtocolPortWriteError):
        wrapper.write("t-1", _make_command("t-1"))
    with pytest.raises(DeviceProtocolPortStartError):
        wrapper.start()
    assert alarms == []


# ---------------------------------------------------------------------------
# Robustheit + Komposition
# ---------------------------------------------------------------------------


def test_on_alarm_failure_does_not_suppress_missing_point() -> None:
    """3b-R3 / ADR 0053 §2.4: ein werfender `on_alarm`-Callback
    wird Best-Effort geschluckt — der `MISSING`-Point hat
    Vorrang vor dem Alarm-Nebenkanal."""

    def _broken_sink(alarm: Alarm) -> None:
        raise RuntimeError("alarm sink down")

    clock = FakeClock()
    clock.advance(1000)
    wrapper = CommFailureGuardedDeviceProtocolPort(
        _make_failing_adapter(DeviceProtocolPortReadError("boom")),
        run_id=_RUN_ID,
        clock=clock,
        on_alarm=_broken_sink,
    )

    point = wrapper.read("t-1")
    assert point is not None
    assert point.quality is Quality.MISSING


def test_alarm_id_source_failure_does_not_suppress_missing_point() -> None:
    """Review-Folge F1: der GESAMTE Alarm-Nebenkanal ist
    Best-Effort — auch ein Fehler in der Alarm-KONSTRUKTION
    (werfender `alarm_id_source`, VOR dem `on_alarm`-Call)
    verhindert den `MISSING`-Point nicht."""
    alarms: list[Alarm] = []
    clock = FakeClock()
    clock.advance(1000)

    def _broken_id_source() -> str:
        raise RuntimeError("id source down")

    wrapper = CommFailureGuardedDeviceProtocolPort(
        _make_failing_adapter(DeviceProtocolPortReadError("boom")),
        run_id=_RUN_ID,
        clock=clock,
        on_alarm=alarms.append,
        alarm_id_source=_broken_id_source,
    )

    point = wrapper.read("t-1")
    assert point is not None
    assert point.quality is Quality.MISSING
    assert alarms == [], "Alarm-Konstruktion brach — kein halber Alarm emittiert"


def test_single_clock_read_per_failure_shares_timestamp() -> None:
    """Review-Folge F2: pro gefangenem Read-Fehler wird die
    Sim-Zeit genau EINMAL gelesen — `Point.simulation_time` und
    `Alarm.simulation_time_ms` tragen denselben Stempel (kein
    Divergenz-Risiko bei fortschreitender Clock)."""
    alarms: list[Alarm] = []
    clock = _CountingClock(3000)
    wrapper = CommFailureGuardedDeviceProtocolPort(
        _make_failing_adapter(DeviceProtocolPortReadError("boom")),
        run_id=_RUN_ID,
        clock=clock,
        on_alarm=alarms.append,
        alarm_id_source=lambda: "alarm-0",
    )

    point = wrapper.read("t-1")

    assert clock.now_calls == 1, "genau ein Sim-Zeit-Read pro Fehler"
    assert point is not None
    assert point.simulation_time == 3000
    assert alarms[0].simulation_time_ms == 3000


def test_composition_outer_comm_failure_inner_otel() -> None:
    """3b-R2 / ADR 0053 §2.2: Komposition Comm-Failure AUSSEN /
    OTel INNEN — der innere Span sieht den Original-Fehler als
    `error`-Event (und wird geschlossen), der aeussere Wrapper
    liefert trotzdem den `MISSING`-Point + Alarm."""
    alarms: list[Alarm] = []
    trace = RecordingTracePort()
    inner = OtelSpanWrappedDeviceProtocolPort(
        _make_failing_adapter(
            Iec61850PortReadConnectionLostError("t-iec", "IED1/LD0/MMXU1.TotW", "MX")
        ),
        trace,
        "iec61850",
    )
    wrapper = _make_wrapper(inner, alarms=alarms)

    point = wrapper.read("t-iec")

    assert point is not None
    assert point.quality is Quality.MISSING
    assert len(alarms) == 1
    assert len(trace.spans) == 1
    span = trace.spans[0]
    assert span.name == "protocol.iec61850.read"
    assert span.ended, "Span-Lifecycle bleibt garantiert (finally-Pfad)"
    error_events = [event for event in span.events if event[0] == "error"]
    assert len(error_events) == 1, "der innere Span sieht den Original-Fehler"
    assert error_events[0][1]["exception.type"] == "Iec61850PortReadConnectionLostError"


def test_default_alarm_id_source_is_uuid() -> None:
    """ADR 0040 Decision 16: ohne injizierten Stub liefert der
    Default eine UUIDv4-formatige Alarm-ID."""
    alarms: list[Alarm] = []
    clock = FakeClock()
    clock.advance(1000)
    wrapper = CommFailureGuardedDeviceProtocolPort(
        _make_failing_adapter(DeviceProtocolPortReadError("boom")),
        run_id=_RUN_ID,
        clock=clock,
        on_alarm=alarms.append,
    )

    wrapper.read("t-1")
    assert len(alarms) == 1
    # UUIDv4-String: 36 Zeichen, 4 Bindestriche.
    assert len(alarms[0].alarm_id) == 36
    assert alarms[0].alarm_id.count("-") == 4
