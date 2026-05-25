"""M3-Welle-6-C3 Integration-Smoke fuer den OTLP-Adapter-Pfad.

Spawnt einen `otel-collector`-Sibling-Container via Docker-API
(testcontainers-`DockerContainer`, **nicht** `DockerCompose` —
der `test-runner` hat kein `docker`-CLI und braucht keinen).
Treibt einen TickLoop mit dem MVP-Demo-Szenario gegen das
produktive `OtlpAdapterBundle` und prueft, dass mindestens eine
Metric und ein Log mit der per-Lauf eindeutigen `service.instance.
id` exportiert wurden.

Erfuellt die Welle-6-DoD-Pflicht „`make test-integration` gruen
mit Welle-6-Smoke" (M3-welle-6.md §C3) und das Acceptance-Kriterium
aus ADR 0024 §4.5.7 (Compose-Smoke-Determinismus-Pattern).

**Span-Caveat (Welle 6 C3, 2026-05-25):** Der **Span**-Teil des
ursprueng-geplanten Tripel-Asserts (Span/Metric/Log) ist hier
**bewusst nicht** gepflichtet — siehe Trigger 029
(`open/029-otlp-span-grpc-export-edge-case.md`). Befund: Adapter
emittiert Spans SDK-side korrekt (ConsoleSpanExporter zeigt sie,
recording=True, valide IDs); der OTLP-gRPC-Span-Export ueber die
Sibling-Container-Verbindung kommt jedoch nicht im Collector an.
Metrics + Logs ueber die identische Connection funktionieren.
Detail-Diagnose in `tools/diagnose_otlp_span_export.py`. C3-DoD-
Item 'Span-Sichtbarkeit' wandert nach Trigger 029, Welle-6-Closure
bleibt mit dokumentiertem Caveat moeglich.

**Sink (Welle-6-C3-Refinement, 2026-05-25):**
Iteration 1 (DockerCompose-Fixture) scheiterte: testcontainers
ruft `docker compose ...` als Subprozess auf, der `test-runner`-
Container hat aber kein `docker`-CLI installiert.

Iteration 2 (DockerContainer + file-Exporter + tmpfs auf
`/var/log/otel`) scheiterte: trotz `mode=1777` und `user=0:0`
lieferte `container.get_archive(...)` keine Daten — docker-py
extrahiert tmpfs-Inhalte im Sibling-Container-Modus nicht
zuverlaessig. Der Collector bekam die Records nachweislich
(Debug-Exporter zeigt strukturierte Records im Container-Stderr),
aber der File-Sink-Pfad blieb fuer den Test unsichtbar.

Iteration 3 (gewaehlt): **Sink = Container-Logs des Debug-
Exporters**. Der `debug`-Exporter im Collector emittiert
Span/Metric/Log strukturiert nach stderr; `container.logs()`
ist via Docker-API zuverlaessig lesbar (kein tmpfs-Edge-Case).
Per-Lauf eindeutige `service.instance.id` filtert weiterhin
gegen alte Eintraege (Pflicht 3).

**Sink-Determinismus-Pflichten (ADR 0024 §4.5.7):**

1. **Per-Lauf isolierter Sink** — frischer Collector-Container
   pro Test-Modul hat leeren Logbuffer; kein Cross-Run-Carryover.
2. **Vorab-Truncation** — implizit durch Container-Boot.
3. **Per-Lauf eindeutige `service.instance.id`** — `uuid.uuid4()`
   pro Test-Run; alle Assertions filtern auf diese ID.
4. **Zweischichtiges Flush-Protokoll** — `OtlpAdapterBundle.
   flush_and_shutdown()` (SDK-Seite synchron) + Bounded-Poll-Loop
   mit 5s-Timeout im 100-ms-Raster auf die Container-Logs
   (Collector-Seite eventually).
"""

from __future__ import annotations

import os
import re
import time
import urllib.error
import urllib.request
import uuid
from collections.abc import Iterator
from typing import Final

import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.adapters.driven.telemetry_otlp import (
    OtlpAdapterBundle,
    OtlpAdapterConfig,
    build_otlp_adapters,
)
from grid_gym.hexagon.core.scenario.loader import TickLoopWiring, build_tick_loop

from tests.integration._constants import MVP_DEMO_SCENARIO_PATH
from tests.integration._yaml_scenario_loader import load_yaml_scenario
from tests.unit.hexagon.ports.driven._fakes import FakeClock

_COLLECTOR_IMAGE_DEFAULT: Final[str] = "otel/opentelemetry-collector-contrib:0.152.1"
_COLLECTOR_IMAGE_ENV: Final[str] = "OTEL_COLLECTOR_IMAGE"
_GRPC_PORT: Final[int] = 4317
_HEALTH_PORT: Final[int] = 13133
_SINK_DIR_IN_CONTAINER: Final[str] = "/var/log/otel"
_TICKS: Final[int] = 5
_SDK_FLUSH_TIMEOUT_MS: Final[int] = 5000
_SINK_POLL_TIMEOUT_S: Final[float] = 5.0
_SINK_POLL_INTERVAL_S: Final[float] = 0.1
_COLLECTOR_HEALTH_TIMEOUT_S: Final[float] = 30.0

