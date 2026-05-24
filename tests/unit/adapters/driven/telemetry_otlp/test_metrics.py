"""Tests fuer `OtlpMetricsAdapter` (M3 Welle 6 C1.3b, ADR 0024 §2.3 + §4.5.2).

Pinnt:

- Protocol-Conformance (`isinstance(adapter, MetricsPort)`).
- `increment(name, value)` mappt auf OTel-`Counter.add(...)`;
  Folge-Aufrufe akkumulieren sauber.
- `gauge(name, value)` mappt auf OTel-`Gauge.set(...)`; letzter Wert
  wird exportiert.
- `observe(name, value)` mappt auf OTel-`Histogram.record(...)`.
- Instrument-Caching: zweimal `increment("x")` benutzt dasselbe
  OTel-`Counter`-Instrument (kein zweites `create_counter`).
- Attributes-Propagation.

Tests verwenden `InMemoryMetricReader` als In-Process-Sink (kein
Live-Collector noetig). Die `time.*`/`datetime`-Freiheit des
Adapter-Moduls (ADR 0024 §4.5.5 D-4) wird zentral vom
`AC-OTLP-ADAPTER-NO-TIME`-Contract in `tools/arch_check.py`
geprueft.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from grid_gym.adapters.driven.telemetry_otlp import (
    OtlpMetricsAdapter,
    OtlpMetricsNameCollisionError,
)
from grid_gym.hexagon.ports.driven.observability import MetricsPort


@pytest.fixture
def metric_reader() -> InMemoryMetricReader:
    return InMemoryMetricReader()


@pytest.fixture
def adapter(metric_reader: InMemoryMetricReader) -> Iterator[OtlpMetricsAdapter]:
    provider = MeterProvider(metric_readers=[metric_reader])
    yield OtlpMetricsAdapter(provider, instrumentation_name="grid-gym-test")
    provider.shutdown()


def _collect_metric_data(reader: InMemoryMetricReader) -> dict[str, object]:
    """Sammelt alle Metric-Records nach Name auf, fuer einfache Asserts."""
    data = reader.get_metrics_data()
    by_name: dict[str, object] = {}
    if data is None:
        return by_name
    for resource_metric in data.resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                by_name[metric.name] = metric
    return by_name


# --- Protocol-Conformance ----------------------------------------------------


def test_adapter_implements_metrics_port(adapter: OtlpMetricsAdapter) -> None:
    assert isinstance(adapter, MetricsPort)


# --- increment (Counter) -----------------------------------------------------


def test_increment_default_value(
    adapter: OtlpMetricsAdapter,
    metric_reader: InMemoryMetricReader,
) -> None:
    adapter.increment("tick_count")
    metrics = _collect_metric_data(metric_reader)
    assert "tick_count" in metrics


def test_increment_accumulates(
    adapter: OtlpMetricsAdapter,
    metric_reader: InMemoryMetricReader,
) -> None:
    adapter.increment("evt_count", 1)
    adapter.increment("evt_count", 2)
    adapter.increment("evt_count", 5)
    metrics = _collect_metric_data(metric_reader)
    counter = metrics["evt_count"]
    # OTel-Counter-Metric has `data.data_points` mit kumulativem `value`.
    points = list(counter.data.data_points)  # type: ignore[attr-defined]
    assert len(points) == 1
    assert points[0].value == 8


def test_increment_with_attributes_propagates(
    adapter: OtlpMetricsAdapter,
    metric_reader: InMemoryMetricReader,
) -> None:
    adapter.increment("labelled", 3, attributes={"phase": "init"})
    metrics = _collect_metric_data(metric_reader)
    counter = metrics["labelled"]
    points = list(counter.data.data_points)  # type: ignore[attr-defined]
    assert len(points) == 1
    assert dict(points[0].attributes) == {"phase": "init"}


# --- gauge -------------------------------------------------------------------


def test_gauge_sets_value(
    adapter: OtlpMetricsAdapter,
    metric_reader: InMemoryMetricReader,
) -> None:
    adapter.gauge("event_queue_len", 7.0)
    metrics = _collect_metric_data(metric_reader)
    assert "event_queue_len" in metrics


def test_gauge_overwrites_previous_value(
    adapter: OtlpMetricsAdapter,
    metric_reader: InMemoryMetricReader,
) -> None:
    adapter.gauge("queue", 3.0)
    adapter.gauge("queue", 7.0)
    metrics = _collect_metric_data(metric_reader)
    points = list(metrics["queue"].data.data_points)  # type: ignore[attr-defined]
    assert len(points) == 1
    assert points[0].value == pytest.approx(7.0)


# --- observe (Histogram) -----------------------------------------------------


def test_observe_records_distribution(
    adapter: OtlpMetricsAdapter,
    metric_reader: InMemoryMetricReader,
) -> None:
    adapter.observe("latency_ms", 12.5)
    adapter.observe("latency_ms", 25.0)
    adapter.observe("latency_ms", 7.25)
    metrics = _collect_metric_data(metric_reader)
    histogram = metrics["latency_ms"]
    points = list(histogram.data.data_points)  # type: ignore[attr-defined]
    assert len(points) == 1
    assert points[0].count == 3
    assert points[0].sum == pytest.approx(44.75)


# --- Instrument-Caching ------------------------------------------------------


def test_repeated_increment_reuses_counter(adapter: OtlpMetricsAdapter) -> None:
    """Zweimal `increment("x")` darf nicht ein zweites `Counter`-Instrument anlegen."""
    adapter.increment("cached")
    counter_first = adapter._counters["cached"]
    adapter.increment("cached")
    counter_second = adapter._counters["cached"]
    assert counter_first is counter_second


def test_repeated_gauge_reuses_gauge(adapter: OtlpMetricsAdapter) -> None:
    adapter.gauge("g", 1.0)
    first = adapter._gauges["g"]
    adapter.gauge("g", 2.0)
    second = adapter._gauges["g"]
    assert first is second


def test_repeated_observe_reuses_histogram(adapter: OtlpMetricsAdapter) -> None:
    adapter.observe("h", 1.0)
    first = adapter._histograms["h"]
    adapter.observe("h", 2.0)
    second = adapter._histograms["h"]
    assert first is second


# --- Cross-Family-Naming-Collision (Review-Folge M-4) ------------------------


def test_counter_then_gauge_same_name_raises(adapter: OtlpMetricsAdapter) -> None:
    adapter.increment("queue_len")
    with pytest.raises(OtlpMetricsNameCollisionError) as exc_info:
        adapter.gauge("queue_len", 5.0)
    assert "queue_len" in str(exc_info.value)
    assert "counter" in str(exc_info.value)
    assert "gauge" in str(exc_info.value)


def test_counter_then_histogram_same_name_raises(adapter: OtlpMetricsAdapter) -> None:
    adapter.increment("latency")
    with pytest.raises(OtlpMetricsNameCollisionError):
        adapter.observe("latency", 1.5)


def test_gauge_then_counter_same_name_raises(adapter: OtlpMetricsAdapter) -> None:
    adapter.gauge("rate", 3.0)
    with pytest.raises(OtlpMetricsNameCollisionError):
        adapter.increment("rate")


def test_histogram_then_gauge_same_name_raises(adapter: OtlpMetricsAdapter) -> None:
    adapter.observe("dist", 1.0)
    with pytest.raises(OtlpMetricsNameCollisionError):
        adapter.gauge("dist", 0.0)


def test_same_family_same_name_no_collision(adapter: OtlpMetricsAdapter) -> None:
    """Wiederholter Aufruf in derselben Familie ist erlaubt — Cache-Reuse."""
    adapter.increment("ok_counter")
    adapter.increment("ok_counter", 5)  # selbe Familie, kein Collision
    adapter.gauge("ok_gauge", 1.0)
    adapter.gauge("ok_gauge", 2.0)  # selbe Familie, kein Collision


# --- Modul-Importe ----------------------------------------------------------
#
# `time.*`/`datetime`-Freiheit (ADR 0024 §4.5.5 D-4) wird zentral vom
# `AC-OTLP-ADAPTER-NO-TIME`-Contract per AST geprueft, nicht hier per
# Substring-Inspektion (Review-Folge H-2). Siehe `tools/arch_check.py`.
