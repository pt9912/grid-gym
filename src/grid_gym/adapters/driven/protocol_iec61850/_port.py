# SPDX-License-Identifier: GPL-3.0-only
"""`Iec61850DeviceProtocolPort` — IEC-61850-Adapter als
`DeviceProtocolPort`-Implementer (M4 Welle 5b, ADR 0035).

Sync-Surface (ADR 0030 §2.1) direkt gegen
`pyiec61850.mms.MMSClient` (sync-Context-Manager — Probe-Run-Befund
2026-06-01: alle relevanten public Methoden sind sync); **kein**
Adapter-interner Thread+Loop-Marshal noetig (Decision I-b,
ADR 0035 §2.2 — Pattern-Praezedenz Welle-3-Decision-M-c +
Welle-5a-Decision-D-b).

Decision I-d: Per-Target MMS-Read via
`MMSClient.read_value(object_reference, fc)`. RCB-Subscription
und GOOSE-Subscription bleiben Welle-6+-Schaerfung.

Decision I-f (Lizenz-Boundary): `pyiec61850-ng` ist optionales
Extra (`pip install grid-gym[iec61850]`). Der Top-Level-Import
ist in einem Try-Block geschuetzt; ohne installiertes Extra wirft
`Iec61850DeviceProtocolPort.__init__` `Iec61850PortLibraryNotInstalledError`.

Simulations-/Testadapter (Lastenheft Z. 1155-1157); **keine
produktive Anlagensteuerung**.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Final, Literal, Protocol, cast

from grid_gym.adapters.driven.protocol_iec61850._codec import (
    decode_mms_value,
)
from grid_gym.adapters.driven.protocol_iec61850._config import (
    Iec61850LnConfig,
    Iec61850ProtocolPortConfig,
)
from grid_gym.adapters.driven.protocol_iec61850._errors import (
    Iec61850CodecError,
    Iec61850PortConnectError,
    Iec61850PortDisconnectError,
    Iec61850PortLibraryNotInstalledError,
    Iec61850PortPointNotFoundError,
    Iec61850PortReadAccessMismatchError,
    Iec61850PortReadFailedError,
    Iec61850PortReadNotStartedError,
    Iec61850PortWriteAccessMismatchError,
    Iec61850PortWriteNotImplementedError,
    Iec61850PortWriteNotStartedError,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPortUnknownTargetError,
)


# Decision I-f: Optional-Extra-Import-Guard.
# `pyiec61850-ng` ist in `[project.optional-dependencies.iec61850]`,
# nicht in `[project] dependencies`. Ohne `pip install grid-gym[iec61850]`
# ist das Modul nicht importierbar — Adapter-Konstruktor faengt das
# und wirft `Iec61850PortLibraryNotInstalledError`.
try:
    from pyiec61850.mms import (
        ConnectionError as _PyIecConnectionError,
        ConnectionFailedError as _PyIecConnectionFailedError,
        ConnectionTimeoutError as _PyIecConnectionTimeoutError,
        MMSClient as _PyIecMMSClient,
        MMSError as _PyIecMMSError,
        NotConnectedError as _PyIecNotConnectedError,
        ReadError as _PyIecReadError,
        WriteError as _PyIecWriteError,
    )

    _HAS_PYIEC61850 = True
except ImportError:
    # Optional-Extra-Off-Pfad: `pip install grid-gym` ohne `[iec61850]`-
    # Extra installiert pyiec61850-ng nicht. Der Adapter-Konstruktor
    # wirft dann `Iec61850PortLibraryNotInstalledError` mit Install-
    # Hinweis (Decision I-f). Mock-Tests koennen das via
    # `client_factory`-Hook umgehen.
    _HAS_PYIEC61850 = False
    _PyIecMMSClient = None
    _PyIecMMSError = Exception
    _PyIecReadError = Exception
    _PyIecWriteError = Exception
    _PyIecConnectionError = Exception
    _PyIecConnectionFailedError = Exception
    _PyIecConnectionTimeoutError = Exception
    _PyIecNotConnectedError = Exception


# Strukturelles Protocol fuer den MMSClient.
# Erlaubt Tests, einen Mock durchzureichen, und entkoppelt den
# Adapter von der konkreten `MMSClient`-Konstruktor-Signatur.
class _MmsClientLike(Protocol):
    def connect(self, host: str | None = ..., port: int | None = ...) -> bool: ...

    def disconnect(self) -> None: ...

    def read_value(self, reference: str, fc: Any = ...) -> Any: ...


ClientFactory = Callable[[Iec61850ProtocolPortConfig], "_MmsClientLike"]


def _default_client_factory(config: Iec61850ProtocolPortConfig) -> _MmsClientLike:
    """Default-Client-Factory: `pyiec61850.mms.MMSClient(host, port, ...)`.

    Trennt das Konstruktor-Detail vom Adapter-Pfad, damit Tests den
    Client mocken koennen, ohne die Welle-5b-Default-Wahl zu
    duplizieren.
    """
    if not _HAS_PYIEC61850 or _PyIecMMSClient is None:
        raise Iec61850PortLibraryNotInstalledError
    timeout_ms = int(config.response_timeout_s * 1000)
    return cast(
        "_MmsClientLike",
        _PyIecMMSClient(host=config.host, port=config.port, timeout=timeout_ms),
    )


class Iec61850DeviceProtocolPort:
    """IEC-61850-Adapter (Simulations-/Testadapter; keine produktive
    Anlagensteuerung).

    Implementiert `DeviceProtocolPort` (ADR 0030 §2.1).
    `pyiec61850.mms.MMSClient` ist als sync-Context-Manager
    implementiert (Probe-Run-Befund 2026-06-01) und wird direkt
    vom TickLoop-Thread aufgerufen (Decision I-b, ADR 0035 §2.2 —
    Pattern-Praezedenz Welle-3-M-c + Welle-5a-D-b).

    Lifecycle ist idempotent: Doppel-`start()` ist No-op nach
    erstem erfolgreichem Connect; `stop()` nach erfolglosem
    `start()` ist No-op.

    Welle-5b-Read-Pfad (Decision I-d): jeder `read(target)`-Aufruf
    macht **einen** `client.read_value(reference, fc)`-Roundtrip.
    RCB-/GOOSE-Subscription ist Welle-6-Material.
    """

    def __init__(
        self,
        config: Iec61850ProtocolPortConfig,
        *,
        client_factory: ClientFactory | None = None,
    ) -> None:
        if not _HAS_PYIEC61850 and client_factory is None:
            # Decision I-f: ohne Optional-Extra **und** ohne explizit
            # uebergebenen Factory (Test-Hook) ist der Adapter nicht
            # lauffaehig. Tests koennen eine Mock-Factory uebergeben,
            # damit Adapter-Unit-Tests ohne installiertes Extra laufen.
            raise Iec61850PortLibraryNotInstalledError
        self._config: Iec61850ProtocolPortConfig = config
        self._client_factory: ClientFactory = client_factory or _default_client_factory
        self._client: _MmsClientLike | None = None
        self._started: bool = False

    # ------------------------------------------------------------------
    # `DeviceProtocolPort`-Surface (ADR 0030 §2.1)
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Connect zum IEC-61850-Server. Idempotent."""
        if self._started:
            return
        client = self._client_factory(self._config)
        try:
            client.connect(self._config.host, self._config.port)
        except (
            _PyIecConnectionFailedError,
            _PyIecConnectionTimeoutError,
            _PyIecConnectionError,
            OSError,
        ) as exc:
            raise Iec61850PortConnectError(self._config.host, self._config.port, str(exc)) from exc
        self._client = client
        self._started = True

    def stop(self) -> None:
        """Disconnect. Idempotent — Doppel-Stop ist No-op."""
        if not self._started or self._client is None:
            return
        client = self._client
        self._client = None
        self._started = False
        try:
            client.disconnect()
        except (_PyIecMMSError, OSError) as exc:
            raise Iec61850PortDisconnectError(str(exc)) from exc

    def read(self, target: str) -> TelemetryPoint | None:
        """Liest Point vom Server via `read_value(reference, fc)`
        (Decision I-d direkt-sync).

        Wirft `DeviceProtocolPortUnknownTargetError`, wenn das Target
        nicht im Profil ist. Wirft `Iec61850PortReadAccessMismatchError`,
        wenn das Target als `access="write"` konfiguriert ist.
        Wirft `Iec61850PortReadFailedError` bei Library-Fehlern;
        `Iec61850PortPointNotFoundError`, wenn die Library-Message
        auf einen fehlenden Object-Reference hinweist.
        """
        ln_cfg = self._resolve_ln_config(target)
        if ln_cfg.access != "read":
            raise Iec61850PortReadAccessMismatchError(target, ln_cfg.access)
        client = self._require_client(target, "read")
        try:
            raw_value = client.read_value(ln_cfg.object_reference, ln_cfg.functional_constraint)
        except _PyIecNotConnectedError as exc:
            raise Iec61850PortReadNotStartedError(target) from exc
        except _PyIecReadError as exc:
            if _looks_like_object_not_found(str(exc)):
                raise Iec61850PortPointNotFoundError(
                    target, ln_cfg.object_reference, ln_cfg.functional_constraint
                ) from exc
            raise Iec61850PortReadFailedError(
                target,
                ln_cfg.object_reference,
                ln_cfg.functional_constraint,
                str(exc),
            ) from exc
        except _PyIecMMSError as exc:
            raise Iec61850PortReadFailedError(
                target,
                ln_cfg.object_reference,
                ln_cfg.functional_constraint,
                str(exc),
            ) from exc
        try:
            value = decode_mms_value(
                raw_value,
                ln_cfg.datatype,
                ln_cfg.object_reference,
                ln_cfg.functional_constraint,
            )
        except Iec61850CodecError as exc:
            raise Iec61850PortReadFailedError(
                target,
                ln_cfg.object_reference,
                ln_cfg.functional_constraint,
                str(exc),
            ) from exc
        return _build_telemetry_point(target, ln_cfg, value)

    def write(self, target: str, command: Command) -> None:
        """Write-Pfad ist Welle-5b-Anti-Scope (ADR 0035 §2.4;
        Welle-6-Schaerfung).

        Wirft `DeviceProtocolPortUnknownTargetError` bei unbekanntem
        Target, `Iec61850PortWriteAccessMismatchError` bei
        `access="read"`-Targets, sonst
        `Iec61850PortWriteNotImplementedError`.
        """
        ln_cfg = self._resolve_ln_config(target)
        if ln_cfg.access != "write":
            raise Iec61850PortWriteAccessMismatchError(target, ln_cfg.access)
        self._require_client(target, "write")
        _ = command  # Welle-5b ist Read-only
        raise Iec61850PortWriteNotImplementedError(target)

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _resolve_ln_config(self, target: str) -> Iec61850LnConfig:
        if target not in self._config.points:
            raise DeviceProtocolPortUnknownTargetError(
                target,
                available_targets=tuple(sorted(self._config.points.keys())),
            )
        return self._config.points[target]

    def _require_client(self, target: str, operation: Literal["read", "write"]) -> _MmsClientLike:
        if self._client is None:
            if operation == "write":
                raise Iec61850PortWriteNotStartedError(target)
            raise Iec61850PortReadNotStartedError(target)
        return self._client


