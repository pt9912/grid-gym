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

| Datei                          | Gegenstand                                                                                                                                          |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `M1-tick-loop-spine.md`        | M1-Slice-Plan: deterministischer Tick-Loop ohne Geraete (Domain-Modelle, ClockPort/RandomPort, Scheduler, Snapshot, Scenario/Replay, FastAPI-Stub, Compose-Smoke). 7 Wellen, `make fullbuild` als Abschluss-Gate. |
| `001-code-review-doc.md`       | `docs/user/code-review.md` + PR-Template. M1-blockierend (Post-Acceptance aktiviert per Drittes Review, 2026-05-15). Wartet auf Scope-Schliff.       |

Spike-0 selbst ist abgeschlossen und in
[`done/spike-0.md`](../done/spike-0.md) archiviert. Weitere
Eintraege folgen mit Geraetemodellen aus §9 Lastenheft (M2),
optionalen Protokolladaptern (`GG-MQTT/MODB/OPCUA/DNP3/IEC-001`)
und UI-Erweiterungen `GG-UI-006..008`.
