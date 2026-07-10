# ADR 0001 — Dokumentations- und Planungsstruktur

**Status:** Accepted
**Datum:** 2026-05-14
**Bezug:** [Lastenheft](../../../spec/lastenheft.md), [Architektur](../../../spec/architecture.md)

---

## 1. Kontext

`grid-gym` startet in der Anforderungs- und Architekturphase. Neben dem
Lastenheft und der Architekturbeschreibung braucht das Projekt eine
stabile Dokumentationsstruktur fuer:

- normative Spezifikation,
- Architekturentscheidungen,
- Roadmap und Umsetzungsplaene,
- offene Folgearbeiten und Trigger-Watch-Punkte,
- anwender- und betreibernahe Erklaerungen sowie Runbooks,
- archivierte Ideenskizzen.

Die Struktur soll klein genug fuer den Projektstart bleiben, aber
spaeter Meilensteine, weitere ADRs und Umsetzungsslices aufnehmen
koennen. Sie muss zudem den V-Modell-Anforderungen aus
[der Traceability-Matrix](../traceability.md) (Rueckverfolgbarkeit
Anforderung → Design → Implementierung → Test) und der
Anforderung [`GG-TRACE-001`](../../../spec/lastenheft.md#gg-trace-001) Rechnung tragen.

---

## 2. Entscheidung

Die Dokumentation wird wie folgt organisiert:

| Pfad                                 | Zweck                                                          |
| ------------------------------------ | -------------------------------------------------------------- |
| `spec/`                              | normative Produkt- und Architekturvorgaben (Lastenheft, Architektur, ggf. weitere Specs) |
| `docs/plan/adr/`                     | Architecture Decision Records                                   |
| `docs/plan/planning/open/`           | Trigger-Watch, offene Folgearbeiten und Vorabklaerungen          |
| `docs/plan/planning/next/`           | konkret geplante, aber noch nicht aktive Arbeit (Scope-Skizze)   |
| `docs/plan/planning/in-progress/`    | aktive Roadmap und laufende Slice-Plaene                         |
| `docs/plan/planning/done/`           | abgeschlossene Plaene und Closure-Notizen                       |
| `docs/user/`                         | anwender- und betreibernahe Dokumentation                        |
| `docs/archive/`                      | verworfene oder historische Ideenskizzen                        |

ADR-Dateinamen folgen dem Schema
`NNNN-kurz-titel.md` (vierstellige Nummer, fortlaufend).

Lebenszyklus eines Plan-Eintrags:
`open/` (Trigger entsteht) → `next/` (Scope skizziert) →
`in-progress/` (Slice-Plan aktiv) → `done/` (geliefert).
Wird ein Eintrag verworfen, wandert er nach `docs/archive/`.

---

## 3. Konsequenzen

- Das Lastenheft bleibt die Quelle fuer Anforderungen
  (`GG-*`-Kennungen).
- Die Architektur beschreibt Verantwortungsgrenzen und technische
  Leitplanken (`GG-AR-*`-Kennungen).
- ADRs dokumentieren **Entscheidungen**, nicht laufende Diskussionen.
  Offene Punkte aus `architecture.md §19` (`GG-AR-OPEN-*`) wandern bei
  Entscheidung in einen ADR und werden in `architecture.md` mit
  ADR-Verweis als geschlossen markiert.
- Roadmap-Dokumente in `in-progress/` verfolgen Status, Reihenfolge und
  Abnahmeschnitte. Sie liefern spaeter die Meilenstein-Marker (`M1`,
  `M2`, …) fuer Lastenheft §27.2.
- Offene Punkte werden nicht in abgeschlossenen Plaenen versteckt,
  sondern unter `docs/plan/planning/open/` sichtbar gehalten.
- `docs/user/` ist explizit getrennt von Plaenen; Runbooks und
  Bedienanleitungen sind keine Architekturartefakte.
- `docs/archive/` ist explizit getrennt von `done/`: archiviert =
  verworfen oder ueberholt; done = umgesetzt.

---

## 4. Pflege-Regeln

- Neue fachliche Anforderungen erhalten eine `GG-*`-Kennung im
  Lastenheft.
- Neue Architekturartefakte erhalten eine `GG-AR-*`-Kennung in
  `architecture.md` und werden in Lastenheft §27.1 verknuepft.
- Neue technische Entscheidungen erhalten eine ADR, wenn sie
  langfristige Auswirkungen haben oder einen `GG-AR-OPEN-*` schliessen.
- Jeder Plan in `in-progress/` muss Akzeptanzkriterien und einen
  Verifikationspfad enthalten.
- Abgeschlossene Plaene wandern nach `done/` mit kurzer
  Closure-Notiz (was wurde geliefert, was bleibt offen).
- Offene Trigger bleiben in `open/`, bis sie zu einem skizzierten
  Scope werden (→ `next/`), direkt aktiviert (→ `in-progress/`)
  oder verworfen (→ `archive/`) werden.
- Eintraege in `next/` werden aktiviert (→ `in-progress/`),
  zurueckgestuft (→ `open/`) oder verworfen (→ `archive/`).
- ADRs werden nach Erstellung nicht inhaltlich ueberschrieben; spaetere
  Aenderungen kommen als neue ADR mit Verweis auf den abgeloesten
  Vorgaenger.

---

## 5. Nicht Gegenstand dieser ADR

- Wahl der Programmiersprache und des Build-Systems
  ([`GG-AR-OPEN-001`](../../../spec/architecture.md#19-offene-architektonische-punkte), eigene Folge-ADR).
- Trennung von API- und Simulationsdienst ([`GG-AR-OPEN-002`](../../../spec/architecture.md#19-offene-architektonische-punkte)).
- Persistenzzugriffsmuster ([`GG-AR-OPEN-003`](../../../spec/architecture.md#19-offene-architektonische-punkte)).
- Konkrete Pfade fuer Test-Artefakte, Container-Images oder
  Release-Pipelines.
