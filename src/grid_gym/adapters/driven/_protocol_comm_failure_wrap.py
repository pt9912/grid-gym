"""Cross-Adapter-Comm-Failure-Wrapper fuer `DeviceProtocolPort`-
Implementer (M7 Welle 3b, ADR 0053; `GG-SAFE-003`).

Composition-Wrapper, der einen bereits-konstruierten konkreten
`DeviceProtocolPort` (MQTT/Modbus/OPC-UA/DNP3/IEC-61850) um die
fehlende `GG-SAFE-003`-Folge-Substanz ergaenzt: typisierte
Read-Fehler (Verbindungsverlust mid-flight, Timeouts, Poll-
Fehler — alle `DeviceProtocolPortReadError`-Subklassen, z. B.
`Iec61850PortReadConnectionLostError`) werden auf einen
synthetisierten `TelemetryPoint` mit `Quality.MISSING` plus
einen `adapter_communication_lost`-Alarm gemappt, statt zum
Caller zu propagieren. Pattern-Sibling zu
`_protocol_otel_wrap.py` (ADR 0024 §4.5; Composition statt
per-Adapter-Edit, ADR 0053 §2.2).

**Scope-Abgrenzungen (ADR 0053 §2.3 + §7):**

- `read() → None` (MQTT-leere-Queue-Poll) ist KEIN Ausfall —
  bleibt `None`, kein Point, kein Alarm.
- `start()`/`stop()`/`write()` bleiben Pass-Through fail-fast:
  ein Lauf ohne Verbindung soll nicht still mit `MISSING`
  starten (`start_protocol_ports` propagiert mit LIFO-Cleanup);
  der Command-Pfad ist `CommandResult`-/Device-Domaene.
- Der Wrapper ist **opt-in** (Verdrahter-Entscheidung):
  ungewrappte Adapter verhalten sich unveraendert.
- Komposition mit dem OTel-Wrapper: Comm-Failure **aussen**,
  OTel innen — der OTel-Span sieht den Original-Fehler als
  `error`-Event, bevor dieser Wrapper ihn in Daten wandelt
  (ADR 0053 §2.2; Unit-Test pinnt die Reihenfolge).

**Kontext-Injection (ADR 0053 §2.5):** die gewrappten Adapter
bauen `TelemetryPoint`s bewusst mit Platzhalter-Kontext
(„Caller-Verantwortung", z. B. `protocol_modbus/_port.py`).
Alarm + synthetisierter Point brauchen aber `run_id` +
Sim-Zeit — der Wrapper traegt sie keyword-only injiziert
(`run_id` + `clock: ClockPort`; `ClockPort` ist die
deterministische Sim-Zeit-Quelle, `AC-NO-TIME` gewahrt). Der
Wrapper wird **pro Lauf** konstruiert.

**Alarm-Nebenkanal-Robustheit (ADR 0053 §2.4, Review-Folge
F1):** der GESAMTE Alarm-Nebenkanal (Alarm-Konstruktion inkl.
`alarm_id_source` + `on_alarm`-Callback) ist Best-Effort
gefangen (geteiltes Catch-Tupel aus
`_protocol_wrap_common.py`) — der `MISSING`-Point hat Vorrang
vor dem Alarm-Nebenkanal. Pro gefangenem Fehler wird die
Sim-Zeit genau einmal gelesen — Point und Alarm tragen
denselben Zeitstempel (Review-Folge F2).
"""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import Callable
from decimal import Decimal
from typing import TYPE_CHECKING

from grid_gym.adapters.driven._protocol_wrap_common import (
    BEST_EFFORT_CALLBACK_EXCEPTIONS,
)
from grid_gym.hexagon.core.domain.alarm import Alarm
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPort,
    DeviceProtocolPortReadError,
)

if TYPE_CHECKING:
    from grid_gym.hexagon.core.domain.command import Command
    from grid_gym.hexagon.ports.driven.clock import ClockPort, SimulationTime


ADAPTER_COMMUNICATION_LOST_CODE = "adapter_communication_lost"
"""ADR 0053 §2.4: vierter stabiler Alarm-Code neben
`power_clamp_limited`/`command_rejected`/`smart_meter_rejected`
(`alarm_mappers.py`-Konvention)."""

_COMM_FAILURE_SOURCE_PREFIX = "comm_failure"
"""ADR 0053 §2.6: `source`-Praefix synthetisierter Points —
maschinell unterscheidbar von regulaeren Adapter-Emissionen
(`protocol_<typ>.<target>`)."""

_ZERO = Decimal("0")

# Best-Effort-Catch-Tupel fuer den Alarm-Nebenkanal — geteilte
# Single-Source mit `_protocol_otel_wrap.py` (Review-Folge F4;
# ADR 0024 §2.4-Semantik): bekannte Callback-Bug-Klassen werden
# geschluckt (der MISSING-Point hat Vorrang), unbekannte
# Exceptions propagieren als sichtbares Signal.
_BEST_EFFORT_ALARM_EXCEPTIONS = BEST_EFFORT_CALLBACK_EXCEPTIONS


def _default_alarm_id_source() -> str:
    """Production-Default fuer die Alarm-ID-Generierung
    (`uuid.uuid4` als String; ADR 0040 Decision 16). Tests
    injizieren einen monoton zaehlenden Stub via
    `alarm_id_source`-Konstruktor-Kwarg (Pattern identisch
    `tick_loop._default_alarm_id_source`)."""
    return str(uuid.uuid4())


