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

| Datei                       | Gegenstand                                                                                                                                        |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `001-code-review-doc.md`    | `docs/user/code-review.md` + PR-Template. M1-blockierend (Post-Acceptance aktiviert per Drittes Review, 2026-05-15). Wartet auf Scope-Schliff.    |

Spike-0 selbst ist abgeschlossen und in
[`done/spike-0.md`](../done/spike-0.md) archiviert. Weitere
Eintraege entstehen mit dem ersten M1-Slice (Tick-Loop-Spine)
und mit jedem Folgeschritt fuer Geraetemodelle aus §9 Lastenheft,
optionale Protokolladapter (`GG-MQTT/MODB/OPCUA/DNP3/IEC-001`)
oder UI-Erweiterungen `GG-UI-006..008`.
