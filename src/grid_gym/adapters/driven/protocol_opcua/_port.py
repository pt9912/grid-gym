"""`OpcuaDeviceProtocolPort` — OPC-UA-Adapter als
`DeviceProtocolPort`-Implementer (M4 Welle 4, ADR 0033).

Sync-Surface (ADR 0030 §2.1) ueber Adapter-internen
`OpcuaLoopThread`-Marshal: `asyncua.Client` lebt in einem
dedizierten asyncio-Loop-Thread, `read()`/`write()` ruft
Coroutinen via `run_coroutine_threadsafe` (Decision O-b,
ADR 0033 §2.2).

Decision O-d: Polling-Read via `client.get_node(node_id).read_value()`
und Direct-Write via `node.write_value(variant)`. Subscription-Pfad
mit Monitored Items bleibt Welle-6-Schaerfung.

Simulations-/Testadapter (Lastenheft Z. 1161-1163); **keine
produktive Anlagensteuerung**.
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from typing import Protocol, cast

from asyncua import Client, ua
from asyncua.ua import uaerrors

from grid_gym.adapters.driven.protocol_opcua._loop_thread import (
    OpcuaLoopThread,
    OpcuaLoopThreadError,
)

from grid_gym.adapters.driven.protocol_opcua._codec import (
    OpcuaCodecError,
    OpcuaCodecPayloadTypeError,
    decode_variant_to_value,
    encode_value_to_variant,
)
from grid_gym.adapters.driven.protocol_opcua._config import (
    OpcuaNodeConfig,
    OpcuaProtocolPortConfig,
)
from grid_gym.adapters.driven.protocol_opcua._errors import (
    OpcuaPortConnectError,
    OpcuaPortDisconnectError,
    OpcuaPortMissingCommandPayloadError,
    OpcuaPortReadAccessMismatchError,
    OpcuaPortReadFailedError,
    OpcuaPortReadNotStartedError,
    OpcuaPortWriteAccessMismatchError,
    OpcuaPortWriteFailedError,
    OpcuaPortWriteNotStartedError,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPortUnknownTargetError,
)


class _AsyncClient(Protocol):
    """Strukturelles Protocol fuer den asyncua-Client.

    Erlaubt Tests, einen `AsyncMock` ohne Inheritance-Klimmzuege durch-
    zureichen, und entkoppelt den Adapter von der konkreten
    `asyncua.Client`-Konstruktor-Signatur.
    """

    async def connect(self) -> None: ...

    async def disconnect(self) -> None: ...

    def get_node(self, nodeid: str) -> object: ...


ClientFactory = Callable[[OpcuaProtocolPortConfig], _AsyncClient]


def _default_client_factory(config: OpcuaProtocolPortConfig) -> _AsyncClient:
    """Default-Client-Factory: `asyncua.Client(url=endpoint_url, timeout=timeout_s)`.

    Trennt das Konstruktor-Detail vom Adapter-Pfad, damit Tests den
    Client mocken koennen, ohne die Welle-4-Default-Wahl zu
    duplizieren.
    """
    client = Client(url=config.endpoint_url, timeout=config.timeout_s)
    return cast("_AsyncClient", client)


class OpcuaDeviceProtocolPort:
    """OPC-UA-Adapter (Simulations-/Testadapter; keine produktive
    Anlagensteuerung).

    Implementiert `DeviceProtocolPort` (ADR 0030 §2.1). asyncua ist
    rein-async, daher haelt der Adapter einen eigenen
    `OpcuaLoopThread` (Decision O-b, ADR 0033 §2.2) und marshalt
    Calls in den Loop-Thread via `run_coroutine_threadsafe`.

    Lifecycle ist idempotent: Doppel-`start()` ist No-op nach erstem
    erfolgreichem Connect; `stop()` nach erfolglosem `start()` ist
    No-op.
    """

    def __init__(
        self,
        config: OpcuaProtocolPortConfig,
        *,
        client_factory: ClientFactory | None = None,
        loop_thread: OpcuaLoopThread | None = None,
    ) -> None:
        self._config: OpcuaProtocolPortConfig = config
        self._client_factory: ClientFactory = client_factory or _default_client_factory
        self._loop_thread: OpcuaLoopThread = loop_thread or OpcuaLoopThread()
        self._client: _AsyncClient | None = None
        self._started: bool = False

    # ------------------------------------------------------------------
    # `DeviceProtocolPort`-Surface (ADR 0030 §2.1)
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Spawnt den Loop-Thread, baut asyncua-Client auf und
        connectet. Idempotent."""
        if self._started:
            return
        self._loop_thread.start()
        client = self._client_factory(self._config)
        try:
            self._loop_thread.run_coroutine(client.connect(), timeout_s=self._config.timeout_s)
        except (OSError, TimeoutError, uaerrors.UaError, OpcuaLoopThreadError) as exc:
            # Loop-Thread sauber abbauen, dann Original-Exception
            # als typed Connect-Fehler propagieren.
            self._loop_thread.stop()
            raise OpcuaPortConnectError(self._config.endpoint_url, str(exc)) from exc
        self._client = client
        self._started = True

    def stop(self) -> None:
        """Disconnectet und baut den Loop-Thread ab. Idempotent."""
        if not self._started or self._client is None:
            return
        client = self._client
        self._client = None
        self._started = False
        try:
            self._loop_thread.run_coroutine(client.disconnect(), timeout_s=self._config.timeout_s)
        except (OSError, TimeoutError, uaerrors.UaError, OpcuaLoopThreadError) as exc:
            # Loop-Thread trotzdem abbauen, dann typed Stop-Fehler
            # propagieren.
            self._loop_thread.stop()
            raise OpcuaPortDisconnectError(str(exc)) from exc
        self._loop_thread.stop()

    def read(self, target: str) -> TelemetryPoint | None:
        """Liest Node-Value vom Server, dekodiert + verpackt in
        `TelemetryPoint` (Decision O-d Polling-Read).

        Wirft `DeviceProtocolPortUnknownTargetError`, wenn das Target
        nicht im Profil ist. Wirft `OpcuaPortReadAccessMismatchError`,
        wenn das Target als `access="write"` konfiguriert ist.
        """
        node_cfg = self._resolve_node_config(target)
        if node_cfg.access != "read":
            raise OpcuaPortReadAccessMismatchError(target, node_cfg.access)
        client = self._require_client(target, "read")
        try:
            variant = self._loop_thread.run_coroutine(
                _read_node_value(client, node_cfg.node_id),
                timeout_s=self._config.timeout_s,
            )
        except (OSError, TimeoutError, uaerrors.UaError, OpcuaLoopThreadError) as exc:
            raise OpcuaPortReadFailedError(target, node_cfg.node_id, str(exc)) from exc
        try:
            value = decode_variant_to_value(variant, node_cfg.datatype)
        except OpcuaCodecError as exc:
            raise OpcuaPortReadFailedError(target, node_cfg.node_id, str(exc)) from exc
        return _build_telemetry_point(target, node_cfg, value)

    def write(self, target: str, command: Command) -> None:
        """Encodiert `command.payload["value"]` zu `Variant` und
        sendet den Wert an den Server (Decision O-d Direct-Write).

        Wirft `DeviceProtocolPortUnknownTargetError` bei unbekanntem
        Target, `OpcuaPortWriteAccessMismatchError` bei
        `access="read"`-Targets, `OpcuaPortMissingCommandPayloadError`
        wenn `command.payload` keinen `value`-Key hat.
        """
        node_cfg = self._resolve_node_config(target)
        if node_cfg.access != "write":
            raise OpcuaPortWriteAccessMismatchError(target, node_cfg.access)
        client = self._require_client(target, "write")
        if "value" not in command.payload:
            raise OpcuaPortMissingCommandPayloadError(target)
        raw_value = command.payload["value"]
        if not isinstance(raw_value, (bool, int, Decimal, float, str)):
            raise OpcuaPortWriteFailedError(
                target,
                node_cfg.node_id,
                f"command.payload['value'] hat unsupported type {type(raw_value).__name__}",
            )
        try:
            variant = encode_value_to_variant(raw_value, node_cfg.datatype)
        except (OpcuaCodecError, OpcuaCodecPayloadTypeError) as exc:
            raise OpcuaPortWriteFailedError(target, node_cfg.node_id, str(exc)) from exc
        try:
            self._loop_thread.run_coroutine(
                _write_node_value(client, node_cfg.node_id, variant),
                timeout_s=self._config.timeout_s,
            )
        except (OSError, TimeoutError, uaerrors.UaError, OpcuaLoopThreadError) as exc:
            raise OpcuaPortWriteFailedError(target, node_cfg.node_id, str(exc)) from exc

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _resolve_node_config(self, target: str) -> OpcuaNodeConfig:
        if target not in self._config.nodes:
            raise DeviceProtocolPortUnknownTargetError(
                target,
                available_targets=tuple(sorted(self._config.nodes.keys())),
            )
        return self._config.nodes[target]

    def _require_client(self, target: str, operation: str) -> _AsyncClient:
        if self._client is None:
            if operation == "write":
                raise OpcuaPortWriteNotStartedError(target)
            raise OpcuaPortReadNotStartedError(target)
        return self._client


