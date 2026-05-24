"""Tests fuer `OtlpLogAdapter` (M3 Welle 6 C1.3b, ADR 0024 §2.2).

Pinnt:

- Protocol-Conformance (`isinstance(adapter, LogPort)`).
- Level-Mapping (String → `SeverityNumber`); unbekannte Levels
  fallen auf `INFO`.
- Pflicht-Felder aus `GG-OTEL-002` werden als Attributes uebernommen:
  `run_id`, `module`, `event_id`. `None`-Werte werden nicht
  eingetragen.
- `attributes`-Mapping ueberschreibt Pflicht-Felder (`GG-OTEL-002`
  flexible Extension-Surface).
- `body` matched `message`.
- `severity_text` matched `level.upper()`.
- **Kein `time.*`-Import im Adapter-Modul** (ADR 0024 §4.5.5 D-4).

Tests verwenden `InMemoryLogExporter` als In-Process-Sink (kein
Live-Collector noetig).
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from opentelemetry._logs import SeverityNumber
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import (
    InMemoryLogExporter,
    SimpleLogRecordProcessor,
)

from grid_gym.adapters.driven.telemetry_otlp import OtlpLogAdapter
from grid_gym.hexagon.ports.driven.observability import LogPort


@pytest.fixture
def log_exporter() -> InMemoryLogExporter:
    return InMemoryLogExporter()


@pytest.fixture
def adapter(log_exporter: InMemoryLogExporter) -> Iterator[OtlpLogAdapter]:
    provider = LoggerProvider()
    provider.add_log_record_processor(SimpleLogRecordProcessor(log_exporter))
    yield OtlpLogAdapter(provider, instrumentation_name="grid-gym-test")
    provider.shutdown()


# --- Protocol-Conformance ----------------------------------------------------


def test_adapter_implements_log_port(adapter: OtlpLogAdapter) -> None:
    assert isinstance(adapter, LogPort)


# --- Basic emission ----------------------------------------------------------


def test_log_emits_record(
    adapter: OtlpLogAdapter,
    log_exporter: InMemoryLogExporter,
) -> None:
    adapter.log("info", "tick_begin")
    records = log_exporter.get_finished_logs()
    assert len(records) == 1
    assert records[0].log_record.body == "tick_begin"


def test_log_severity_text_uppercases_level(
    adapter: OtlpLogAdapter,
    log_exporter: InMemoryLogExporter,
) -> None:
    adapter.log("warn", "low-fuel")
    records = log_exporter.get_finished_logs()
    assert records[0].log_record.severity_text == "WARN"


# --- Level-Mapping -----------------------------------------------------------


@pytest.mark.parametrize(
    ("level", "expected_severity"),
    [
        ("trace", SeverityNumber.TRACE),
        ("debug", SeverityNumber.DEBUG),
        ("info", SeverityNumber.INFO),
        ("warn", SeverityNumber.WARN),
        ("warning", SeverityNumber.WARN),
        ("error", SeverityNumber.ERROR),
        ("critical", SeverityNumber.FATAL),
        ("fatal", SeverityNumber.FATAL),
    ],
)
def test_known_levels_map_to_severity(
    adapter: OtlpLogAdapter,
    log_exporter: InMemoryLogExporter,
    level: str,
    expected_severity: SeverityNumber,
) -> None:
    adapter.log(level, "msg")
    records = log_exporter.get_finished_logs()
    assert records[0].log_record.severity_number == expected_severity


def test_unknown_level_defaults_to_info(
    adapter: OtlpLogAdapter,
    log_exporter: InMemoryLogExporter,
) -> None:
    adapter.log("audit", "msg")
    records = log_exporter.get_finished_logs()
    assert records[0].log_record.severity_number == SeverityNumber.INFO


def test_case_insensitive_level_match(
    adapter: OtlpLogAdapter,
    log_exporter: InMemoryLogExporter,
) -> None:
    adapter.log("INFO", "upper-case")
    records = log_exporter.get_finished_logs()
    assert records[0].log_record.severity_number == SeverityNumber.INFO


# --- Attributes-Propagation (`GG-OTEL-002`) ---------------------------------


def test_log_includes_mandatory_fields_as_attributes(
    adapter: OtlpLogAdapter,
    log_exporter: InMemoryLogExporter,
) -> None:
    adapter.log(
        "info",
        "tick_begin",
        run_id="run-42",
        module="tick_loop",
        event_id="evt-001",
    )
    record_attrs = dict(log_exporter.get_finished_logs()[0].log_record.attributes or {})
    assert record_attrs.get("run_id") == "run-42"
    assert record_attrs.get("module") == "tick_loop"
    assert record_attrs.get("event_id") == "evt-001"


def test_log_omits_unset_mandatory_fields(
    adapter: OtlpLogAdapter,
    log_exporter: InMemoryLogExporter,
) -> None:
    adapter.log("info", "minimal")
    record_attrs = dict(log_exporter.get_finished_logs()[0].log_record.attributes or {})
    assert "run_id" not in record_attrs
    assert "module" not in record_attrs
    assert "event_id" not in record_attrs


def test_log_attributes_extension_merged(
    adapter: OtlpLogAdapter,
    log_exporter: InMemoryLogExporter,
) -> None:
    adapter.log(
        "info",
        "with-extras",
        run_id="run-1",
        attributes={"custom_field": "value", "feature": "welle-6"},
    )
    record_attrs = dict(log_exporter.get_finished_logs()[0].log_record.attributes or {})
    assert record_attrs.get("run_id") == "run-1"
    assert record_attrs.get("custom_field") == "value"
    assert record_attrs.get("feature") == "welle-6"


def test_log_extras_override_mandatory_fields(
    adapter: OtlpLogAdapter,
    log_exporter: InMemoryLogExporter,
) -> None:
    """`GG-OTEL-002`-Pflichtfelder sind ueberschreibbar durch explizite `attributes`.

    Das matched die nachgiebige Extension-Surface — Aufrufer kann via
    `attributes={"run_id": "...special..."}` einen abweichenden Wert
    eintragen.
    """
    adapter.log(
        "info",
        "override-test",
        run_id="original",
        attributes={"run_id": "overridden"},
    )
    record_attrs = dict(log_exporter.get_finished_logs()[0].log_record.attributes or {})
    assert record_attrs.get("run_id") == "overridden"


# --- Modul-Importe (ADR 0024 §4.5.5 D-4) -------------------------------------


def test_module_does_not_import_time() -> None:
    """`logs`-Modul darf kein `time.*` importieren (ADR 0024 §4.5.5)."""
    import grid_gym.adapters.driven.telemetry_otlp.logs as logs_mod

    source = logs_mod.__file__
    assert source is not None
    with open(source, encoding="utf-8") as fh:
        text = fh.read()
    assert "import time" not in text
    assert "from time" not in text
    assert "from datetime" not in text
    assert "perf_counter" not in text
    assert "monotonic" not in text
