# In Progress

Lebende Roadmap und aktive Slice-Plaene, an denen gearbeitet wird.
Abgrenzung zu den anderen `planning/`-Unterverzeichnissen:

| Verzeichnis    | Inhalt                                                                  |
| -------------- | ----------------------------------------------------------------------- |
| `open/`        | Trigger-Watch-Notizen (Follow-up-Items, warten auf konkreten Anlass).    |
| `next/`        | Geplante Arbeit mit Scope-Skizze, aber kein laufender Slice.             |
| `in-progress/` | Lebende Roadmap und aktive Slice-Plaene, an denen gearbeitet wird.       |
| `done/`        | Abgeschlossene Slices und Meilensteinplaene (eingefroren, nur Referenz). |

Ein Eintrag wechselt typischerweise:
`open/` (Trigger entsteht) → `next/` (Scope skizziert) →
`in-progress/` (Slice-Plan aktiv) → `done/` (geliefert).

## Bestand

| Datei                     | Gegenstand                                                                                                                                          |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `roadmap.md`              | Meilenstein-Uebersicht (M1..Mx) mit Lastenheft-/Architektur-Bezuegen, Abnahmekriterien und Status.                                                  |
| `welle-4b.md`             | M3-Welle-4b-Slice-Begleit-Dokument (RuleBasedAgent + Scenario-`agents`-Top-Level-Block + Property-Tests + End-to-End-Demo + Welle-4-Abschluss-Gate). Stand 2026-05-22: `Done` (Commits `8802dc0..ac7b47f` + C3-Sync). 992 Unit-Tests + 19 Integration-Tests; `make fullbuild` cache-frei gruen ohne Override (Welle-4-Abnahme-Kriterium erfuellt). Wandert nach `done/` mit M3-Welle-5-Pre-C0. |
| `M3-faults-agents-observability.md` | M3-Slice-Plan: Fault-Injection + Multi-Agent-Bus + Observability (Log/Metrics/Trace). Stand 2026-05-22: `In Progress` — Welle 0/1/2/3/4a/4b abgeschlossen (M3-Welle 4 = Multi-Agent komplett); Welle 5 (Observability — LogPort/MetricsPort/TracePort) der naechste Slice. |
| `025-github-actions-four-gates.md` | Trigger 025: GitHub-Actions-CI-Workflow mit vier Pflicht-Gates (`lint-imports`, `ruff check`, `python tools/arch_check.py`, `mypy --strict`). Stand 2026-05-21: `In Progress` — `.github/workflows/ci.yml` eingebaut in `01796ae`; wartet auf ersten produktiven CI-Lauf nach Push auf `origin/main`. Wandert nach `done/` nach erstem gruenen Lauf. M6-Vorzieh-Slice. |
