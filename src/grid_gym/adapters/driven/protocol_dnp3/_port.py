"""`Dnp3DeviceProtocolPort` — DNP3-Adapter als
`DeviceProtocolPort`-Implementer (M4 Welle 5a, ADR 0034).

Sync-Surface (ADR 0030 §2.1) direkt gegen `nfm-dnp3.DNP3Master`
(sync-by-design; alle public Methoden ohne async-Marker, Thread-
Lock-Schutz per Library-Doku); **kein** Adapter-interner
Thread+Loop-Marshal noetig (Decision D-b, ADR 0034 §2.2 — Pattern-
Praezedenz Welle-3-Decision-M-c).

Decision D-d: Class-0-Polling-Read mit Resultat-Filter-by-Index.
`read(target)` ruft `master.read_class(0)` und sucht das
konfigurierte `(group, variation, index)`-Point im typed
`PollResult.analog_inputs`/`.binary_inputs`. Subscription-/Event-
Class-Polling bleibt Welle-6-Schaerfung.

Simulations-/Testadapter (Lastenheft Z. 1161-1163); **keine
produktive Anlagensteuerung**.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Final, Literal, Protocol, cast


# DNP3-Object-Group-Konstanten (ADR 0034 §2.3).
_GROUP_BINARY_INPUT: Final[int] = 1
_GROUP_ANALOG_INPUT: Final[int] = 30

from dnp3py import (
    DNP3CommunicationError,
    DNP3Config,
    DNP3CRCError,
    DNP3Error,
    DNP3Master,
    DNP3ProtocolError,
    DNP3TimeoutError,
)

from grid_gym.adapters.driven.protocol_dnp3._codec import (
    Dnp3CodecError,
    decode_point_value,
)
from grid_gym.adapters.driven.protocol_dnp3._config import (
    Dnp3PointConfig,
    Dnp3ProtocolPortConfig,
)
from grid_gym.adapters.driven.protocol_dnp3._errors import (
    Dnp3PortConnectError,
    Dnp3PortDisconnectError,
    Dnp3PortPointNotInPollResultError,
    Dnp3PortReadAccessMismatchError,
    Dnp3PortReadFailedError,
    Dnp3PortReadNotStartedError,
    Dnp3PortWriteAccessMismatchError,
    Dnp3PortWriteNotImplementedError,
    Dnp3PortWriteNotStartedError,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPortUnknownTargetError,
)


# Strukturelles Protocol fuer den nfm-dnp3 Master.
# Erlaubt Tests, einen Mock durchzureichen, und entkoppelt den
# Adapter von der konkreten `DNP3Master`-Konstruktor-Signatur.
class _DnpMaster(Protocol):
    def open(self) -> None: ...

    def close(self) -> None: ...

    def read_class(self, class_num: int) -> Any: ...


ClientFactory = Callable[[Dnp3ProtocolPortConfig], _DnpMaster]


def _default_client_factory(config: Dnp3ProtocolPortConfig) -> _DnpMaster:
    """Default-Client-Factory: `nfm-dnp3.DNP3Master(DNP3Config(...))`.

    Trennt das Konstruktor-Detail vom Adapter-Pfad, damit Tests den
    Master mocken koennen, ohne die Welle-5a-Default-Wahl zu
    duplizieren.
    """
    dnp_config = DNP3Config(
        host=config.host,
        port=config.port,
        master_address=config.master_address,
        outstation_address=config.outstation_address,
        response_timeout=config.response_timeout_s,
    )
    return cast("_DnpMaster", DNP3Master(dnp_config))


class Dnp3DeviceProtocolPort:
    """DNP3-Adapter (Simulations-/Testadapter; keine produktive
    Anlagensteuerung).

    Implementiert `DeviceProtocolPort` (ADR 0030 §2.1). nfm-dnp3-
    Sync-Master wird **direkt** vom TickLoop-Thread aufgerufen
    (Decision D-b, ADR 0034 §2.2) — kein Background-Polling, kein
    Thread-Marshal, kein Queue-State.

    Lifecycle ist idempotent: Doppel-`start()` ist No-op nach
    erstem erfolgreichem Connect; `stop()` nach erfolglosem
    `start()` ist No-op.

    Welle-5a-Read-Pfad (Decision D-d): jeder `read(target)`-Aufruf
    macht **einen** `master.read_class(0)`-Roundtrip und filtert
    das Resultat nach `(group, variation, index)`. Tick-Caching
    ist Welle-6-Material (generisches Cross-Adapter-Pattern).
    """

    def __init__(
        self,
        config: Dnp3ProtocolPortConfig,
        *,
        client_factory: ClientFactory | None = None,
    ) -> None:
        self._config: Dnp3ProtocolPortConfig = config
        self._client_factory: ClientFactory = client_factory or _default_client_factory
        self._master: _DnpMaster | None = None
        self._started: bool = False

    # ------------------------------------------------------------------
    # `DeviceProtocolPort`-Surface (ADR 0030 §2.1)
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Connect zum DNP3-Outstation. Idempotent."""
        if self._started:
            return
        master = self._client_factory(self._config)
        try:
            master.open()
        except (OSError, DNP3Error) as exc:
            raise Dnp3PortConnectError(self._config.host, self._config.port, str(exc)) from exc
        self._master = master
        self._started = True

    def stop(self) -> None:
        """Disconnect. Idempotent — Doppel-Stop ist No-op."""
        if not self._started or self._master is None:
            return
        master = self._master
        self._master = None
        self._started = False
        try:
            master.close()
        except (OSError, DNP3Error) as exc:
            raise Dnp3PortDisconnectError(str(exc)) from exc

    def read(self, target: str) -> TelemetryPoint | None:
        """Liest Point vom Server via Class-0-Integrity-Poll +
        Resultat-Filter (Decision D-d direkt-sync).

        Wirft `DeviceProtocolPortUnknownTargetError`, wenn das Target
        nicht im Profil ist. Wirft `Dnp3PortReadAccessMismatchError`,
        wenn das Target als `access="write"` konfiguriert ist.
        Wirft `Dnp3PortReadFailedError` bei Library-Fehlern oder
        wenn das Point nicht im Poll-Resultat enthalten ist.
        """
        point_cfg = self._resolve_point_config(target)
        if point_cfg.access != "read":
            raise Dnp3PortReadAccessMismatchError(target, point_cfg.access)
        master = self._require_master(target, "read")
        try:
            poll = master.read_class(0)
        except (
            OSError,
            DNP3CommunicationError,
            DNP3TimeoutError,
            DNP3CRCError,
            DNP3ProtocolError,
        ) as exc:
            raise Dnp3PortReadFailedError(
                target,
                point_cfg.group,
                point_cfg.variation,
                point_cfg.index,
                str(exc),
            ) from exc
        if not getattr(poll, "success", False):
            raise Dnp3PortReadFailedError(
                target,
                point_cfg.group,
                point_cfg.variation,
                point_cfg.index,
                f"poll error: {getattr(poll, 'error', '?')}",
            )
        point = _find_point(poll, point_cfg)
        if point is None:
            raise Dnp3PortPointNotInPollResultError(
                target, point_cfg.group, point_cfg.variation, point_cfg.index
            )
        try:
            value = decode_point_value(point, point_cfg.group, point_cfg.variation)
        except Dnp3CodecError as exc:
            raise Dnp3PortReadFailedError(
                target,
                point_cfg.group,
                point_cfg.variation,
                point_cfg.index,
                str(exc),
            ) from exc
        return _build_telemetry_point(target, point_cfg, value)

    def write(self, target: str, command: Command) -> None:
        """Write-Pfad ist Welle-5a-Anti-Scope (ADR 0034 §2.1;
        Welle-6-Schaerfung).

        Wirft `DeviceProtocolPortUnknownTargetError` bei unbekanntem
        Target, `Dnp3PortWriteAccessMismatchError` bei
        `access="read"`-Targets, sonst
        `Dnp3PortWriteNotImplementedError`.
        """
        point_cfg = self._resolve_point_config(target)
        if point_cfg.access != "write":
            raise Dnp3PortWriteAccessMismatchError(target, point_cfg.access)
        self._require_master(target, "write")
        # Welle-5a-Adapter ist Read-only — wir akzeptieren `command`
        # nur, um den `DeviceProtocolPort`-Vertrag formal zu halten.
        _ = command
        raise Dnp3PortWriteNotImplementedError(target)

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _resolve_point_config(self, target: str) -> Dnp3PointConfig:
        if target not in self._config.points:
            raise DeviceProtocolPortUnknownTargetError(
                target,
                available_targets=tuple(sorted(self._config.points.keys())),
            )
        return self._config.points[target]

    def _require_master(self, target: str, operation: Literal["read", "write"]) -> _DnpMaster:
        if self._master is None:
            if operation == "write":
                raise Dnp3PortWriteNotStartedError(target)
            raise Dnp3PortReadNotStartedError(target)
        return self._master


