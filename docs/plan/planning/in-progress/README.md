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
| `M2-devices.md`           | Forwarder-Stub fuer ADR-Pfad-Stabilitaet (ADR 0006 §3); aktueller Slice-Plan ist [`done/M2-devices.md`](../done/M2-devices.md), Welle-Tabelle + Abnahme-Belege [`done/M2-devices-results.md`](../done/M2-devices-results.md). M2 ist `Done` seit 2026-05-20. |
| `welle-4b.md`             | M3-Welle-4b-Slice-Begleit-Dokument (RuleBasedAgent + Scenario-`agents`-Top-Level-Block + Property-Tests + End-to-End-Demo + Welle-4-Abschluss-Gate). Stand 2026-05-22: `In Progress` (Pre-C0 `8802dc0` rename welle-4a → done/, Post-Pre-C0 `c055be9` link-fix, C0 dieses Slice-Doc). Welle 4 schliesst mit Welle-4b ab; Welle-4a `Done` ist in [`done/welle-4a.md`](../done/welle-4a.md). |
| `M3-faults-agents-observability.md` | M3-Slice-Plan: Fault-Injection + Multi-Agent-Bus + Observability (Log/Metrics/Trace). Stand 2026-05-22: `In Progress` — Welle 0/1/2/3/4a abgeschlossen, Welle 4b (RuleBasedAgent + Scenario-Schema + Welle-4-Gate) der aktuelle Slice. |
| `025-github-actions-four-gates.md` | Trigger 025: GitHub-Actions-CI-Workflow mit vier Pflicht-Gates (`lint-imports`, `ruff check`, `python tools/arch_check.py`, `mypy --strict`). Stand 2026-05-21: `In Progress` — `.github/workflows/ci.yml` eingebaut in `01796ae`; wartet auf ersten produktiven CI-Lauf nach Push auf `origin/main`. Wandert nach `done/` nach erstem gruenen Lauf. M6-Vorzieh-Slice. |
| `M1-tick-loop-spine.md`   | Forwarder-Stub (Link-Stabilitaet fuer ADRs 0008/0009 etc., die auf den `in-progress/`-Pfad zeigen). Aktueller Slice-Plan: [`done/M1-tick-loop-spine.md`](../done/M1-tick-loop-spine.md). |
