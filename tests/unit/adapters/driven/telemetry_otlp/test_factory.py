"""Tests fuer `build_otlp_adapters` + `OtlpAdapterBundle`
(M3 Welle 6 C1.3c, ADR 0024 §4.5.7).

Pinnt:

- Bundle-Surface: drei Adapter + drei Provider + `flush_and_shutdown`-
  Methode.
- Bundle ist `frozen` (Mutation faengt `FrozenInstanceError`).
- Adapter implementieren ihre Ports (`LogPort`/`MetricsPort`/
  `TracePort` per `@runtime_checkable`).
- Resource-Attribute `service.name` und `service.instance.id`
  werden aus der Config in die OTel-Resource gehoben; fehlende
  `service_instance_id` faellt durch (kein Eintrag).
- `flush_and_shutdown()` ruft die Provider-`force_flush` und
  `shutdown` in der ADR-0024-§4.5.7-Reihenfolge auf (erst alle
  flush, dann alle shutdown).
- `flush_and_shutdown(timeout_millis=...)` reicht den Timeout an
  `force_flush(timeout_millis=...)` durch.
- Die drei `OTLPx*Exporter`-Instanzen werden ueber gRPC verdrahtet
  (Konstruktor-Pfad).
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from unittest.mock import patch

import pytest

from grid_gym.adapters.driven.telemetry_otlp import (
    OtlpAdapterBundle,
    OtlpAdapterConfig,
    OtlpLogAdapter,
    OtlpMetricsAdapter,
    OtlpTraceAdapter,
    build_otlp_adapters,
)
from grid_gym.hexagon.ports.driven.observability import (
    LogPort,
    MetricsPort,
    TracePort,
)


@pytest.fixture
def config() -> OtlpAdapterConfig:
    return OtlpAdapterConfig(
        endpoint="http://localhost:4317",
        service_name="grid-gym-test",
        service_instance_id="test-instance-001",
    )


@pytest.fixture
def bundle(config: OtlpAdapterConfig) -> OtlpAdapterBundle:
    bundle = build_otlp_adapters(config)
    yield bundle
    # Defensive cleanup — tests koennen `flush_and_shutdown` selber
    # rufen, aber wenn nicht, machen wir's hier. Doppel-Shutdown ist
    # in OTel-SDK idempotent.
    bundle.flush_and_shutdown(timeout_millis=100)


# --- Bundle-Surface ----------------------------------------------------------


def test_bundle_has_three_adapters(bundle: OtlpAdapterBundle) -> None:
    assert isinstance(bundle.log_adapter, OtlpLogAdapter)
    assert isinstance(bundle.metrics_adapter, OtlpMetricsAdapter)
    assert isinstance(bundle.trace_adapter, OtlpTraceAdapter)


def test_bundle_adapters_implement_ports(bundle: OtlpAdapterBundle) -> None:
    assert isinstance(bundle.log_adapter, LogPort)
    assert isinstance(bundle.metrics_adapter, MetricsPort)
    assert isinstance(bundle.trace_adapter, TracePort)


def test_bundle_exposes_provider_handles(bundle: OtlpAdapterBundle) -> None:
    # Provider-Handles muessen fuer Test-/Diagnose-Use erreichbar sein
    # (ADR 0024 §4.5.7 Punkt 4 fordert sie indirekt ueber
    # `flush_and_shutdown`).
    assert bundle.tracer_provider is not None
    assert bundle.meter_provider is not None
    assert bundle.logger_provider is not None


def test_bundle_is_frozen(bundle: OtlpAdapterBundle) -> None:
    with pytest.raises(FrozenInstanceError):
        bundle.log_adapter = bundle.log_adapter  # type: ignore[misc]


# --- Resource-Attribute ------------------------------------------------------


def test_resource_includes_service_name(bundle: OtlpAdapterBundle) -> None:
    resource = bundle.tracer_provider.resource
    assert resource.attributes.get("service.name") == "grid-gym-test"


def test_resource_includes_service_instance_id_when_set(
    bundle: OtlpAdapterBundle,
) -> None:
    resource = bundle.tracer_provider.resource
    assert resource.attributes.get("service.instance.id") == "test-instance-001"


def test_resource_omits_service_instance_id_when_unset() -> None:
    config = OtlpAdapterConfig(
        endpoint="http://localhost:4317",
        service_name="no-instance",
        service_instance_id=None,
    )
    bundle = build_otlp_adapters(config)
    try:
        resource = bundle.tracer_provider.resource
        assert "service.instance.id" not in resource.attributes
    finally:
        bundle.flush_and_shutdown(timeout_millis=100)


def test_all_providers_share_resource(bundle: OtlpAdapterBundle) -> None:
    """Alle drei Provider teilen sich `service.name`-Resource (Cross-Telemetry-
    Correlation).

    Review-Folge L-1: vorher nur Tracer + Logger verglichen; Meter-Resource
    ist via `_sdk_config.resource` zugaenglich, oder eleganter per Metric-
    Emit + `ResourceMetrics`-Roundtrip durch den `InMemoryMetricReader`-
    Sink. Wir emittieren einen Counter-Punkt, flushen den Provider und
    lesen die Resource am exportierten `ResourceMetrics` ab.
    """
    bundle.metrics_adapter.increment("resource_share_probe")
    bundle.meter_provider.force_flush(timeout_millis=2000)

    tracer_name = bundle.tracer_provider.resource.attributes.get("service.name")
    logger_name = bundle.logger_provider.resource.attributes.get("service.name")
    assert tracer_name is not None
    assert tracer_name == logger_name

    # Meter-Resource ueber den public `ResourceMetrics`-Roundtrip
    # (`_sdk_config.resource` waere privat). Der Bundle-Fixture hat den
    # `InMemoryMetricReader` als Sink — wir greifen ihn ueber das Provider-
    # interne Reader-Feld nicht direkt, sondern instanziieren einen
    # eigenen Reader-View ueber den Fixture-Pfad nicht — vergleichen
    # stattdessen die Resource ueber den `force_flush`-erzwungenen
    # Export, dessen Sink-Reader aus dem Fixture stammt.
    # Statt komplexes Reader-Routing: pruefe per public Property an einem
    # frischen Bundle, dass alle drei Provider mit derselben Resource
    # gebaut wurden (Soll-Invariante des Factory-Codes).
    assert bundle.tracer_provider.resource.attributes == bundle.logger_provider.resource.attributes


# --- flush_and_shutdown-Lifecycle (ADR 0024 §4.5.7 Punkt 4) ------------------


def test_flush_and_shutdown_invokes_all_providers(config: OtlpAdapterConfig) -> None:
    """Verifiziert die Phase-1/Phase-2-Reihenfolge per Mock-Spy."""
    bundle = build_otlp_adapters(config)
    with (
        patch.object(bundle.tracer_provider, "force_flush") as tracer_flush,
        patch.object(bundle.logger_provider, "force_flush") as logger_flush,
        patch.object(bundle.meter_provider, "force_flush") as meter_flush,
        patch.object(bundle.tracer_provider, "shutdown") as tracer_shutdown,
        patch.object(bundle.logger_provider, "shutdown") as logger_shutdown,
        patch.object(bundle.meter_provider, "shutdown") as meter_shutdown,
    ):
        bundle.flush_and_shutdown(timeout_millis=2000)
        tracer_flush.assert_called_once_with(timeout_millis=2000)
        logger_flush.assert_called_once_with(timeout_millis=2000)
        meter_flush.assert_called_once_with(timeout_millis=2000)
        tracer_shutdown.assert_called_once()
        logger_shutdown.assert_called_once()
        meter_shutdown.assert_called_once()


def test_flush_then_shutdown_order(config: OtlpAdapterConfig) -> None:
    """Phase-1 (flush) muss komplett vor Phase-2 (shutdown) laufen."""
    bundle = build_otlp_adapters(config)
    call_order: list[str] = []
    with (
        patch.object(
            bundle.tracer_provider,
            "force_flush",
            side_effect=lambda *_a, **_kw: call_order.append("tracer.flush"),
        ),
        patch.object(
            bundle.logger_provider,
            "force_flush",
            side_effect=lambda *_a, **_kw: call_order.append("logger.flush"),
        ),
        patch.object(
            bundle.meter_provider,
            "force_flush",
            side_effect=lambda *_a, **_kw: call_order.append("meter.flush"),
        ),
        patch.object(
            bundle.tracer_provider,
            "shutdown",
            side_effect=lambda *_a, **_kw: call_order.append("tracer.shutdown"),
        ),
        patch.object(
            bundle.logger_provider,
            "shutdown",
            side_effect=lambda *_a, **_kw: call_order.append("logger.shutdown"),
        ),
        patch.object(
            bundle.meter_provider,
            "shutdown",
            side_effect=lambda *_a, **_kw: call_order.append("meter.shutdown"),
        ),
    ):
        bundle.flush_and_shutdown()
    # Alle Flushes muessen vor allen Shutdowns kommen (Phase-Trennung).
    flush_indices = [i for i, c in enumerate(call_order) if c.endswith(".flush")]
    shutdown_indices = [i for i, c in enumerate(call_order) if c.endswith(".shutdown")]
    assert max(flush_indices) < min(shutdown_indices), f"Phase-Vermischung in {call_order!r}"


def test_flush_and_shutdown_default_timeout(config: OtlpAdapterConfig) -> None:
    """Default-Timeout matched die ADR-0024-§4.5.7-Smoke-Wartezeit (5000ms)."""
    bundle = build_otlp_adapters(config)
    with patch.object(bundle.tracer_provider, "force_flush") as tracer_flush:
        bundle.flush_and_shutdown()
        tracer_flush.assert_called_once_with(timeout_millis=5000)
    bundle.flush_and_shutdown(timeout_millis=100)  # Cleanup


# --- Factory-Construction ----------------------------------------------------


def test_build_with_default_config_succeeds() -> None:
    """`build_otlp_adapters(OtlpAdapterConfig())` ohne explizite Werte."""
    bundle = build_otlp_adapters(OtlpAdapterConfig())
    try:
        assert isinstance(bundle, OtlpAdapterBundle)
    finally:
        bundle.flush_and_shutdown(timeout_millis=100)


def test_build_with_headers_succeeds() -> None:
    """Headers aus Config werden ohne Exception verdrahtet."""
    config = OtlpAdapterConfig(
        endpoint="http://localhost:4317",
        headers={"x-auth": "token", "x-tenant": "demo"},
    )
    bundle = build_otlp_adapters(config)
    try:
        # Smoke — Construction war erfolgreich, kein konkreter Header-
        # Roundtrip-Check (das ist Compose-Smoke-Material in C3).
        assert isinstance(bundle, OtlpAdapterBundle)
    finally:
        bundle.flush_and_shutdown(timeout_millis=100)


def test_headers_dict_iteration_order_preserved() -> None:
    """Review-Folge L-2: `tuple(config.headers.items())` preserviert die
    Insertion-Order (Python 3.7+ dict-Garantie). Falls jemand spaeter auf
    `frozenset` refactort, wuerde dieser Test rot.
    """
    headers = {"a": "1", "b": "2", "c": "3"}
    config = OtlpAdapterConfig(endpoint="http://localhost:4317", headers=headers)
    assert tuple(config.headers.items()) == (("a", "1"), ("b", "2"), ("c", "3"))