class CommFailureGuardedDeviceProtocolPort:
    """Composition-Wrapper um einen `DeviceProtocolPort`-
    Implementer: `read()`-Fehler → `Quality.MISSING`-Point +
    `adapter_communication_lost`-Alarm (M7 Welle 3b, ADR 0053).

    Implementiert selbst das `DeviceProtocolPort`-Protocol;
    `start()`/`stop()`/`write()` werden ungewrappt durchgereicht
    (fail-fast-Bestand, ADR 0053 §2.3/§7).

    Konstruktor-Argumente (keyword-only ausser `wrapped`):

    - `wrapped` — der konkrete Adapter (oder ein bereits
      OTel-gewrappter Adapter; Comm-Failure gehoert aussen).
    - `run_id` — Lauf-Identitaet fuer Point + Alarm
      (`GG-DATA-001`); der Wrapper wird pro Lauf konstruiert.
    - `clock` — `ClockPort` (deterministische Sim-Zeit fuer
      `simulation_time`/`simulation_time_ms`; `AC-NO-TIME`).
    - `on_alarm` — Alarm-Senke; der Verdrahter entscheidet das
      Ziel (`AlarmStreamPort.publish` + History-Buffer im
      API-Kontext; Listen-Collector im Test). Best-Effort
      gegen Callback-Fehler.
    - `alarm_id_source` — uuid4-Default; Test-Stub fuer
      deterministische Asserts (ADR 0040 Decision 16).
    """

    def __init__(
        self,
        wrapped: DeviceProtocolPort,
        *,
        run_id: str,
        clock: "ClockPort",
        on_alarm: Callable[[Alarm], None],
        alarm_id_source: Callable[[], str] | None = None,
    ) -> None:
        self._wrapped: DeviceProtocolPort = wrapped
        self._run_id: str = run_id
        self._clock: "ClockPort" = clock
        self._on_alarm: Callable[[Alarm], None] = on_alarm
        self._alarm_id_source: Callable[[], str] = alarm_id_source or _default_alarm_id_source

    # ------------------------------------------------------------------
    # `DeviceProtocolPort`-Surface
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Pass-Through fail-fast (ADR 0053 §7): ein Lauf ohne
        Verbindung startet nicht still mit `MISSING` —
        `start_protocol_ports` propagiert mit LIFO-Cleanup."""
        self._wrapped.start()

    def stop(self) -> None:
        """Pass-Through fail-fast; analog `start()`."""
        self._wrapped.stop()

    def read(self, target: str) -> TelemetryPoint | None:
        """`read()` mit Comm-Failure-Mapping (ADR 0053 §2.3):
        `DeviceProtocolPortReadError`-Subklassen → synthetisierter
        `Quality.MISSING`-Point (§2.6) + `adapter_communication_
        lost`-Alarm (§2.4). `None` (MQTT-leere Queue) bleibt
        `None` — kein Ausfall.

        Review-Folge F1/F2: die Sim-Zeit wird genau EINMAL pro
        Fehler gelesen (Point + Alarm teilen den Zeitstempel);
        der gesamte Alarm-Nebenkanal (Konstruktion inkl.
        `alarm_id_source` + Callback) ist Best-Effort gefangen —
        der `MISSING`-Point hat Vorrang."""
        try:
            return self._wrapped.read(target)
        except DeviceProtocolPortReadError as exc:
            now_ms = self._clock.now()
            with contextlib.suppress(*_BEST_EFFORT_ALARM_EXCEPTIONS):
                self._emit_comm_lost_alarm(target, exc, now_ms)
            return self._missing_point(target, now_ms)

    def write(self, target: str, command: "Command") -> None:
        """Pass-Through fail-fast (ADR 0053 §7): der Command-Pfad
        ist `CommandResult`-/Device-Domaene (ADR 0040 §2.1) —
        Write-Fehler propagieren typisiert."""
        self._wrapped.write(target, command)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _missing_point(self, target: str, now_ms: "SimulationTime") -> TelemetryPoint:
        """ADR 0053 §2.6: synthetisierter `MISSING`-Point.

        `tick`/`sequence` folgen der Platzhalter-Konvention der
        gewrappten Adapter („Caller-Verantwortung");
        `metric`/`unit` bleiben leer (die Codec-Konfiguration des
        Targets ist bewusst Adapter-intern — keine
        Codec-Introspektion); `value` = 0 (Praezedenz
        SmartMeter-pre-attach-MISSING, ADR 0018 §2.3). `now_ms`
        kommt vom Caller — ein Zeitstempel pro Fehler (F2)."""
        return TelemetryPoint(
            run_id=self._run_id,
            tick=0,
            simulation_time=now_ms,
            device_id=target,
            metric="",
            value=_ZERO,
            unit="",
            quality=Quality.MISSING,
            source=f"{_COMM_FAILURE_SOURCE_PREFIX}.{target}",
            sequence=0,
        )

    def _emit_comm_lost_alarm(
        self,
        target: str,
        exc: DeviceProtocolPortReadError,
        now_ms: "SimulationTime",
    ) -> None:
        """ADR 0053 §2.4: `adapter_communication_lost`-Alarm mit
        den drei Akzeptanz-Pflichtfeldern Ziel (`target`),
        Startzeit (`simulation_time_ms`, Sim-Zeit — identisch mit
        `Point.simulation_time`, F2) und Ursache (`message`,
        Exception-Klassenname maschinenlesbar praefixt).
        Best-Effort liegt am Call-Site in `read()` (F1): auch
        Konstruktions-Fehler (z. B. werfender `alarm_id_source`)
        verhindern den `MISSING`-Point nicht."""
        alarm = Alarm(
            alarm_id=self._alarm_id_source(),
            run_id=self._run_id,
            simulation_time_ms=now_ms,
            target=target,
            code=ADAPTER_COMMUNICATION_LOST_CODE,
            severity="warning",
            message=f"{exc.__class__.__name__}: {exc}",
            status="active",
            fault_id=None,
        )
        self._on_alarm(alarm)
