"""Matrix-Diagnose fuer den OTLP-Span-Export-Edge-Case (Welle 6 C3).

Hintergrund (siehe `docs/plan/planning/open/029-otlp-span-grpc-
export-edge-case.md` + `tests/integration/test_otlp_compose_smoke.
py` Span-Caveat):

Welle-6-C3-Smoke konnte fuer den OTLP-Adapter-Pfad Metric+Log gegen
einen Compose-Sibling-Collector verifizieren, aber keinen Span.
SDK-side ist alles korrekt (ConsoleSpanExporter zeigt valide Spans
mit `recording=True`); der OTLP-gRPC-Span-Export geht aber silent
verloren — `force_flush()` returnt `True`, der Collector empfaengt
nichts. Metrics+Logs ueber die identische gRPC-Verbindung
funktionieren.

Dieses Script ist **laut** (Debug-Logging von opentelemetry+grpc
voll aufgedreht, Collector-Logs am Ende, `GRPC_VERBOSITY=DEBUG`),
faehrt einen frischen Collector-Container per Docker-API hoch und
probiert eine Matrix aus Endpoint-/Insecure-/Processor-Varianten,
um den Bruchpunkt einzugrenzen.

**Kein Pytest-Test.** Direkt aufrufen — z. B. aus dem `test-runner`-
Container oder einem Sibling-Container mit Docker-Socket-Mount:

    docker compose -f tests/integration/compose.yml run --rm test-runner \\
        uv run python tools/diagnose_otlp_span_export.py

Ausgabe ist Matrix-Tabelle (Variante x Signal); Output > 50KB
moeglich.
"""

from __future__ import annotations

import logging
import os
import sys
import time
import urllib.request
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Final

# gRPC + OpenTelemetry-Logger schon vor dem ersten Import auf DEBUG
# stellen, damit die Provider-Setup-Logs sichtbar werden.
os.environ.setdefault("GRPC_VERBOSITY", "DEBUG")
os.environ.setdefault("GRPC_TRACE", "api,client_channel,connectivity_state,call_error")
logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
logging.getLogger("opentelemetry").setLevel(logging.DEBUG)
logging.getLogger("grpc").setLevel(logging.DEBUG)

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from testcontainers.core.container import DockerContainer  # type: ignore[import-untyped]
from testcontainers.core.waiting_utils import wait_for_logs  # type: ignore[import-untyped]

_COLLECTOR_IMAGE_DEFAULT: Final[str] = "otel/opentelemetry-collector-contrib:0.152.1"
_COLLECTOR_IMAGE_ENV: Final[str] = "OTEL_COLLECTOR_IMAGE"
_GRPC_PORT: Final[int] = 4317
_HEALTH_PORT: Final[int] = 13133
_INTERNAL_METRICS_PORT: Final[int] = 8888

# Span-relevante Internal-Counter aus dem Collector. Die nominelle
# Beweisfuehrung „kommt am Receiver an / wird gedroppet / wird
# exportiert" laeuft genau ueber diese drei (plus ihre Equivalente
# fuer Metrics+Logs zum Vergleich). `force_flush=True` allein ist
# laut OTLPSpanExporter-Python-API trivial wahr (der Exporter
# puffert selbst nichts) — siehe Trigger 029 Doku-Befund.
_INTERESTING_COUNTERS: Final[tuple[str, ...]] = (
    "otelcol_receiver_accepted_spans",
    "otelcol_receiver_refused_spans",
    "otelcol_processor_batch_batch_send_size",
    "otelcol_exporter_sent_spans",
    "otelcol_exporter_send_failed_spans",
    "otelcol_receiver_accepted_metric_points",
    "otelcol_receiver_accepted_log_records",
)

_COLLECTOR_CONFIG_YAML: Final[str] = """
extensions:
  health_check:
    endpoint: 0.0.0.0:13133
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
processors:
  batch:
    timeout: 100ms
    send_batch_size: 1
exporters:
  debug:
    verbosity: detailed
service:
  # Internal-Telemetry auf :8888 (Prometheus-Format). Pflicht fuer
  # Trigger-029-Diagnose: die einzige verlaessliche Beweisfuehrung
  # ist `otelcol_receiver_accepted_spans` vs.
  # `otelcol_exporter_sent_spans` — Debug-Exporter-Logs alleine
  # zeigen nicht, ob ein Span am Receiver angenommen wurde.
  telemetry:
    logs:
      level: debug
    metrics:
      readers:
        - pull:
            exporter:
              prometheus:
                host: 0.0.0.0
                port: 8888
  extensions: [health_check]
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug]
    logs:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug]
"""


