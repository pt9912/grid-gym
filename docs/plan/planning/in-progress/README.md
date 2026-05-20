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
| `welle-1.md`              | M3-Welle-1-Slice-Begleit-Dokument (Fault-Foundation: ADR 0022 + FaultPort + FaultInjectableDevice + Validator-Haertung + TickLoop-Hook). Stand 2026-05-20: `In Progress`. Erste Code-Welle in M3. |
| `M3-faults-agents-observability.md` | M3-Slice-Plan: Fault-Injection + Multi-Agent-Bus + Observability (Log/Metrics/Trace). Stand 2026-05-20: `In Progress` seit M3-Welle-0. |
| `M1-tick-loop-spine.md`   | Forwarder-Stub (Link-Stabilitaet fuer ADRs 0008/0009 etc., die auf den `in-progress/`-Pfad zeigen). Aktueller Slice-Plan: [`done/M1-tick-loop-spine.md`](../done/M1-tick-loop-spine.md). |
