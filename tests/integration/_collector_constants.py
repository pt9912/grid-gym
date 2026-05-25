"""Single-Source-of-Truth fuer den OTLP-Collector-Pin in den
Welle-6-Integration-Tests und im Diagnose-Tooling.

Bezug: Welle-6-Review-Folge M-1 (`docs/plan/planning/done/M3-welle-6.md`
Review-Folge 2026-05-25). Vorher waren `OTEL_COLLECTOR_IMAGE_DEFAULT`
und die Port-Konstanten dupliziert in `test_otlp_compose_smoke.py`,
`tools/diagnose_otlp_span_export.py` und `Makefile` — bei einem
Upgrade muessten drei `Final[str]`-Defaults plus eine `?=`-Variable
parallel gepflegt werden.

`deploy/compose.yml` ist bewusst NICHT auf dieses Modul angewiesen
(YAML kann nicht importieren), sondern liest die Env-Var
`OTEL_COLLECTOR_IMAGE` mit `:-default`-Fallback aus dem Makefile.
Bei einem Upgrade braucht es daher zwei synchronisierte Stellen:
diese Datei + `Makefile`s `OTEL_COLLECTOR_IMAGE ?=`-Default.
"""

from __future__ import annotations

from typing import Final

OTEL_COLLECTOR_IMAGE_DEFAULT: Final[str] = "otel/opentelemetry-collector-contrib:0.152.1"
"""Default-Pin fuer das OTel-Collector-Contrib-Image. Override per
`OTEL_COLLECTOR_IMAGE`-Env-Var ueberall, wo es konsumiert wird
(Smoke-Fixture, Diagnose-Script, Compose-File via Makefile)."""

OTEL_COLLECTOR_IMAGE_ENV: Final[str] = "OTEL_COLLECTOR_IMAGE"

# Port-Konvention aus `deploy/otel-collector-config.yaml`:
GRPC_PORT: Final[int] = 4317
"""OTLP-gRPC-Receiver-Port (Standard-OTel-Konvention)."""

HEALTH_PORT: Final[int] = 13133
"""`health_check`-Extension-Port (Standard-OTel-Konvention)."""

INTERNAL_METRICS_PORT: Final[int] = 8888
"""`service.telemetry.metrics.readers.pull.exporter.prometheus`-Port
fuer Internal-Counter-Scrape (siehe Welle-6-Trigger-029-Closure +
`docs/user/observability.md` §4.3)."""
