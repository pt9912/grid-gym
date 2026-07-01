# Planning

Planungs- und Slice-Plan-Verzeichnis fuer grid-gym. Jedes
Unterverzeichnis hat einen klar abgegrenzten Lifecycle-Status:

| Verzeichnis    | Inhalt                                                                  |
| -------------- | ----------------------------------------------------------------------- |
| [`open/`](open/)               | Trigger-Watch-Notizen (Follow-up-Items, warten auf konkreten Anlass).    |
| [`next/`](next/)               | Geplante Arbeit mit Scope-Skizze, aber kein laufender Slice.             |
| [`in-progress/`](in-progress/) | Lebende Roadmap und aktive Slice-Plaene, an denen gearbeitet wird.       |
| [`done/`](done/)               | Abgeschlossene Slices und Meilensteinplaene (eingefroren, nur Referenz). |

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

Analog gilt fuer groessere Slice-Plaene (`NNN-slug.md`): der Self-Move
nach `done/` erfolgt per reinem `git mv` als Teil der eigenen
Closure-Sequenz. (Historisch galt dies fuer Meilenstein-Slice-Plaene
`M*-*.md` am Meilenstein-Closure.)

Vor dieser Konvention wurde der Move erst durch den **Pre-C0-Commit
der Folge-Welle** ausgefuehrt. Das hat funktioniert, solange eine
Folge-Welle planmaessig kam, hat aber Done-Wellen unbestimmt lang in
`in-progress/` haengen lassen, wenn die naechste Welle / der naechste
Meilenstein noch nicht aktiv war.

## Datei-Naming-Konvention

Neue Slice-/Wellen-Dokumente werden **repo-weit fortlaufend** als
`NNN-slug.md` benannt (dreistellige Nummer; Beispiele `041-...`,
`045-...`, `051-...`, `053-...`). Grosse Slices sub-slicen als
`NNN-a`/`NNN-b`. Die Nummer ist repo-weit eindeutig und verhindert
Kollisionen ohne Meilenstein-Container
([`ADR 0072`](../adr/0072-slice-driven-planning-no-milestones.md)).

**Historisch:** Bis zur slice-first-Umstellung trugen die Welle-Slice-
Begleit-Dokumente das `M{N}-welle-{X}.md`-Praefix (Beispiele
`M3-welle-5.md`, `M8-welle-2a.md`) zur Meilenstein-Zuordnung, und die
Meilenstein-Slice-Plaene das `M{N}-`-Praefix (`M2-devices.md`). Diese
Dokumente bleiben in `done/`/`done-archive/` in ihrer historischen Form
erstarrt; das `M{N}`-Praefix wird fuer **neue** Dokumente nicht mehr
vergeben.