def _looks_like_object_not_found(message: str) -> bool:
    """Heuristik: pyiec61850-ng hat **kein** typed
    `ObjectReferenceError`; `ReadError`-Library-Messages, die auf
    einen fehlenden Object-Reference hinweisen, werden via Substring-
    Match identifiziert.
    """
    msg = message.lower()
    return (
        "not found" in msg
        or "object reference" in msg
        or "data-access-error" in msg
        or "objectnonexistent" in msg
    )


def _build_telemetry_point(target: str, ln_cfg: Iec61850LnConfig, value: Any) -> TelemetryPoint:
    """Verpackt einen dekodierten Wert in einen `TelemetryPoint` mit
    Welle-5b-Defaults.

    Pattern analog Welle-3 `protocol_modbus._port._build_telemetry_point`,
    Welle-4 `protocol_opcua._port._build_telemetry_point`, Welle-5a
    `protocol_dnp3._port._build_telemetry_point`.
    """
    return TelemetryPoint(
        run_id="",
        tick=0,
        simulation_time=0,
        device_id=target,
        metric=f"{ln_cfg.functional_constraint}.{ln_cfg.datatype}",
        value=value,
        unit="",
        quality=Quality.VALID,
        source=f"protocol_iec61850.{target}",
        sequence=0,
    )


if TYPE_CHECKING:
    # Type-Checker sieht ein nicht-Optional `_PyIecMMSClient`;
    # Runtime-`None`-Pfad ist durch _HAS_PYIEC61850-Guard geschuetzt.
    _MmsClient = _PyIecMMSClient
