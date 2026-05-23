# In Progress

Lebende Roadmap und aktive Slice-Plaene, an denen gearbeitet wird.

## Bestand

| Datei                     | Gegenstand                                                                                                                                          |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `roadmap.md`              | Meilenstein-Uebersicht (M1..Mx) mit Lastenheft-/Architektur-Bezuegen, Abnahmekriterien und Status.                                                  |
| `M3-faults-agents-observability.md` | M3-Slice-Plan: Fault-Injection + Multi-Agent-Bus + Observability (Log/Metrics/Trace). Stand 2026-05-23: `In Progress` — Welle 0/1/2/3/4a/4b/5 abgeschlossen (Multi-Agent komplett, Observability-Foundation komplett); Welle 6 (OTLP-Adapter) ist der naechste Slice. |
| `025-github-actions-four-gates.md` | Trigger 025: GitHub-Actions-CI-Workflow mit vier Pflicht-Gates (`lint-imports`, `ruff check`, `python tools/arch_check.py`, `mypy --strict`). Stand 2026-05-21: `In Progress` — `.github/workflows/ci.yml` eingebaut in `01796ae`; wartet auf ersten produktiven CI-Lauf nach Push auf `origin/main`. Wandert nach `done/` nach erstem gruenen Lauf. M6-Vorzieh-Slice. |
