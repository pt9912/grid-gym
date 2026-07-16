# ADR 0080 — Dreischicht-Spezifikationsmodell (Lastenheft / Spezifikation / Architektur)

**Status:** Accepted (2026-07-15) — Modell angenommen. **Keine Migration in diesem ADR**;
die Umsetzung erfolgt in Folge-Slices (Vertrag zuletzt/atomar). Die §4-Detailfragen sind mit
dem Owner **entschieden** (§4); offen bleibt nur ihre Ausführung in den Migrations-Slices.
Adressiert die **Wurzel** der
wiederkehrenden Traceability-Redundanzen (das entfernte architecture.md §18, die
„Bezug"-Spalten ↔ `traceability.md` §27.1-Spiegelung), indem die fehlende mittlere
Spezifikations-Schicht eingezogen wird.
**Datum:** 2026-07-15
**Bezug:**

- [`ADR 0072`](0072-slice-driven-planning-no-milestones.md) — Präzedenz: strukturelle
  Doku-Entscheidungen werden als ADR getroffen, Umsetzung slice-getrieben.
- [`Slice 063`](../planning/done/063-traceability-doc-auslagern.md) — lagerte §27 aus
  `lastenheft.md` nach `traceability.md` aus (Vertrag frei von Abwärts-Verweisen).
  Präzedenz für Schicht-Bereinigung.
- [`Slice 066`](../planning/done/066-traceability-recut-delegate-27-2.md) — ersetzte die
  handgepflegte §27.2-Liefertabelle durch Ableitung (`make doc-trace`). Präzedenz:
  Traceability wird **abgeleitet**, nicht doppelt gepflegt.
- [`ADR 0004`](0004-identifier-based-cross-references.md) — kennungsbasierte
  Querverweise; jede Schicht referenziert per ID **aufwärts**.
- [`GG-TRACE-001`](../../../spec/lastenheft.md#gg-trace-001) — die
  Rückverfolgbarkeits-Anforderung, deren Akzeptanz bei Umsetzung amendiert werden muss
  (wie in [`Slice 066`](../planning/done/066-traceability-recut-delegate-27-2.md)).

---

## 1. Kontext

Der normative Spec-Satz kennt heute faktisch **zwei** Ebenen für Anforderung↔Design:
`spec/lastenheft.md` (Vertrag, SDP-Klasse `contract`) und `spec/architecture.md` (Sicht,
`sicht`). `spec/protocol_profiles.md` besetzt zwar die mittlere `technik`-Klasse, ist aber
auf Protokollprofile beschränkt — **keine allgemeine Spezifikationsschicht**.

Diese fehlende Mitte erzeugt zwei belegte Struktur-Probleme:

**(1) Der Vertrag vermischt Anforderungs- und Spezifikations-/Qualitätsebene.** ~44
Kennungen im `lastenheft.md` gehören ganz oder teilweise auf die Ebene „*wie/womit wird
spezifiziert und geprüft*" statt „*was der Kunde will*". Die Grenze ist nicht überall
scharf — ein **harter Kern** ist eindeutig Spezifikation, andere Familien haben
**Abnahmekriterium-Charakter** und sind Grenzfälle (finale Zuordnung → §4.2):

| Familie | Zahl | Inhalt |
| --- | --- | --- |
| `GG-PRINC-*` | 6 | SOLID-Prinzipien + Durchsetzung (`ruff`/`mypy`) |
| `GG-CC-*` | 8 | Clean-Code-Konventionen |
| `GG-QA-*` / `GG-QG-*` / `GG-COV-*` | 18 | Qualitätssicherung, Quality-Gates, Coverage |
| `GG-TESTTYPE-*` / `GG-ARCHTEST-*` | 12 | Testarten- und Architektur-Test-Spezifikation |

**Harter Kern** (klar Spezifikation, interne Disziplin): `GG-PRINC-*`, `GG-CC-*`.
**Grenzfall** (auch als Kunden-Abnahmekriterium lesbar — z. B.
[`GG-COV-001`](../../../spec/spezifikation.md#gg-cov-001) „*Mindest-Testabdeckung 90 %*",
[`GG-QG-002`](../../../spec/spezifikation.md#gg-qg-002) „*Security-Gate*"): `GG-QA-*` /
`GG-QG-*` / `GG-COV-*` / `GG-TESTTYPE-*` / `GG-ARCHTEST-*`. Die genaue Grenze entscheidet
§4.2; die Migration führt sie aus.

**(2) Ihre Realisierung ist heimatlos.** Weil diese Familien im Vertrag als „Anforderung"
stehen, aber kein Architektur-Artefakt sind, landet ihre Realisierung (z. B.
[`GG-PRINC-005`](../../../spec/spezifikation.md#gg-princ-005) → „ISP wird per `ruff PLR0904`
durchgesetzt") als **Residuum** in der advisory-RTM `traceability.md` §27.1 — dem einzigen
genuin einzigartigen Inhalt dort.

Dieselbe fehlende Mitte ist die **Wurzel** der Redundanzen, die diese Session aufdeckte:
das (entfernte) §18 spiegelte intern die „Bezug"-Spalten; die „Bezug"-Spalten
(§2/§4/§5/§8/§17) spiegeln §27.1; §27.1 **driftet** gegen sie (belegt:
[`GG-ARCH-007`](../../../spec/lastenheft.md#gg-arch-007)/008 verorten §5-Spalte →
[`GG-AR-COMP-CORE`](../../../spec/architecture.md#5-komponentensicht), §27.1 → Port/Prinzip).
Jede Spec-Sache wird **gespalten**: Anforderungs-Hälfte in den Vertrag,
Realisierungs-Hälfte in Architektur-Bezug/RTM.

## 2. Entscheidung

Eine mittlere **Spezifikations-Schicht** einziehen (im Folgenden **Spezifikation**;
entspricht dem V-Modell-*Pflichtenheft*):

```
lastenheft.md      Lastenheft    (WAS / contract)      — nur echte Anforderungen
spezifikation.md   Spezifikation (WIE-funktional/QS)   — Prinzipien, Konventionen, QS/Gates, Testarten
architecture.md    Architektur   (WIE-strukturell)     — nur GG-AR-*
```

Kernpunkte:

**(a) Neues Dokument** `spec/spezifikation.md` <!-- d-check:ignore (geplant: entsteht mit der Migration nach Annahme dieses ADR) -->.
Es verallgemeinert die bislang unterbenutzte `technik`-Klasse; `spec/protocol_profiles.md`
wird Teil dieser Schicht (Detail → §4).

**(b) Umzug der Qualitäts-/Durchsetzungs-Familien** (`GG-PRINC-*`, `GG-CC-*`, `GG-QA-*`,
`GG-QG-*`, `GG-COV-*`, `GG-TESTTYPE-*`, `GG-ARCHTEST-*`) aus `lastenheft.md` in die
Spezifikations-Schicht. Ihre Realisierung (Durchsetzungs-Werkzeug, Gate) wird **dort
erstklassig** dokumentiert — nicht mehr als RTM-Residuum. Reine Scope-/Definitions-Familien
(`GG-TERM-*`, `GG-MVP-*`, `GG-NONGOAL-*`, `GG-FUTURE-*`) bleiben im Vertrag (Scope ist
Kundensache) — final entschieden in §4.2 (`GG-SEED-*` ausgenommen: → Spezifikation).

**(c) SDP-Rang** wird `contract > spezifikation > architektur > adr > slice`. Jede Schicht
verfeinert die darüber und verweist **aufwärts** (SDP-konform). `architecture.md` verweist
künftig auf die Spezifikations-Schicht statt direkt auf den Vertrag, wo es Spec-Ebene betrifft.

**(d) Traceability wird Schicht-Verfeinerung — §27.1 wechselt von `authored` zu `derived`.**
Weil jede Spezifikation aufwärts auf ihre Anforderung und jedes Architektur-Artefakt aufwärts
auf seine Spezifikation zeigt, wird die Anforderung→Design-Kette aus den Aufwärts-Zeigern
**ableitbar** — **sofern** die architecture.md-Bezug-Spalten dafür zuvor vollständig und
korrekt gemacht werden (heute nicht: ARCH-007/008-Drift + die SCN-006-Lücke); diese Vorarbeit
ist Teil der Migration. Damit hört §27.1 auf, eine **handgepflegte Quelle** zu sein.

Die requirement-indizierte **Sicht** selbst bleibt jedoch nötig und wird **nicht gelöscht**
(Löschen verletzte [`GG-TRACE-001`](../../../spec/lastenheft.md#gg-trace-001), s. §5): eine
Verfeinerungs-**Schicht** ist kein Vollständigkeits-**Index**. Die Schicht-Zeiger zeigen
*aufwärts* (Design→Anforderung); Abnahme/Audit und Waisen-Erkennung brauchen das *Inverse*
(Anforderung→Design + „welche Anforderung hat *gar kein* Design"), das erst durch Aufzählen
der Anforderungsliste sichtbar wird. `spezifikation.md` liefert diese Sicht daher nicht — es
ist die Schicht, nicht ihr Index. §27.1 überlebt folglich als **Ableitung/Gate** gegen die
Schicht-Zeiger (Ausbaustufe → §4.4). **§27.1.1** („Anforderungen ohne Design-Artefakt") bleibt
hingegen **kuratiert**: dass eine Waise *gewollt* ist (`GG-TERM-*` / `GG-NONGOAL-*` mappen
bewusst auf nichts), ist menschliches Urteil, kein invertierter Zeiger — ein Werkzeug erkennt
Waisen, erklärt sie aber nicht.

Die 3 falsch platzierten §27.1-Annotationen aus Commit `0318ce1` (2 redundant, 1
fehlplatziert) sind **bereits zurückgenommen** (eigener Commit, unabhängig von diesem ADR);
die eine echte Lücke (Szenario-Fault-Injection → Fault-Komponente, heute nur sekundär und
unverzeichnet) wird in der Migration **normativ in architecture.md** geschlossen —
[`GG-SCN-006`](../../../spec/lastenheft.md#gg-scn-006) bleibt via
[`GG-AR-COMP-SCENARIO`](../../../spec/architecture.md#5-komponentensicht) gedeckt, kein Orphan.

**(e) [`GG-TRACE-001`](../../../spec/lastenheft.md#gg-trace-001) wird amendiert** (wie in
[`Slice 066`](../planning/done/066-traceability-recut-delegate-27-2.md)), um die Dreischicht
+ die abgeleitete/gegatete §27.1 zu beschreiben.

## 3. Konsequenzen

**Positiv:**

- Der Vertrag enthält nur noch echte Anforderungen; jede Kennungs-Familie hat **eine**
  autoritative Heimat.
- Das §27.1-Residuum (Prinzip→`ruff` etc.) wird erstklassige Spezifikation statt
  RTM-Beifang.
- Die Redundanz-Klasse (§18, „Bezug" ↔ §27.1) löst sich **strukturell** auf; Drift wird
  unmöglich, wo Traceability abgeleitet ist.
- Sauberes V-Modell-Schichten; künftige „wohin gehört diese Kennung?"-Fragen haben eine
  klare Antwort.

**Negativ / Kosten:**

- **Vertrags-Eingriff (rank-1).** Die betroffenen IDs (bis zu ~44, je nach
  §4.2-Grenzziehung) verlassen `lastenheft.md`; jeder Verweis darauf (architecture.md-Bezug,
  §27.1/§27.3, ADRs, Slices, Tests, `.d-check.yml` `ids`/`matrix`/`trace`-Muster,
  [`GG-TRACE-001`](../../../spec/lastenheft.md#gg-trace-001)) muss mitgezogen werden.
- **Gate-blinder Anteil.** ~30 dieser IDs werden in `src/` / `tests/` / `.github/` /
  `pyproject.toml` / `Makefile` referenziert — Pfade, die d-check per `scan.ignore`
  (`src/**`, `.github/**`) und Nicht-Markdown **nicht** prüft. Deren Umzug bricht Verweise,
  die das docs-check-Link-Gate **nicht** fängt → separater manueller Grep-Sweep in der
  Migration nötig.
- Mehrstufige Migration; hoher Blast-Radius; sorgfältig zu sequenzieren (Vertrag
  zuletzt/atomar).
- Zwei d-check-Anpassungen nötig: neue `matrix`-Klasse `spezifikation`; ggf. neue
  Ableitungs-/Gate-Fähigkeit für §27.1.

## 4. Detailentscheidungen (2026-07-15, mit Owner ratifiziert; Ausführung in den Migrations-Slices)

Die bei Annahme offenen Detailfragen sind entschieden. Reihenfolge/Atomarität regelt §6; die
Entscheidungen hier sind die Vorgaben, an denen sich die Migrations-Slices ausrichten.

1. **`protocol_profiles.md` → Geschwister-Dokument** (nicht einschmelzen). Die
   Spezifikations-SDP-Klasse wird mehrpfadig: die neue `spezifikation.md` + `protocol_profiles.md`
   (in place, unverändert). Grund: protocol_profiles ist reife, eigen-versionierte
   Wire-Level-Interface-Spec **anderen Wesens** als die Disziplin-/QS-Familien; ein Merge
   erzeugte ein thematisch inkohärentes God-Dokument (nahe `GG-CC-*` „keine God-Utility") bei
   unnötigem Anker-/Link-Churn. `spezifikation.md` verweist *seitwärts* darauf (schicht-intern
   SDP-konform). **d-check:** `matrix`-Klasse `technik` → `spezifikation` mit **beiden** Pfaden
   (`spec/protocol_profiles.md` + die neue `spec`-Datei).
2. **Familien-Grenze.**
   **(a) Scope-Familien:** `GG-TERM-*` / `GG-MVP-*` / `GG-NONGOAL-*` / `GG-FUTURE-*` bleiben
   **Vertrag** (Vokabular + Scope = Kundensache; kein Design-Artefakt, keine Mechanik).
   **Ausnahme `GG-SEED-*` → Spezifikation** — interne Determinismus-/Test-Konvention, Wesen wie
   `GG-CC-*`; der *Kundenwunsch* Determinismus liegt in `GG-SIM-*` / `GG-RT-*`, SEED ist das
   *Wie*. Einziger Grenzfall; ein ID, geringer Churn (§27.1.1-Eintrag entfällt für SEED).
   **(b) Abnahme-Familien** (`GG-QA-*` / `GG-QG-*` / `GG-COV-*` / `GG-TESTTYPE-*` /
   `GG-ARCHTEST-*`): **ganz in die Spezifikation, inkl. Schwellwert — kein per-ID-Split.** Ein
   Split klonte jeden ID über zwei Schichten und reproduzierte exakt die in §1 benannte Wurzel
   (jede Spec-Sache gespalten → Drift) — verworfen. Der Kunden-**Abnahme-Anker** bleibt via
   `GG-ACCEPT-*` + `GG-MVP-*` (E2E-Referenzszenario + Abnahme-CLI) im Vertrag; die verschobenen
   Familien verfeinern ihn aufwärts. Harter Kern `GG-PRINC-*` / `GG-CC-*` ohnehin Spezifikation.
3. **Kennungs-Präfixe: beibehalten** (kein neues `GG-SPEC-*`-Schema). Ein Rename klonte ~30
   **gate-blinde** Referenzen (src/tests/.github/pyproject/Makefile — d-check-`scan.ignore`) für
   null semantischen Gewinn; §3 markiert genau diesen Sweep als teuerste Kosten. Das Präfix
   trägt die Familie; Schicht-Zugehörigkeit = **Datei + `matrix`-Klasse**, nicht Präfix.
   **d-check-Arbeitspaket:** die generische `ids`-Regel `GG-…-NNN` → `lastenheft.md` gilt für
   die verschobenen Präfixe nicht mehr → höher-priorisierte Muster (bzw. eine Alternation) mit
   Ziel `spezifikation.md` für PRINC/CC/QA/QG/COV/TESTTYPE/ARCHTEST/SEED.
4. **§27.1-Ausbaustufe: Konsistenz-Gate zuerst, Generator/Report als Endzustand** (§27.1
   wechselt `authored → derived`, §2d). Reihenfolge: (i) Residuum-Umzug nach `spezifikation.md`;
   (ii) Bezug-Spalten-Drift beheben (ARCH-007/008 + SCN-006-Lücke); (iii) **Konsistenz-Gate** —
   jede §27.1-Zeile ↔ ein Schicht-Zeiger (killt Drift, den *eigentlichen* Defekt); (iv)
   *optional* Promotion zum **Generator/Report** — Positivtabelle nicht mehr gespeichert, sondern
   von `doc-trace` aus den Bezug-Spalten erzeugt (Präzedenz: §27.2-Delegation, Slice 066).
   **Warum Gate zuerst:** die Bezug-Spalten driften heute; ein Generator auf driftender Quelle
   produzierte selbstbewusst Falsches — das Gate erzwingt die Quelle sauber und verdient sich
   damit das Recht zu generieren. **§27.1.1 bleibt kuratiert** (§2d). **d-check:** neue
   Ableitungs-/Gate-Fähigkeit erst für Stufe (iii)/(iv).
5. **[ZURÜCKGENOMMEN — Owner-Entscheidung 2026-07-16 bei der §4.4-i-Umsetzung:**
   `spezifikation.md` beschreibt (wie `lastenheft.md`/`architecture.md`) das *Soll*;
   offene Prozess-/Werkzeug-/Traceability-Punkte gehören in die Planung
   (Roadmap/Slice/Trigger), **nicht** in die normative Spec. Daher `GG-SPEC-OPEN-*`
   + Sektion „Offene Spezifikationspunkte" **nicht eingeführt**; der als Seed
   vorgesehene §27.1-Generator-Punkt ist Traceability-Tooling und wird in der
   Traceability-Finalisierung geführt. Die zugrunde liegende `GG-AR-OPEN-*`/
   architecture.md-§19-Analogie ist aus demselben Grund als aufzulösen markiert
   (eigener Bereinigungs-Slice). Der ursprüngliche §4.5-Text bleibt als Historie
   stehen.]** Offene Spec-Punkte: neue Familie `GG-SPEC-OPEN-*` analog `GG-AR-OPEN-*` (architecture.md
   §19): Sektion „Offene Spezifikationspunkte" in `spezifikation.md` (Tabelle ID | Frage |
   Status; geschlossene Zeilen zitieren die auflösende ADR). Muss in `.d-check.yml`
   `matrix.exclude-sections` (wie „19. Offene architektonische Punkte"), damit geschlossene
   Zeilen ihre ADR *abwärts* zitieren dürfen. **Sofort seeden** mit den hier vertagten
   *Ausführungs*-Punkten (z. B. §27.1-Generator-Promotion nach Bezug-Stabilisierung →
   `GG-SPEC-OPEN-001`). Neuer Präfix ist hier gerechtfertigt (Kontrast zu §4.3): brandneue
   Artefakte **ohne** zu erhaltende Referenzen — wie `GG-AR-OPEN-*` schicht-nativ. In `ids`
   aufnehmen (Ziel `spezifikation.md`); als Meta **außerhalb** des `trace`-`id-pattern` (wie
   ARCH/OPEN heute).

**Zwei durchgehende Prerequisites** (Voraussetzung für *jeden* Slice, insbesondere §4.4):
Residuum-Umzug nach `spezifikation.md` und Behebung der Bezug-Spalten-Drift (ARCH-007/008 +
SCN-006-Lücke) — zugleich das, was das Konsistenz-Gate erzwingt.

## 5. Alternativen (verworfen)

- **Zweischicht beibehalten + nur §27.1 gaten** (Konsistenz-Gate ohne neue Schicht): heilt
  die Drift, aber der Vertrag bleibt überladen und das §27.1-Residuum bleibt heimatlos.
  Behandelt das Symptom, nicht die Wurzel.
- **Zweischicht + §27.1 löschen**: verletzt [`GG-TRACE-001`](../../../spec/lastenheft.md#gg-trace-001) (fordert requirement-indizierte
  Matrix) und verliert das einzigartige Residuum.
- **Spezifikations-*Abschnitt* statt eigenes Dokument** (neue `matrix`-Klasse ohne physisch
  neue Datei, oder ein markierter Abschnitt): kleinerer Datei-Blast-Radius. Löst „Vertrag
  überladen" aber nur, wenn der Abschnitt *aus* `lastenheft.md` herausgezogen wird — dann ist
  es de facto doch ein eigenes Dokument. Ein Abschnitt *innerhalb* des Vertrags behielte die
  Vermischung bei. Verworfen zugunsten klarer Schicht-Trennung.
- **Nichts tun**: die Redundanz/Drift bleibt und wächst mit jeder neuen
  Spec-Ebenen-Kennung.

## 6. Umsetzung

In Folge-Slices (nicht in diesem ADR), Vertrag atomar/zuletzt. Reihenfolge und
§27.1-Ausbaustufe gemäß den §4-Entscheidungen in der Slice-Planung. Der Status ist **Accepted**
(Modell-Entscheidung); die Specs `lastenheft.md`/`architecture.md`/`traceability.md` bleiben
unverändert, bis die Migrations-Slices greifen.
