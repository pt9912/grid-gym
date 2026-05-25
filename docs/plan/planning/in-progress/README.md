# In Progress

Lebende Roadmap und aktive Slice-Plaene, an denen gearbeitet wird.

## Bestand

| Datei                     | Gegenstand                                                                                                                                          |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `roadmap.md`              | Meilenstein-Uebersicht (M1..Mx) mit Lastenheft-/Architektur-Bezuegen, Abnahmekriterien und Status.                                                  |
| `M3-faults-agents-observability.md` | M3-Slice-Plan: Fault-Injection + Multi-Agent-Bus + Observability (Log/Metrics/Trace). Stand 2026-05-24: `In Progress` — Welle 0/1/2/3/4a/4b/5 abgeschlossen (Multi-Agent komplett, Observability-Foundation komplett); Welle 6 (OTLP-Adapter) eroeffnet via `M3-welle-6.md`. |
| `M3-welle-6.md`           | Welle-6-Slice-Begleit: telemetry-otlp-Adapter (gRPC) + Compose-Collector-Sibling + Integration-Smoke (≥1 Span + ≥1 Metric). Stand 2026-05-25: `In Progress` — **C1 done** (`c98ce1a..5493831` inkl. drei Review-Folgen) und **C2 done** (`c61ab0d`: `otel-collector`-Sibling + Config-YAML + `make runtime`-Poll + `make image-audit`-Erweiterung; distroless-Image, externer Health-Poll). C3 (Integration-Smoke `tests/integration/test_otlp_compose_smoke.py` + Runbook `docs/user/observability.md` + README-Closure + Status/DoD-Sync) ausstehend. |
