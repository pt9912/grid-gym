# 088 — §27.1 `authored → derived` (Traceability-Ausbaustufe)

**Status:** Open — **umgeschnitten 2026-07-17** nach dem
[`ADR 0080`](../../adr/0080-three-layer-spec-model.md)-§4.4-4-Amendment: Das
Konsistenz-**Gate** (Stufe iii) ist **gestrichen**, der **Generator** (Stufe iv) von
*optional* auf verbindlich vorgezogen. Die d-check-Fähigkeit aus
[`CR 089`](089-dcheck-design-consistency-gate-cr.md) ist geliefert und verifiziert —
sie wird aber **nicht verdrahtet**, sondern einmalig als Messinstrument benutzt.
**Datum:** 2026-07-16 (umgeschnitten 2026-07-17)
**Quelle:** [`Slice 086`](../done/086-traceability-derived-27-1-finalization.md) —
die `§27.1 authored → derived`-Ausbaustufe aus
[`ADR 0080`](../../adr/0080-three-layer-spec-model.md) §2d.

---

## Kontext

Die [`traceability.md`](../../traceability.md) §27.1-Design-Tabelle ist eine
**kuratierte, gegroundete Vorwärts-Map** (Anforderung → implementierende
`GG-AR-*`-Artefakte) — **kein** vollständiger Spiegel der aufwärts zeigenden
`architecture.md`-Bezug-Kanten. Das ist keine Schwäche, sondern ihre erklärte Form:
§27.1 nennt das **Haupt**-Artefakt, die Bezug-Kanten nennen **jede** Berührung.

Ein **dauerhaftes** Set-Gate zwischen beiden (die ursprüngliche Stufe iii) ist deshalb
unbrauchbar. Belegt an den Realdaten mit d-check v0.45.1 (advisory-Lauf, Config unten):
**161 Differenzen = 86 `F\B` + 75 `B\F`** — davon sind **65 der 75 `B\F` Absicht**
(Ports 40, Prinzipien 19, 6 Komponenten, die §27.1 als Nicht-Haupt-Artefakt weglässt;
Kriterium: ihr `F\B` ist leer, das Haupt-Artefakt also gematcht — die Rück-Kante ist
reiner Überschuss). `mode: equal` bliebe damit dauerhaft rot, solange §27.1 kuratiert
bleibt; grün würde es erst, wenn §27.1 exakter Spiegel ist — und dann ist es die Ausgabe
des Generators.

**Die restlichen 10 `B\F` sind aber keine Absicht** und gehören in die Arbeitsliste:

- **6× erfundene Kanten:** [`GG-AR-COMP-DEVICES`](../../../../spec/architecture.md#5-komponentensicht)
  verweist per [`GG-DEV-001`](../../../../spec/lastenheft.md#gg-dev-001)`..018` zurück auf
  die Nummern 004–009 dieser Familie — **die es nicht gibt** (der Vertrag springt von `003`
  auf [`GG-DEV-010`](../../../../spec/lastenheft.md#gg-dev-010); die Range überspannt die
  Lücke). Ein Generator erzeugte daraus §27.1-Zeilen für Phantom-Anforderungen — die
  [`ADR 0080`](../../adr/0080-three-layer-spec-model.md)-Sorge „Generator auf driftender
  Quelle produziert selbstbewusst Falsches" ist hier **belegt**, nicht widerlegt.
- **2× echte Drift** (Schnittmenge null — das Kriterium aus
  [`CR 089`](089-dcheck-design-consistency-gate-cr.md) §1): (a)
  [`GG-ARCH-005`](../../../../spec/lastenheft.md#gg-arch-005) — §27.1 nennt `COMP-CORE`/
  `COMP-DOMAIN`, zurück verweisen nur
  [`GG-AR-COMP-SCHED`](../../../../spec/architecture.md#5-komponentensicht)/`P-005`/`P-009`;
  (b) [`GG-SIM-009`](../../../../spec/lastenheft.md#gg-sim-009) — §27.1 nennt `COMP-DOMAIN`
  (`RunMetadata`)/`COMP-PERSIST` (Schema), aber keiner der beiden verweist zurück; die
  einzige Rück-Kante kommt von `COMP-CORE` per Pauschal-Range
  [`GG-SIM-001`](../../../../spec/lastenheft.md#gg-sim-001)`..009`.
- **2× Werkzeug-Artefakt:** d-check verschluckt die Komma-Aufzählung in
  [`GG-SCN-001`](../../../../spec/lastenheft.md#gg-scn-001)`..005, 007, 008` (§27.1) still →
  [`GG-SCN-007`](../../../../spec/lastenheft.md#gg-scn-007)/008 erscheinen fälschlich als
  `B\F`. **An d-check gemeldet**; trifft auch das produktiv verdrahtete `trace.coverage`
  (leere `Trace`-Spalte für beide IDs trotz Mapping).

Begründung der Entscheidung: §4.4-4-Amendment.

## Mess-Config (ohne sie sind die Zahlen nicht reproduzierbar)

Nicht in `.d-check.yml` — der Block wird für den Einmal-Lauf temporär unter `trace:`
eingehängt und danach wieder entfernt:

```yaml
  cross-consistency:
    forward:
      file: docs/plan/traceability.md
      sections: ["27.1 Anforderung zu Design"]
      exclude-sections: ["27.1.1 Anforderungen ohne Design-Artefakt"]
      req-column: "Lastenheft-Kennung"
      design-column: "Design-Artefakt"
      design-pattern: 'GG-AR-[A-Z0-9-]+'
      req-pattern: 'GG-[A-Z]+-\d{3}'      # trennt Vergleichs- von RTM-Scope (v0.45.0)
      ranges: true
    backward:
      file: spec/architecture.md
      sections: ["2. Architekturprinzipien", "4.2 Hexagonale Sicht (Driving / Driven Ports)", "5. Komponentensicht"]
      artifact-id-column: first
      edge-column: Bezug
      req-pattern: 'GG-[A-Z]+-\d{3}'
      ranges: true
    mode: equal
    exclude-req: 'GG-(PRINC|CC|SEED|QA|QG|COV|TESTTYPE|ARCHTEST)-\d+'
```

Die Zahlen sind config-abhängig (ohne `exclude-req` 169, mit engerem `design-pattern` 159)
— sie gelten nur für genau diesen Block. **`17. Testarchitektur` fehlt bewusst in
`backward.sections`:** d-check bricht dort hart ab (`spec/architecture.md:913`,
„Tabellenzeile hat 4 statt 3 Zellen" — der `<!-- d-check:ignore -->`-Marker wird als
4. Zelle gezählt). An d-check gemeldet; blockiert Lieferpunkt (1).

## Erwartete Lieferung (amendiert)

1. **Bezug-Reinigung (§2d-Vorbedingung, repo-lokal, JETZT baubar).** Der
   `cross-consistency`-Abgleich wird **einmalig** als Messinstrument gefahren. Arbeitsliste
   sind **beide** Richtungen: die **85 echten `F\B`** (86 minus 1 Wildcard-Phantom) über
   62 Anforderungen — darunter 26 Fälle, in denen §27.1 auf `GG-AR-TEST-*` zeigt, das in
   `architecture.md` gar keine Artefakt-Zeile trägt — **und die 8 echten `B\F`** (6×
   Phantom-Kanten der `GG-DEV-*`-Lücke, 2× Drift:
   [`GG-ARCH-005`](../../../../spec/lastenheft.md#gg-arch-005) und
   [`GG-SIM-009`](../../../../spec/lastenheft.md#gg-sim-009)). Kein d-check-Feature nötig
   (`forward.req-pattern` genügt); die §17-Erweiterung ist bis zum d-check-Fix blockiert
   (s. Mess-Config).
2. **Kanten-Anmerkungen umziehen (repo-lokal, JETZT baubar).** Die §27.1-Prosa zieht
   dorthin, wo die Kante lebt: `Bezug`-Zelle, geklammert nach der Kennung bzw. nach der
   Range-Fortsetzung. Titel-Handkopien entfallen ersatzlos (der Generator gibt den
   Artefakt-Titel aus). Notation + verifizierte Grenzen: §4.4-4-Amendment.
3. **Generator (Stufe iv, cross-repo).** §27.1-Positivtabelle nicht mehr gespeichert,
   sondern von `doc-trace` aus den Bezug-Spalten erzeugt (Präzedenz: §27.2-Delegation,
   [`Slice 066`](../done/066-traceability-recut-delegate-27-2.md)). **§27.1.1 bleibt
   kuratiert** (§2d). Die Akzeptanz von
   [`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001) ist dabei zu amendieren
   (Slice-066-Muster) — `derived` ist **nicht** gelöscht, die requirement-indizierte
   Matrix bleibt.

## Aktivierungs-Bedingung

- **(1) + (2) sind nicht mehr blockiert** — sie brauchen kein d-check-Feature und können
  als Slice geschnitten werden.
- **(3)** wartet auf eine Generator-Fähigkeit in Users externem `d-check`
  (ghcr.io/pt9912/d-check), die **den Artefakt-Titel mitausgibt** und die
  **Kanten-Anmerkung durchreicht**. Diese Anforderung ist der Nachfolge-CR zu
  [`CR 089`](089-dcheck-design-consistency-gate-cr.md) (dort §10 als „eigene spätere CR"
  vorgesehen — der Schreib-Pfad, näher an `--repair` als an `--trace`).

## Wandert nach

- (1)+(2) → als Slice nach `next/`/`in-progress/` → `done/`.
- (3) bleibt Trigger-Watch, bis das d-check-Generator-Feature verfügbar ist.

## Bezug

- [`ADR 0080`](../../adr/0080-three-layer-spec-model.md) §2d + §4.4-4 (amendiert),
  [`ADR 0081`](../../adr/0081-open-points-belong-in-planning.md) (offene Punkte → Planung).
- [`Slice 086`](../done/086-traceability-derived-27-1-finalization.md) (Vertagung),
  [`066`](../done/066-traceability-recut-delegate-27-2.md) (Delegations-Präzedenz).
- [`docs/plan/traceability.md`](../../traceability.md) §27.1.