@dataclass(frozen=True, slots=True)
class _Variant:
    name: str
    endpoint_template: str  # `{host}` und `{port}` werden gefuellt
    insecure: bool | None  # None = nicht setzen
    use_simple_processor: bool


_VARIANTS: Final[tuple[_Variant, ...]] = (
    _Variant("http-batch-no-flag", "http://{host}:{port}", None, False),
    _Variant("http-simple-no-flag", "http://{host}:{port}", None, True),
    _Variant("http-simple-insecure", "http://{host}:{port}", True, True),
    _Variant("hostport-simple-insecure", "{host}:{port}", True, True),
    _Variant("hostport-batch-insecure", "{host}:{port}", True, False),
)


@contextmanager
def _collector_container() -> Iterator[DockerContainer]:
    image = os.environ.get(_COLLECTOR_IMAGE_ENV, _COLLECTOR_IMAGE_DEFAULT)
    container = (
        DockerContainer(image)
        .with_env("OTEL_CONFIG_YAML", _COLLECTOR_CONFIG_YAML)
        .with_command("--config=env:OTEL_CONFIG_YAML")
        .with_exposed_ports(_GRPC_PORT, _HEALTH_PORT, _INTERNAL_METRICS_PORT)
        .with_kwargs(user="0:0")
    )
    container.start()
    try:
        wait_for_logs(
            container,
            "Everything is ready. Begin running and processing data.",
            timeout=30,
        )
        yield container
    finally:
        container.stop()


def _run_variant(variant: _Variant, *, host: str, port: int, instance_id: str) -> None:
    """Sendet einen einzelnen Span gemaess der Variante; Console
    + OTLP parallel, damit SDK-Erzeugung sichtbar bleibt."""
    endpoint = variant.endpoint_template.format(host=host, port=port)
    exporter_kwargs: dict[str, object] = {"endpoint": endpoint}
    if variant.insecure is not None:
        exporter_kwargs["insecure"] = variant.insecure
    otlp_exporter = OTLPSpanExporter(**exporter_kwargs)  # type: ignore[arg-type]
    resource = Resource.create(
        {"service.name": "diagnose-otlp-span", "service.instance.id": instance_id}
    )
    provider = TracerProvider(resource=resource)
    if variant.use_simple_processor:
        provider.add_span_processor(SimpleSpanProcessor(otlp_exporter))
    else:
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    tracer = provider.get_tracer(f"diagnose-{variant.name}")
    with tracer.start_as_current_span(f"diagnose.{variant.name}") as span:
        ctx = span.get_span_context()
        # `trace_flags & 0x01` ist das SAMPLED-Bit (W3C-Trace-Spec).
        # Wenn das Bit 0 ist, wird der Span vom SDK-Sampler abgewiesen
        # und kein OTLP-Export findet statt — eine der ersten
        # Hypothesen des Trigger-029-Doku-Befunds.
        sampled = bool(ctx.trace_flags & 0x01)
        print(
            f"[diagnose] variant={variant.name} endpoint={endpoint} "
            f"insecure={variant.insecure} processor="
            f"{'simple' if variant.use_simple_processor else 'batch'} "
            f"span_id={ctx.span_id:016x} trace_flags={int(ctx.trace_flags):#04x} "
            f"sampled={sampled} recording={span.is_recording()}",
            file=sys.stderr,
        )
    # `force_flush=True` ist laut OTLPSpanExporter-Python-API trivial
    # (der Exporter puffert selbst nichts; siehe Trigger 029 Doku-
    # Befund) — wir loggen es trotzdem, aber die echte Beweisfuehrung
    # erfolgt ueber die Internal-Counter unten.
    flush_ok = provider.force_flush(timeout_millis=5000)
    print(f"[diagnose] variant={variant.name} flush_ok={flush_ok}", file=sys.stderr)
    provider.shutdown()


