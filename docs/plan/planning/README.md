# Planning

Planungs- und Slice-Plan-Verzeichnis fuer grid-gym. Jedes
Unterverzeichnis hat einen klar abgegrenzten Lifecycle-Status:

| Verzeichnis    | Inhalt                                                                  |
| -------------- | ----------------------------------------------------------------------- |
| `open/`        | Trigger-Watch-Notizen (Follow-up-Items, warten auf konkreten Anlass).    |
| `next/`        | Geplante Arbeit mit Scope-Skizze, aber kein laufender Slice.             |
| `in-progress/` | Lebende Roadmap und aktive Slice-Plaene, an denen gearbeitet wird.       |
| `done/`        | Abgeschlossene Slices und Meilensteinplaene (eingefroren, nur Referenz). |

Ein Eintrag wechselt typischerweise:
`open/` (Trigger entsteht) → `next/` (Scope skizziert) →
`in-progress/` (Slice-Plan aktiv) → `done/` (geliefert).

## Wave-Self-Close-Commit-Konvention

Sobald eine `welle-*.md` den Status `Done` erreicht, schliesst sie ihre
eigene Commit-Sequenz mit einem reinen `git mv welle-N.md ../done/`
(kein Inhalts-Edit im selben Commit — git-Rename-Detection braucht den
reinen Move). Inhaltliche Folge-Edits — relative Link-Anpassungen des
verschobenen Dokuments, Update referenzierender Bezug-Linien per
[`ADR 0028`](../adr/0028-link-maintenance-accepted-adr-bezug.md),
Bestand-Zeilen-Pflege in den README-Dateien — landen in einem
unmittelbar nachfolgenden Commit.

Analog gilt fuer Meilenstein-Slice-Plaene (`M*-*.md`,
`M*-faults-...md`) am Meilenstein-Closure: Self-Move durch einen
reinen `git mv` als Teil der Welle-7-Closure-Sequenz, nicht ueber den
ersten Commit des Folge-Meilensteins.

Vor dieser Konvention wurde der Move erst durch den **Pre-C0-Commit
der Folge-Welle** ausgefuehrt. Das hat funktioniert, solange eine
Folge-Welle planmaessig kam, hat aber Done-Wellen unbestimmt lang in
`in-progress/` haengen lassen, wenn die naechste Welle / der naechste
Meilenstein noch nicht aktiv war.
