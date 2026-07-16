# ADR 0004 — Kennungsbasierte Querverweise

**Status:** Accepted
**Datum:** 2026-05-14
**Bezug:** [ADR 0001](0001-documentation-and-planning-structure.md),
[ADR 0006](0006-adr-lifecycle-superseding-and-process-corrections.md),
[Lastenheft](../../../spec/lastenheft.md),
[Architektur](../../../spec/architecture.md)
**Aenderungstyp:** Ergaenzung — die Pflege-Regeln in `ADR 0001`
werden durch eine zusaetzliche Konvention ergaenzt; ADR 0001
bleibt inhaltlich unveraendert.

---

## 1. Kontext

Die Spezifikation arbeitet bereits mit positionsunabhaengigen
Kennungsraeumen:

- `GG-*` — Lastenheft-Anforderungen (`GG-SIM-*`, `GG-API-*`, …)
- `GG-AR-*` — Architekturartefakte (`GG-AR-P-*`, `GG-AR-PORT-*`,
  `GG-AR-COMP-*`, `GG-AR-TABU-*`, `GG-AR-OPEN-*`)
- `GG-TRACE-*` — Rueckverfolgbarkeits-Pflichten
- `AC-*` — Architekturtest-Contracts in ADR 0002 (Familie wird mit
  `Accepted` verbindlich)
- ADR-Nummern (`ADR 0001`, …)

Trotzdem tauchen in den bisherigen Artefakten haeufig
Querverweise wie `architecture.md §4.2`, `architecture.md §19`,
`architecture.md §17` oder `lastenheft.md §27.1` auf. Diese
Verweise sind:

- **positionsfragil:** Eine Umnummerierung der Abschnitte (z. B.
  beim Einfuegen eines neuen Kapitels) bricht alle Verweise still.
- **semantisch arm:** `§4.2` sagt nicht, *was* gemeint ist;
  Leser muessen die Zielsektion lesen, um den Bezug zu verstehen.
- **renderer-abhaengig:** Anker in Markdown sind nicht stabil
  (`#42-hexagonale-sicht-driving--driven-ports` haengt am Titel
  und kippt bei jeder Umbenennung; zudem variiert der Slug
  zwischen Renderern).