def _run_factory_variant(*, host: str, port: int, instance_id: str) -> None:
    """6. Variante: voller Produktiv-Pfad ueber `build_otlp_adapters
    (OtlpAdapterConfig(...))` + `bundle.trace_adapter.start_span(...)`
    + `bundle.flush_and_shutdown(...)`. Vergleich gegen die 5
    Standalone-Varianten oben — wenn diese hier 0 Collector-Hits
    liefert, ist der Trigger-029-Bruchpunkt im
    `_factory.py`/`traces.py`/`OtlpAdapterBundle.flush_and_shutdown`-
    Pfad eingegrenzt. Marker: `diagnose.factory.bundle`."""
    from grid_gym.adapters.driven.telemetry_otlp import (
        OtlpAdapterConfig,
        build_otlp_adapters,
    )

    config = OtlpAdapterConfig(
        endpoint=f"http://{host}:{port}",
        service_name="diagnose-otlp-span",
        service_instance_id=instance_id,
    )
    bundle = build_otlp_adapters(config)
    span_ctx = bundle.trace_adapter.start_span("diagnose.factory.bundle")
    print(
        f"[diagnose] variant=factory-bundle endpoint=http://{host}:{port} "
        f"span_id={span_ctx.span_id} trace_id={span_ctx.trace_id}",
        file=sys.stderr,
    )
    bundle.trace_adapter.end_span(span_ctx)
    bundle.flush_and_shutdown(timeout_millis=5000)
    print("[diagnose] variant=factory-bundle flush_and_shutdown done", file=sys.stderr)


def main() -> int:
    instance_id = str(uuid.uuid4())
    print(f"[diagnose] instance_id={instance_id}", file=sys.stderr)
    with _collector_container() as collector:
        host = collector.get_container_host_ip()
        port = int(collector.get_exposed_port(_GRPC_PORT))
        metrics_port = int(collector.get_exposed_port(_INTERNAL_METRICS_PORT))
        for variant in _VARIANTS:
            try:
                _run_variant(variant, host=host, port=port, instance_id=instance_id)
            except Exception as exc:
                print(
                    f"[diagnose] variant={variant.name} raised {type(exc).__name__}: {exc}",
                    file=sys.stderr,
                )
            # Kurz warten, damit Collector den Export verarbeiten kann.
            time.sleep(1.0)
        # 6. Variante: voller Produktiv-Pfad via Factory + Bundle +
        # OtlpTraceAdapter — vergleicht den Smoke-Test-Code-Pfad mit
        # den Standalone-Varianten oben.
        try:
            _run_factory_variant(host=host, port=port, instance_id=instance_id)
        except Exception as exc:
            print(
                f"[diagnose] variant=factory-bundle raised {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
        time.sleep(1.0)
        # Collector-Logs ueber die Docker-API holen und am Ende dumpen.
        logs = collector.get_wrapped_container().logs().decode("utf-8", errors="replace")
        print("\n[diagnose] ===== COLLECTOR LOGS =====", file=sys.stderr)
        print(logs, file=sys.stderr)
        print("[diagnose] ===== END COLLECTOR LOGS =====", file=sys.stderr)
        # Auswertung: zaehle pro Variante die Span-Vorkommen im Collector-Log
        # UND scrape die Internal-Counter — Letzteres ist laut Doku die
        # einzige verlaessliche Quelle ("kommt am Receiver an / wird
        # gedroppet / wird exportiert"). Debug-Logs allein zeigen das
        # nicht.
        print("\n[diagnose] ===== MATRIX (debug-log hits) =====", file=sys.stderr)
        for variant in _VARIANTS:
            marker = f"diagnose.{variant.name}"
            hits = logs.count(marker)
            print(
                f"[diagnose]   variant={variant.name:30s} collector_hits_for_span_name={hits}",
                file=sys.stderr,
            )
        factory_hits = logs.count("diagnose.factory.bundle")
        print(
            f"[diagnose]   variant={'factory-bundle':30s} collector_hits_for_span_name={factory_hits}",
            file=sys.stderr,
        )
        print(
            f"\n[diagnose] ===== INTERNAL METRICS "
            f"(http://{host}:{metrics_port}/metrics) =====",
            file=sys.stderr,
        )
        _dump_internal_counters(host, metrics_port)
    return 0


def _dump_internal_counters(host: str, metrics_port: int) -> None:
    """Scraped die Collector-Internal-Metrics (Prometheus-Format) und
    druckt die Trigger-029-relevanten Counter (Receiver/Processor/
    Exporter pro Signal). Counter sind kumulativ ueber den Container-
    Lebenslauf — keine Per-Variante-Aufschluesselung im Prometheus-
    Format. Was wir hier sehen ist die Summe ueber alle Varianten
    plus Self-Telemetry des Collectors."""
    url = f"http://{host}:{metrics_port}/metrics"
    try:
        body = urllib.request.urlopen(url, timeout=5.0).read().decode("utf-8")
    except Exception as exc:
        print(
            f"[diagnose]   scrape failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return
    for line in body.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        if any(line.startswith(counter) for counter in _INTERESTING_COUNTERS):
            print(f"[diagnose]   {line}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
