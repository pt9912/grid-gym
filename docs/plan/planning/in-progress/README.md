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
| `M2-devices.md`           | M2-Slice-Plan: produktive Geraetemodelle (Battery, PV, Load, SmartMeter, GridConnection) + `grid_model`-Netzbilanz + Scenario-Loader-Builder + MVP-Demo. Stand 2026-05-20: Wellen 0/1/2/3/4/5/6 (6a + 6b + 6c) abgeschlossen; Welle 7 (M2-Closure) ausstehend. |
| `welle-6c.md`             | Welle-6c-Slice-Begleit-Dokument (lesefreundlicher Index zu `M2-devices.md §3 Welle 6c`). Stand 2026-05-20: `Done` mit Commits `8a3aa2f` (Slice-Doc) + `c31052c` (`feat`). |
| `M1-tick-loop-spine.md`   | Forwarder-Stub (Link-Stabilitaet fuer ADRs 0008/0009 etc., die auf den `in-progress/`-Pfad zeigen). Aktueller Slice-Plan: [`done/M1-tick-loop-spine.md`](../done/M1-tick-loop-spine.md). |
