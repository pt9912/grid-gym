# In Progress

Lebende Roadmap und aktive Slice-Plaene, an denen gearbeitet wird.

## Bestand

| Datei                     | Gegenstand                                                                                                                                          |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `roadmap.md`              | Meilenstein-Uebersicht (M1..Mx) mit Lastenheft-/Architektur-Bezuegen, Abnahmekriterien und Status.                                                  |
| `M3-faults-agents-observability.md` | M3-Slice-Plan: Fault-Injection + Multi-Agent-Bus + Observability (Log/Metrics/Trace). Stand 2026-05-23: `In Progress` — Welle 0/1/2/3/4a/4b abgeschlossen (M3-Welle 4 = Multi-Agent komplett); Welle 5 (Observability — LogPort/MetricsPort/TracePort) aktiv eroeffnet. |
| `M3-welle-5.md`           | M3-Welle-5-Slice-Begleit-Dokument (Observability-Foundation: `LogPort`/`MetricsPort`/`TracePort` als Driven-Ports + Null-Adapter + Verdrahtung in TickLoop/Agents/Faults). Stand 2026-05-23: `In Progress` (C0 — Slice-Doc eroeffnet). Plant ADR 0024 mit C1. Erste Welle-Doc unter neuer `M{N}-welle-{X}.md`-Naming-Konvention. |
| `025-github-actions-four-gates.md` | Trigger 025: GitHub-Actions-CI-Workflow mit vier Pflicht-Gates (`lint-imports`, `ruff check`, `python tools/arch_check.py`, `mypy --strict`). Stand 2026-05-21: `In Progress` — `.github/workflows/ci.yml` eingebaut in `01796ae`; wartet auf ersten produktiven CI-Lauf nach Push auf `origin/main`. Wandert nach `done/` nach erstem gruenen Lauf. M6-Vorzieh-Slice. |