Die etablierten Kennungen sind dagegen positionsunabhaengig,
selbst-beschreibend und werden bereits in
[`GG-TRACE-001`](../../../spec/lastenheft.md#gg-trace-001)-Matrizen als stabile Referenz verwendet.

---

## 2. Entscheidung

Querverweise zwischen Spezifikations- und Planungsartefakten
nutzen **Kennungen als primaere Referenz**, nicht Abschnittsnummern.

### 2.1 Pflichtregel

Wenn das Referenzziel eine Kennung besitzt (`GG-*`, `GG-AR-*`,
`GG-TRACE-*`, `AC-*`, ADR-Nummer), MUSS die Kennung als Verweis
verwendet werden. Eine Abschnitts-/Paragraphennummer ist als
**Lesbarkeitshilfe in Klammern** zulaessig, traegt aber keine
semantische Last.

Beispiele:

| Statt                              | Besser                                                                         |
| ---------------------------------- | ------------------------------------------------------------------------------ |
| „siehe `architecture.md §4.2`"      | „siehe Tabu-Familie [`GG-AR-TABU-001`](../../../spec/architecture.md#architektur-tabus-build-architekturtest)..008" (optional: „in `architecture.md` §4.2") |
| „`architecture.md §19`"              | die konkret gemeinte Kennung, z. B. „[`GG-AR-OPEN-007`](../planning/open/architecture-open-points.md#gg-ar-open-007) (UI-Architektur)" — §19 listet [`GG-AR-OPEN-001`](README.md#gg-ar-open-001)..010, ein pauschaler §19-Verweis ist mehrdeutig |
| „`lastenheft.md §27.1`"              | „[`GG-TRACE-001`](../../../spec/lastenheft.md#gg-trace-001) (§27.1-Tabelle)"                                                |
| „Komponente in §5"                   | „[`GG-AR-COMP-DEVICES`](../../../spec/architecture.md#5-komponentensicht)"                                                          |
| „Driving-Port in §4.2"               | „[`GG-AR-PORT-DRV-003`](../../../spec/architecture.md#driving-ports-vom-kern-angeboten) (`ReplayPort`)"                                            |

### 2.2 Wenn kein Kennungsraum existiert

Hat das Referenzziel keine etablierte Kennung (z. B.
`architecture.md` §17 „Testarchitektur"), gilt folgende Reihenfolge:

1. **Bevorzugt:** Eine Kennung im passenden Raum **anlegen**
   (Beispielname: [`GG-AR-TEST-001`](../../../spec/architecture.md#17-testarchitektur) fuer Testarchitektur als
   Ganzes — die konkrete Familie und Nummerierung wird beim
   erstmaligen Anlegen in `architecture.md` normiert). Das ist im
   Rahmen der naechsten inhaltlichen Aenderung des betroffenen
   Dokuments zu erledigen — nicht als eigener Big-Bang.
2. **Uebergangsweise:** Inhaltliche Beschreibung plus
   Abschnittsnummer als Klammer-Hilfe: „die Testarchitektur in
   `architecture.md` (§17)". Diese Form ist nur fuer Sektionen
   ohne Kennung erlaubt und nur uebergangsweise, bis (1) erledigt
   ist.

### 2.3 Innerhalb desselben Dokuments

Innerhalb eines Dokuments (z. B. interne Querverweise in
`architecture.md`) gilt dieselbe Regel. Kennungen sind auch hier
gegenueber `§…`-Verweisen vorzuziehen. Die Klammer-Hilfe
(„[`GG-AR-TABU-005`](../../../spec/architecture.md#architektur-tabus-build-architekturtest) (§4.2)") ist zulaessig.

### 2.4 ADRs

ADR-zu-ADR-Verweise nutzen die ADR-Nummer (`ADR 0002`) als
Kennung. Bezugnahmen auf Unterabschnitte einer ADR werden
inhaltlich benannt („Status-Pfad in ADR 0002") statt
positionsabhaengig („ADR 0002 §4"). Kommen mehrere Verweise auf
denselben Unterabschnitt vor, kann die Ziel-ADR optional einen
inhaltlichen Anker einfuehren (z. B. `<!-- anchor:status-pfad -->`
unmittelbar vor der Zielzeile). Diese Anker-Konvention wird hier
neu eingefuehrt; sie ist Konvention, kein Tooling-Vertrag, und
nur dort sinnvoll, wo der inhaltliche Name allein nicht eindeutig
ist.

### 2.5 Externe Links

Markdown-Hyperlinks auf Dateien sind weiterhin erlaubt und
erwuenscht, sofern sie die Kennung im Linktext fuehren:

```markdown
[`GG-AR-OPEN-001`](README.md#gg-ar-open-001)
```

Der URL-Anker ist Konvention, nicht Vertrag — Verweis-Identitaet
liegt im Linktext.

---

## 3. Retrofit-Regel

Bestehende `§…`-Verweise werden nicht in einer Sammelaktion
ersetzt. Statt dessen gilt:

- Beruehrt eine Aenderung ein Dokument inhaltlich, werden die in
  dieser Aenderung sichtbaren `§…`-Verweise auf Kennungen
  umgestellt.
- ADR 0002 (Status `Provisional`) ist ein laufender Beschluss; seine
  `§…`-Verweise werden im Zuge des Spike-0-Schliffs umgestellt,
  spaetestens vor `Accepted`.
- ADR 0001 und der historische Entscheidungstext von ADR 0003 werden
  nicht nachtraeglich umgestellt — die Pflege-Regeln in `ADR 0001`
  verbieten inhaltliche Ueberschreibung. ADR 0003 darf nur per
  Superseding-Metadaten auf ADR 0006 zeigen; die aktive
  Lifecycle-Regel lebt ab dann in ADR 0006.
- Lastenheft und Architektur werden mit jeder inhaltlichen
  Aenderung gemaess obiger Regel sukzessive umgestellt,
  spaetestens jeweils bei der naechsten Minor-Versions-Hebung
  (heute `lastenheft.md` 0.8, `architecture.md` 0.1.0).

---

## 4. Konsequenzen

- Neue Spezifikations- und Planungsinhalte verwenden ausschliesslich
  Kennungs-Verweise.
- Wenn beim Schreiben eines Verweises auffaellt, dass die Ziel-
  Sektion noch keine Kennung hat, wird die Kennung im selben
  Edit eingefuehrt (siehe Regel fuer Ziele ohne Kennung).
- Dokumentations-Tooling (z. B. ein moeglicher
  `tools/check_refs.py` als Folgearbeit) kann spaeter ueber die <!-- d-check:ignore (historisch: check_refs abgeloest durch d-check, 766ae8c) -->
  Kennungen einen Index erzeugen und nicht aufgeloeste Verweise
  melden.
- Die Pflege-Regeln in `ADR 0001` bleiben unveraendert; diese
  ADR fuegt eine spezialisierte Pflege-Regel hinzu,
  ueberschreibt aber nichts.

---

## 5. Nicht Gegenstand dieser ADR

- Konkrete Linter-Implementierung fuer Querverweise (eigener
  Folge-ADR oder einfach `tools/check_refs.py` als Routinearbeit). <!-- d-check:ignore (historisch: check_refs abgeloest durch d-check, 766ae8c) -->
- Renaming-Regeln fuer Kennungen (Kennungen sind unveraenderlich,
  sobald veroeffentlicht — ohnehin Konvention der `GG-*`-Familie).
- HTML-/PDF-Rendering, Cross-Reference-Erzeugung in einem
  Dokumentations-Build.
