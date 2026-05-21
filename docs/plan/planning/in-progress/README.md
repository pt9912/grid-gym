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
| `welle-3.md`              | M3-Welle-3-Slice-Begleit-Dokument (Multi-Agent-Foundation: ADR 0023 `Agent`-Protocol + `AgentMessageBus`-Core-Klasse + `AgentMessage`-Domain + TickLoop-Schritt-D2-Hook + Pending-Command-Buffer). Stand 2026-05-21: `Done` (Commits `3dbe6af..d6f66fc` + C3 + Review-Folge 2). Foundation-only; konkrete `RuleBasedAgent`-Implementer + Pending-Buffer-Drain kommen mit Welle 4. Wandert nach `done/` mit M3-Welle-4-Pre-C0. |
| `M3-faults-agents-observability.md` | M3-Slice-Plan: Fault-Injection + Multi-Agent-Bus + Observability (Log/Metrics/Trace). Stand 2026-05-21: `In Progress` — Welle 0/1/2/3 abgeschlossen, Welle 4 (Multi-Agent-Subsystem konkret) als naechster Schritt. |
| `M1-tick-loop-spine.md`   | Forwarder-Stub (Link-Stabilitaet fuer ADRs 0008/0009 etc., die auf den `in-progress/`-Pfad zeigen). Aktueller Slice-Plan: [`done/M1-tick-loop-spine.md`](../done/M1-tick-loop-spine.md). |
