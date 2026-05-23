# In Progress

Lebende Roadmap und aktive Slice-Plaene, an denen gearbeitet wird.

## Bestand

| Datei                     | Gegenstand                                                                                                                                          |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `roadmap.md`              | Meilenstein-Uebersicht (M1..Mx) mit Lastenheft-/Architektur-Bezuegen, Abnahmekriterien und Status.                                                  |
| `M3-faults-agents-observability.md` | M3-Slice-Plan: Fault-Injection + Multi-Agent-Bus + Observability (Log/Metrics/Trace). Stand 2026-05-23: `In Progress` — Welle 0/1/2/3/4a/4b/5 abgeschlossen (Multi-Agent komplett, Observability-Foundation komplett); Welle 6 (OTLP-Adapter) ist der naechste Slice. |
| `M3-welle-5.md`           | M3-Welle-5-Slice-Begleit-Dokument (Observability-Foundation: `LogPort`/`MetricsPort`/`TracePort` als Driven-Ports + Null-Adapter + Verdrahtung in TickLoop/Agents/Faults). Stand 2026-05-23: `Done` (Commits `7427daf..a690c02` + C3-Sync). 1023 Unit-Tests + 19 Integration-Tests; Coverage 95.55% total; `make fullbuild` cache-frei gruen ohne Override (Welle-5-Abnahme-Kriterium aus ADR 0024 §4.1 erfuellt). ADR 0024 `Proposed → Provisional`; ADR 0029 `Accepted` (Hygiene-Folge, 11. arch_check-Contract `AC-NO-COVERAGE-PRAGMA`). Wandert nach `done/` per Wave-Self-Close-Konvention im End-of-Wave-Commit. |
| `025-github-actions-four-gates.md` | Trigger 025: GitHub-Actions-CI-Workflow mit vier Pflicht-Gates (`lint-imports`, `ruff check`, `python tools/arch_check.py`, `mypy --strict`). Stand 2026-05-21: `In Progress` — `.github/workflows/ci.yml` eingebaut in `01796ae`; wartet auf ersten produktiven CI-Lauf nach Push auf `origin/main`. Wandert nach `done/` nach erstem gruenen Lauf. M6-Vorzieh-Slice. |
