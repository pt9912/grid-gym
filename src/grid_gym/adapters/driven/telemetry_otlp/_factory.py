"""Welle-6-OTLP-Adapter-Factory + Lifecycle-Helper (ADR 0024 §4.5.7).

`build_otlp_adapters(config)` baut das Welle-6-Adapter-Trio plus die
drei OTel-SDK-Provider und reicht sie zusammen mit dem
`flush_and_shutdown()`-Helper als `OtlpAdapterBundle` zurueck.

Verdrahtungsdetails:

- **Resource**: `service.name` und (optional) `service.instance.id`
  aus `OtlpAdapterConfig` werden in eine OTel-`Resource` gebuendelt;
  die Provider teilen sich dieselbe Resource.
- **Exporter**: drei `OTLPx*Exporter`-Instanzen ueber gRPC (`endpoint`,
  `headers`, `timeout` aus `OtlpAdapterConfig`).
- **Processor / Reader**:
  - Traces: `BatchSpanProcessor(exporter, max_export_batch_size=...)`.
  - Logs: `BatchLogRecordProcessor(exporter, max_export_batch_size=...)`.
  - Metrics: `PeriodicExportingMetricReader(exporter)`.
- **Flush+Shutdown-Reihenfolge** (ADR 0024 §4.5.7 Punkt 4):
  zuerst alle drei Provider `force_flush()` (in fester Reihenfolge
  Tracer → Logger → Meter), danach alle drei `shutdown()`. Damit
  ist garantiert, dass ein Provider nicht waehrend des Flushes
  geschlossen wird (was die SDK als unsicher dokumentiert).

C2-/C3-Lieferungen (Welle 6) konsumieren die `flush_and_shutdown()`-
Surface im Compose-Smoke-Test (siehe ADR 0024 §4.5.7).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# `OTLPLogExporter` liegt in OTel-SDK 1.42 unter dem `_log_exporter`-
# Modul (Underscore-Prefix; documented stable, nicht im public-Re-Export
# des Pakets — daher der explizite `_log_exporter`-Pfad).
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

from grid_gym.adapters.driven.telemetry_otlp._config import _MS_PER_S, OtlpAdapterConfig
from grid_gym.adapters.driven.telemetry_otlp.logs import OtlpLogAdapter
from grid_gym.adapters.driven.telemetry_otlp.metrics import OtlpMetricsAdapter
from grid_gym.adapters.driven.telemetry_otlp.traces import OtlpTraceAdapter

__all__ = [
    "OtlpAdapterBundle",
    "build_otlp_adapters",
]

# Default-Flush-Timeout (Millisekunden). 5000ms matched die in ADR
# 0024 §4.5.7 dokumentierte Smoke-Wartezeit; produktive Stack-
# Shutdown-Pfade duerfen groesseren Wert per Kwarg uebergeben.
_DEFAULT_FLUSH_TIMEOUT_MS: Final[int] = 5000

# `_MS_PER_S` wird aus `_config` importiert (Review-Folge L-4: einzige
# Quelle der Wahrheit fuer ms↔s-Konversion in diesem Adapter-Modul).
# OTel-SDK-Konvention: `OTLPx*Exporter`-`timeout`-Parameter ist in
# **Sekunden**; `force_flush(timeout_millis=)` ist in Millisekunden.


@dataclass(frozen=True, slots=True)
class OtlpAdapterBundle:
    """Welle-6-Adapter-Trio + OTel-Provider-Handles + Lifecycle-Helper.

    Erzeugt von `build_otlp_adapters(config)`. Aufrufer benutzt die
    drei `*_adapter`-Felder als `LogPort`/`MetricsPort`/`TracePort`-
    Implementierungen und ruft `flush_and_shutdown()` am Ende des
    Lebenszyklus (Compose-Smoke-Pflicht in ADR 0024 §4.5.7 Punkt 4).

    Die `*_provider`-Felder sind Public — Tests und produktive
    Aufrufer koennen sie fuer Diagnostik oder zusaetzliche
    Processor-Anbindung greifen. Die Adapter halten interne
    Referenzen auf die Provider; ein Provider-Shutdown ueber
    `flush_and_shutdown()` macht die zugehoerigen Adapter danach
    nicht mehr fuer neue Telemetrie nutzbar (das ist gewollt).
    """

    log_adapter: OtlpLogAdapter
    metrics_adapter: OtlpMetricsAdapter
    trace_adapter: OtlpTraceAdapter
    tracer_provider: TracerProvider
    meter_provider: MeterProvider
    logger_provider: LoggerProvider

    def flush_and_shutdown(self, *, timeout_millis: int = _DEFAULT_FLUSH_TIMEOUT_MS) -> None:
        """Erzwingt Flush + Shutdown aller drei Provider (ADR 0024 §4.5.7 Punkt 4).

        Reihenfolge zwingend: erst Tracer/Logger/Meter `force_flush()`,
        danach alle drei `shutdown()`. Das schuetzt vor flush-waehrend-
        shutdown (laut OTel-SDK-Doku unsicher).
        """
        # Phase 1 — alle Provider synchron flushen.
        self.tracer_provider.force_flush(timeout_millis=timeout_millis)
        self.logger_provider.force_flush(timeout_millis=timeout_millis)
        self.meter_provider.force_flush(timeout_millis=timeout_millis)
        # Phase 2 — alle Provider shut-downen.
        self.tracer_provider.shutdown()
        self.logger_provider.shutdown()
        self.meter_provider.shutdown()


def build_otlp_adapters(config: OtlpAdapterConfig) -> OtlpAdapterBundle:
    """Baut das Welle-6-OTLP-Adapter-Trio aus einer Konfiguration.

    Konstruiert in fester Reihenfolge:

    1. `Resource` aus `service_name` (+ optional `service_instance_id`).
    2. Drei `OTLPx*Exporter`-Instanzen (gRPC, Endpoint + Headers +
       Timeout aus der Config).
    3. Drei Provider (Tracer/Meter/Logger), je mit dem passenden
       Processor/Reader und der gemeinsamen Resource.
    4. Drei Adapter, die ihre jeweiligen Provider als Konstruktor-
       Parameter bekommen.
    5. `OtlpAdapterBundle` als Container fuer das Trio + die Provider
       + `flush_and_shutdown`-Lifecycle-Helper.

    Headers werden als `tuple[tuple[str, str], ...]` an die OTel-API
    weitergereicht (OTel-Konvention; akzeptiert auch `dict`, aber
    Tuples sind hashable + zeigen Reihenfolge stabil).

    Resource-Aufbau (Review-Folge M-6): `Resource.create({})` zieht
    `OTEL_RESOURCE_ATTRIBUTES` per OTel-SDK-Default automatisch (incl.
    `service.name`, `deployment.environment`, custom Attribute, etc.).
    Konfig-Werte (`service_name`, `service_instance_id`) werden als
    Override **on top** gemerged — explizite Konfig schlaegt Env-Var.
    """
    explicit_attrs: dict[str, str] = {"service.name": config.service_name}
    if config.service_instance_id is not None:
        explicit_attrs["service.instance.id"] = config.service_instance_id
    # `Resource.create({})` mit leerem Dict laesst die SDK-Default-
    # Detection laufen (zieht OTEL_RESOURCE_ATTRIBUTES + SDK-Standard-
    # Felder wie `service.name`-Fallback aus `OTEL_SERVICE_NAME`).
    # `merge` ueberschreibt Env-Werte mit den expliziten Konfig-Werten.
    resource = Resource.create({}).merge(Resource.create(explicit_attrs))

    headers_tuple = tuple(config.headers.items())

    trace_exporter = OTLPSpanExporter(
        endpoint=config.endpoint,
        headers=headers_tuple,
        timeout=int(config.timeout_s),
    )
    log_exporter = OTLPLogExporter(
        endpoint=config.endpoint,
        headers=headers_tuple,
        timeout=int(config.timeout_s),
    )
    metric_exporter = OTLPMetricExporter(
        endpoint=config.endpoint,
        headers=headers_tuple,
        timeout=int(config.timeout_s),
    )

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            trace_exporter,
            max_export_batch_size=config.batch_max_export_size,
        ),
    )

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            log_exporter,
            max_export_batch_size=config.batch_max_export_size,
        ),
    )

    metric_reader = PeriodicExportingMetricReader(
        metric_exporter,
        export_timeout_millis=int(config.timeout_s * _MS_PER_S),
    )
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
    )

    trace_adapter = OtlpTraceAdapter(tracer_provider)
    metrics_adapter = OtlpMetricsAdapter(meter_provider)
    log_adapter = OtlpLogAdapter(logger_provider)

    return OtlpAdapterBundle(
        log_adapter=log_adapter,
        metrics_adapter=metrics_adapter,
        trace_adapter=trace_adapter,
        tracer_provider=tracer_provider,
        meter_provider=meter_provider,
        logger_provider=logger_provider,
    )
