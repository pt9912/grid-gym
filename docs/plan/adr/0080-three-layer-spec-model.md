# ADR 0080 — Dreischicht-Spezifikationsmodell (Lastenheft / Spezifikation / Architektur)

**Status:** Proposed (2026-07-15) — Entscheidungsvorlage. **Keine Migration in diesem
ADR**; die Umsetzung erfolgt nach Annahme in Folge-Slices. Adressiert die **Wurzel** der
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
[`GG-COV-001`](../../../spec/lastenheft.md#gg-cov-001) „*Mindest-Testabdeckung 90 %*",
[`GG-QG-002`](../../../spec/lastenheft.md#gg-qg-002) „*Security-Gate*"): `GG-QA-*` /
`GG-QG-*` / `GG-COV-*` / `GG-TESTTYPE-*` / `GG-ARCHTEST-*`. Die genaue Grenze zieht die
Migration (§4.2), nicht dieser ADR.

**(2) Ihre Realisierung ist heimatlos.** Weil diese Familien im Vertrag als „Anforderung"
stehen, aber kein Architektur-Artefakt sind, landet ihre Realisierung (z. B.
[`GG-PRINC-005`](../../../spec/lastenheft.md#gg-princ-005) → „ISP wird per `ruff PLR0904`
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
Kundensache) — Grenzfall, in der Migration final zu ziehen (§4).

**(c) SDP-Rang** wird `contract > spezifikation > architektur > adr > slice`. Jede Schicht
verfeinert die darüber und verweist **aufwärts** (SDP-konform). `architecture.md` verweist
künftig auf die Spezifikations-Schicht statt direkt auf den Vertrag, wo es Spec-Ebene betrifft.

**(d) Traceability wird Schicht-Verfeinerung.** Weil jede Spezifikation aufwärts auf ihre
Anforderung und jedes Architektur-Artefakt aufwärts auf seine Spezifikation zeigt, wird die
Anforderung→Design-Kette aus den Aufwärts-Zeigern **ableitbar** — **sofern** die
architecture.md-Bezug-Spalten dafür zuvor vollständig und korrekt gemacht werden (heute
nicht: ARCH-007/008-Drift + die SCN-006-Lücke); diese Vorarbeit ist Teil der Migration.
Damit hört §27.1 auf, eine handgepflegte Parallel-Karte zu sein — es wird abgeleitet oder
gegen die Schicht-Zeiger gegated (Generator vs. Gate → §4). Die 3 falsch platzierten
§27.1-Annotationen aus Commit `0318ce1` (2 redundant, 1 fehlplatziert) sind **bereits
zurückgenommen** (eigener Commit, unabhängig von diesem ADR); die eine echte Lücke
(Szenario-Fault-Injection → Fault-Komponente, heute nur sekundär und unverzeichnet) wird in
der Migration **normativ in architecture.md** geschlossen —
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

## 4. Offene Detailfragen (in der Migrations-Planung zu entscheiden)

1. **`protocol_profiles.md`**: als Abschnitt in die Spezifikations-Schicht einschmelzen oder
   Geschwister-Dokument innerhalb der Schicht? (Beeinflusst die
   `technik`→`spezifikation`-Klassen-Umbenennung.)
2. **Familien-Grenzziehung.** (a) Scope-Familien (`GG-TERM-*` / `GG-MVP-*` /
   `GG-NONGOAL-*` / `GG-FUTURE-*`): Vertrag oder Spezifikation? Vorschlag: Vertrag (Scope =
   Kundensache), außer `GG-SEED-*` (Test-Konvention → Spezifikation). (b) Abnahmekriterium-
   Familien (`GG-QA-*` / `GG-QG-*` / `GG-COV-*` / `GG-TESTTYPE-*` / `GG-ARCHTEST-*`, §1):
   ganz in die Spezifikation, oder Abnahme-*Schwelle* im Vertrag + Durchsetzungs-*Mechanik*
   in der Spezifikation? Der harte Kern `GG-PRINC-*` / `GG-CC-*` ist unstrittig Spezifikation.
3. **Kennungs-Präfixe**: bestehende IDs (`GG-PRINC-*` …) beibehalten und nur umziehen
   (weniger Churn) vs. neues `GG-SPEC-*`-Schema. Vorschlag: beibehalten.
4. **§27.1-Ausbaustufe**: voller Generator (§27.1 wird Build-Artefakt) vs. Konsistenz-Gate
   (kuratiert, aber gegen die Schicht-Zeiger gepinnt).
5. **Offene Spec-Punkte**: analog `GG-AR-OPEN-*` (Architektur) eine offene-Punkte-Sektion in
   der Spezifikations-Schicht.

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

Nach Annahme in Folge-Slices (nicht in diesem ADR), Vertrag atomar/zuletzt. Reihenfolge und
§27.1-Ausbaustufe gemäß §4 in der Slice-Planung. Bis dahin bleibt der Status **Proposed**;
`lastenheft.md`/`architecture.md`/`traceability.md` sind unverändert.
