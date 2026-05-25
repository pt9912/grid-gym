# In Progress

Lebende Roadmap und aktive Slice-Plaene, an denen gearbeitet wird.

## Bestand

| Datei                     | Gegenstand                                                                                                                                          |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `roadmap.md`              | Meilenstein-Uebersicht (M1..Mx) mit Lastenheft-/Architektur-Bezuegen, Abnahmekriterien und Status.                                                  |
| `M3-faults-agents-observability.md` | M3-Slice-Plan: Fault-Injection + Multi-Agent-Bus + Observability (Log/Metrics/Trace). Stand 2026-05-24: `In Progress` — Welle 0/1/2/3/4a/4b/5 abgeschlossen (Multi-Agent komplett, Observability-Foundation komplett); Welle 6 (OTLP-Adapter) eroeffnet via `M3-welle-6.md`. |
| `M3-welle-6.md`           | Welle-6-Slice-Begleit: telemetry-otlp-Adapter (gRPC) + Compose-Collector-Sibling + Integration-Smoke (≥1 Span + ≥1 Metric). Stand 2026-05-24: `In Progress` — **C1 done** (`c98ce1a..5493831` inkl. drei Review-Folgen): OTel-Deps + Import-Linter + Floor-Refresh, ADR-0024-§4.5-Schaerfung mit 8 normativen Decisions, `OtlpAdapterConfig` + drei Adapter (`OtlpLogAdapter`/`OtlpMetricsAdapter`/`OtlpTraceAdapter`) + `build_otlp_adapters`-Factory + `flush_and_shutdown`-Helper produktiv; neuer 12. arch_check-Contract `AC-OTLP-ADAPTER-NO-TIME`. C2 (`deploy/compose.yml` OTLP-Collector-Sibling) und C3 (Compose-/Integration-Smoke + Runbook + Status/DoD-Sync) ausstehend. |