async def _read_node_value(client: _AsyncClient, node_id: str) -> ua.Variant:
    """Koroutine: holt die Node-Referenz und liest den Variant-Wert."""
    node = client.get_node(node_id)
    raw_value = await node.read_value()  # type: ignore[attr-defined]
    # asyncua liefert den Python-Native-Wert direkt; wir wrappen in
    # einen Variant, um den Decode-Pfad symmetrisch zum Encode-Pfad
    # zu halten. Der VariantType bleibt unspezifiziert (Adapter
    # weiss den erwarteten Typ aus der Config, nicht aus dem Variant).
    if isinstance(raw_value, ua.Variant):
        return raw_value
    return ua.Variant(raw_value)


async def _write_node_value(client: _AsyncClient, node_id: str, variant: ua.Variant) -> None:
    """Koroutine: holt die Node-Referenz und schreibt den Variant."""
    node = client.get_node(node_id)
    await node.write_value(variant)  # type: ignore[attr-defined]


def _build_telemetry_point(
    target: str, node_cfg: OpcuaNodeConfig, value: bool | int | Decimal | str
) -> TelemetryPoint:
    """Verpackt einen dekodierten Node-Wert in einen `TelemetryPoint`.

    Pattern analog Welle-3 `protocol_modbus._port._build_telemetry_point`:
    `run_id`/`tick`/`simulation_time`/`sequence` sind Caller-
    Verantwortung; der Adapter weiss nichts ueber Simulationszeit.
    """
    return TelemetryPoint(
        run_id="",
        tick=0,
        simulation_time=0,
        device_id=target,
        metric=node_cfg.datatype.value,
        value=_to_decimal(value),
        unit="",
        quality=Quality.VALID,
        source=f"protocol_opcua.{target}",
        sequence=0,
    )


def _to_decimal(value: bool | int | Decimal | str) -> Decimal:
    """`TelemetryPoint.value` ist `Decimal`. Bool/int -> Decimal,
    Decimal bleibt, String -> Decimal via repr (Praezisions-
    Konsistenz mit ADR 0032 §2.2)."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return Decimal(int(value))
    if isinstance(value, int):
        return Decimal(value)
    # String — TelemetryPoint.value erwartet numerisch; Welle-6
    # koennte ein nicht-numerisches Telemetry-Schema einfuehren.
    # Welle 4 setzt `Decimal(0)` als Platzhalter und legt den
    # Original-String in `source`-Feld ab.
    return Decimal(0)