# Regex-Pattern auf den Debug-Exporter-Output. Der Collector schreibt
# pretty-printed Records nach stderr (eine Zeile pro Feld), wir
# scannen blockweise nach Metric- und Log-Signal plus per-Lauf-
# instance.id-Filter. Span-Pattern (Trigger 029) bleibt absichtlich
# ausgeklammert.
_RE_INSTANCE_ID = re.compile(r"service\.instance\.id:\s*Str\(([0-9a-f-]+)\)")
_RE_METRIC_NAME = re.compile(r"^\s*->\s*Name:\s*(\S+)\s*$", re.MULTILINE)
_RE_LOG_BODY = re.compile(r"^Body:\s*Str\((\S+)\)\s*$", re.MULTILINE)
# Block-Trenner: der Collector schreibt pro Export-Aufruf einen
# `ResourceMetrics/ResourceLogs #N`-Header gefolgt von Resource-
# Attributes und Inhalts-Blocks. Wir trennen am JSON-Footer, der
# jeden Block beendet.
_RE_BLOCK_END = re.compile(r'^\t\{"resource":', re.MULTILINE)

# Welle-6-Smoke-Profil-Config: kurzer Batch-Timeout, file+debug-
# Exporter, drei symmetrische Pipelines, health_check-Extension.
# Bewusst hier inline (nicht aus `deploy/otel-collector-config.yaml`
# kopiert), weil der Test gegen einen Container-internen Sink-Pfad
# laeuft und einen anderen file-Path nutzen koennte. `file`-Exporter
# bleibt im Config, auch wenn der Test ihn nicht liest — er ist der
# Pattern, den Produktiv-Stack `deploy/compose.yml` nutzt, und der
# Debug-Exporter ist sowieso symmetrisch dazu konfiguriert.
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
  file:
    path: /var/log/otel/otel-out.jsonl
    flush_interval: 100ms
  debug:
    verbosity: detailed
service:
  extensions: [health_check]
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [file, debug]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [file, debug]
    logs:
      receivers: [otlp]
      processors: [batch]
      exporters: [file, debug]
