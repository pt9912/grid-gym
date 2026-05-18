# Next

Plan- und Slice-Notizen fuer **konkret geplante, aber noch nicht
aktive** Arbeit. Abgrenzung zu den anderen `planning/`-Unterverzeichnissen:

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

| Datei                  | Gegenstand                                                                                                                                                |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `M2-devices.md`        | M2-Slice-Plan: produktive Geraetemodelle (Battery, PV, Load, SmartMeter, GridConnection) + `grid_model`-Netzbilanz. Welle 0..7, Status `Next` (2026-05-18). |
| `M1-tick-loop-spine.md` | Forwarder-Stub (Link-Stabilitaet fuer `ADR 0007` Zeile 162). Aktueller Slice-Plan liegt in [`done/M1-tick-loop-spine.md`](../done/M1-tick-loop-spine.md). |

Spike-0 selbst ist abgeschlossen und in
[`done/spike-0.md`](../done/spike-0.md) archiviert. Weitere
Eintraege folgen mit optionalen Protokolladaptern
(`GG-MQTT/MODB/OPCUA/DNP3/IEC-001`) und UI-Erweiterungen
`GG-UI-006..008`.