def _find_point(poll: Any, point_cfg: Dnp3PointConfig) -> Any | None:
    """Sucht das passende Point-Objekt im `PollResult` nach
    `(group, variation, index)`.

    `nfm-dnp3.PollResult` exposed typed Listen
    (`.analog_inputs: list[AnalogInput]`, `.binary_inputs:
    list[BinaryInput]`, etc.). Wir filtern die zur Group passende
    Liste nach `.idx == point_cfg.index`. Variation wird auf der
    Liste-Auswahl-Ebene gefiltert (Group 30/V1 vs. V5 sind beide
    `AnalogInput`-Typed, aber `nfm-dnp3` liefert sie laut Probe-Run
    in derselben Liste; wir akzeptieren das fuer Welle 5a und
    haerten in Welle 6, falls die Library spaeter pro Variation
    separate Listen liefert).
    """
    if point_cfg.group == _GROUP_BINARY_INPUT:
        candidates = getattr(poll, "binary_inputs", None) or ()
    elif point_cfg.group == _GROUP_ANALOG_INPUT:
        candidates = getattr(poll, "analog_inputs", None) or ()
    else:
        # Defensive — Config-Validation pinnt Group auf {1, 30};
        # Andere Werte koennen hier nicht ankommen.
        return None
    for point in candidates:
        # `nfm-dnp3.AnalogInput`/`BinaryInput` haben ein
        # `index`-Field (C1-Probe-Run-Hinweis: `__repr__` zeigt
        # `idx=`, aber das echte Attribut heisst `index`).
        if getattr(point, "index", None) == point_cfg.index:
            return point
    return None


def _build_telemetry_point(target: str, point_cfg: Dnp3PointConfig, value: Any) -> TelemetryPoint:
    """Verpackt einen dekodierten Point-Wert in einen
    `TelemetryPoint` mit Welle-5a-Defaults.

    Pattern analog Welle-3 `protocol_modbus._port._build_telemetry_point`
    und Welle-4 `protocol_opcua._port._build_telemetry_point`:
    `run_id`/`tick`/`simulation_time`/`sequence` sind Caller-
    Verantwortung; der Adapter weiss nichts ueber Simulationszeit.
    """
    return TelemetryPoint(
        run_id="",
        tick=0,
        simulation_time=0,
        device_id=target,
        metric=f"g{point_cfg.group}v{point_cfg.variation}",
        value=value,
        unit="",
        quality=Quality.VALID,
        source=f"protocol_dnp3.{target}",
        sequence=0,
    )
