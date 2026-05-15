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

| Datei                  | Gegenstand                                                                                       |
| ---------------------- | ------------------------------------------------------------------------------------------------ |
| `spike-0.md`           | Spike-0 als Pre-Acceptance-Slice fuer `ADR 0002` und `ADR 0005` (Toolchain, Skelett, A-1/A-2-Contracts, sechzehn Verstoss-Branches). Aktiviert `roadmap.md` Vorbedingung 1. |

Weitere Eintraege entstehen nach Spike-0, sobald M1 das erste
Domain-Slice (Tick-Loop-Spine) skizziert — und mit jedem Folgeschritt
fuer Geraetemodelle aus §9 Lastenheft, optionale Protokolladapter
(`GG-MQTT/MODB/OPCUA/DNP3/IEC-001`) oder UI-Erweiterungen
`GG-UI-006..008`.