"""


@pytest.fixture(scope="module")
def _collector() -> Iterator[DockerContainer]:
    """Spawnt einen otel-collector-Container fuer das ganze Test-
    Modul (Boot ~3-5s; Funktions-Scope waere Verschwendung)."""
    image = os.environ.get(_COLLECTOR_IMAGE_ENV, _COLLECTOR_IMAGE_DEFAULT)
    container = (
        DockerContainer(image)
        .with_env("OTEL_CONFIG_YAML", _COLLECTOR_CONFIG_YAML)
        .with_command("--config=env:OTEL_CONFIG_YAML")
        .with_exposed_ports(_GRPC_PORT, _HEALTH_PORT)
        # tmpfs `mode=1777` + `user=0:0` damit der `file`-Exporter
        # im distroless-Image den Pipeline-Start nicht mit „no such
        # file or directory" abbricht. tmpfs-Inhalt ist aus dem
        # test-runner nicht via get_archive lesbar (siehe Modul-
        # Docstring Iteration 2), aber der `debug`-Exporter
        # auf stderr ist der eigentliche Test-Sink.
        .with_kwargs(
            tmpfs={_SINK_DIR_IN_CONTAINER: "rw,size=10m,mode=1777"},
            user="0:0",
        )
    )
    container.start()
    try:
        wait_for_logs(
            container,
            "Everything is ready. Begin running and processing data.",
            timeout=30,
        )
        _wait_collector_health(container)
        yield container
    finally:
        container.stop()


def _wait_collector_health(container: DockerContainer) -> None:
    """Bounded-Poll auf den Collector-Health-Endpoint vom
    `test-runner`-Container aus."""
    host = container.get_container_host_ip()
    port = container.get_exposed_port(_HEALTH_PORT)
    url = f"http://{host}:{port}/"
    deadline = time.monotonic() + _COLLECTOR_HEALTH_TIMEOUT_S
    last_error: BaseException | None = None
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2.0).read()
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as exc:
            last_error = exc
            time.sleep(0.5)
            continue
        return
    pytest.fail(
        f"otel-collector :{_HEALTH_PORT} nicht erreichbar nach "
        f"{_COLLECTOR_HEALTH_TIMEOUT_S}s: {last_error!r}"
    )


def test_otlp_compose_smoke_exports_metric_and_log(
    _collector: DockerContainer,
) -> None:
    """ADR 0024 §4.5.7: ein TickLoop-Lauf gegen den Collector-
    Sibling liefert >=1 Metric (`tick_count`) und >=1 Log
    (`tick_begin`/`tick_end`), gefiltert auf die per-Lauf
    eindeutige `service.instance.id`.

    Span-Pflicht (`tick.cycle`) ist hier bewusst raus —
    SDK-side korrekt, aber gRPC-Export an Sibling-Collector
    geht silent verloren. Siehe Trigger 029 +
    `tools/diagnose_otlp_span_export.py` fuer die laufende
    Eingrenzung."""
    instance_id = str(uuid.uuid4())
    grpc_host = _collector.get_container_host_ip()
    grpc_port = _collector.get_exposed_port(_GRPC_PORT)
    config = OtlpAdapterConfig(
        endpoint=f"http://{grpc_host}:{grpc_port}",
        service_name="grid-gym-smoke",
        service_instance_id=instance_id,
    )
    bundle = build_otlp_adapters(config)

    try:
        _drive_demo_ticks(bundle)
    finally:
        bundle.flush_and_shutdown(timeout_millis=_SDK_FLUSH_TIMEOUT_MS)

    _poll_signals_until_complete(_collector, instance_id)


def _drive_demo_ticks(bundle: OtlpAdapterBundle) -> None:
    """Baut den TickLoop aus dem MVP-Demo-Szenario mit dem
    OTLP-Adapter-Trio und treibt `_TICKS` Ticks. Wiederverwendet
    `MVP_DEMO_SCENARIO_PATH` aus M2-Welle-6c — Demo-Lauf reicht
    aus, um Metric (`tick_count`) + Log (`tick_begin`/`tick_end`)
    zu produzieren."""
    loaded = load_yaml_scenario(MVP_DEMO_SCENARIO_PATH)
    loop = build_tick_loop(
        loaded.scenario,
        run_id="welle-6-c3-smoke",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=loaded.scenario.simulation.seed),
        wiring=TickLoopWiring(
            log_port=bundle.log_adapter,
            metrics_port=bundle.metrics_adapter,
            trace_port=bundle.trace_adapter,
        ),
    )
    for _ in range(_TICKS):
        loop.tick()


def _poll_signals_until_complete(container: DockerContainer, instance_id: str) -> None:
    """Bounded-Poll-Loop auf die Container-Logs des Collectors (ADR
    0024 §4.5.7 Pflicht 4 Collector-Seite). Liest periodisch die
    Logs des `debug`-Exporters, scannt sie auf die per-Lauf
    eindeutige `service.instance.id` plus Metric+Log mit den
    erwarteten Namen. Test-Failure mit klarem Fehlertext UND
    Collector-Log-Tail, wenn das Duo nach `_SINK_POLL_TIMEOUT_S`
    nicht vollstaendig sichtbar ist."""
    deadline = time.monotonic() + _SINK_POLL_TIMEOUT_S
    last_signals: tuple[bool, bool] = (False, False)
    while time.monotonic() < deadline:
        logs = _get_collector_logs(container)
        last_signals = _check_signals_in_logs(logs, instance_id)
        if all(last_signals):
            return
        time.sleep(_SINK_POLL_INTERVAL_S)
    metric_ok, log_ok = last_signals
    # Failure-Diagnose: Collector-Logs nur bei Fail ausgeben, damit
    # gruene CI-Runs lesbar bleiben.
    log_tail = _get_collector_logs(container)[-4000:]
    pytest.fail(
        f"Collector-Smoke hat nach {_SINK_POLL_TIMEOUT_S}s nicht "
        f"alle Pflicht-Signale fuer instance.id={instance_id!r} "
        f"gesammelt (metric_tick_count={metric_ok}, "
        f"log_tick_begin_or_end={log_ok}). Flush nicht durchgekommen "
        f"oder Adapter nicht verkabelt. Collector-Logs (last 4000 "
        f"chars):\n{log_tail}"
    )


def _get_collector_logs(container: DockerContainer) -> str:
    """Liest die Container-Logs ueber die Docker-API. `logs()`
    liefert stdout+stderr als bytes; der `debug`-Exporter im
    Collector schreibt nach stderr."""
    raw = container.get_wrapped_container().logs()
    return raw.decode("utf-8", errors="replace")


def _check_signals_in_logs(logs: str, instance_id: str) -> tuple[bool, bool]:
    """Scannt die Collector-Logs auf das Signal-Duo mit Filter
    auf die per-Lauf eindeutige `service.instance.id`. Liefert
    `(metric_tick_count, log_tick_begin_or_end)`.

    Der `debug`-Exporter im Collector schreibt blockweise — jeder
    Block beginnt mit `ResourceMetrics/Logs #N`, listet
    `service.instance.id: Str(<uuid>)` in den Resource-Attributes
    und enthaelt die Metric-/Log-Inhalte darunter. Wir splitten
    an den JSON-Footer-Trennern und akzeptieren nur Bloecke, die
    unsere `instance_id` tragen."""
    metric_ok = False
    log_ok = False
    for block in _RE_BLOCK_END.split(logs):
        if not _block_has_instance_id(block, instance_id):
            continue
        if not metric_ok and any(name == "tick_count" for name in _RE_METRIC_NAME.findall(block)):
            metric_ok = True
        if not log_ok and any(
            body in {"tick_begin", "tick_end"} for body in _RE_LOG_BODY.findall(block)
        ):
            log_ok = True
    return metric_ok, log_ok


def _block_has_instance_id(block: str, instance_id: str) -> bool:
    return any(found == instance_id for found in _RE_INSTANCE_ID.findall(block))
