# 084 — Bezug-Drift-Fix: ARCH-007/008-Vollständigkeit + SCN-006-Lücke

**Status:** Open — geplant (Migrations-Arc Spec-Schichtung, Slice 2 von 4).
**Datum:** 2026-07-16
**Quelle:** [`ADR 0080`](../../adr/0080-three-layer-spec-model.md) §4.4 Schritt
**(ii)** „Bezug-Spalten-Drift beheben (ARCH-007/008 + SCN-006-Lücke)" — eine der
**zwei durchgehenden Prerequisites** (ADR §4, Schluss). Reihenfolge nach
Owner-Entscheidung ADR-treu **(i) vor (ii)**: nach dem Residuum-Umzug
[`083`](../next/083-spezifikation-layer-discipline-core-move.md).

---

## Kontext

Damit `traceability.md` §27.1 von „handgepflegt" zu „ableitbar/gegatet" werden
kann (ADR §2d, Ziel von Slice 086), müssen die **Aufwärts-Zeiger** in
`architecture.md` (die „Bezug"-Spalten) zuerst **vollständig und konsistent**
sein. Heute driften sie gegen §27.1 — die Rückwärts-Map ist unvollständig
gegenüber den Aufwärts-Zeigern. **Lehre (bestätigt beim Grounding):** gegen die
`architecture.md`-Bezug-Spalten grounden, **nicht nur** gegen die RTM.

Dieser Slice berührt **nur** `architecture.md` + `traceability.md`; **kein**
Vertrag-Cut, **keine** neue Datei. Er betrifft ausschließlich die
**nicht-umziehenden** IDs
[`GG-ARCH-007`](../../../../spec/lastenheft.md#gg-arch-007)/[`GG-ARCH-008`](../../../../spec/lastenheft.md#gg-arch-008)
+ [`GG-SCN-006`](../../../../spec/lastenheft.md#gg-scn-006) und ist damit disjunkt
zu 083.

## Betroffene Kennungen

- [`GG-ARCH-007`](../../../../spec/lastenheft.md#gg-arch-007) (Clock-Port/Zeitmodell),
  [`GG-ARCH-008`](../../../../spec/lastenheft.md#gg-arch-008) (geteilter Tick-Loop) —
  bleiben im Vertrag.
- [`GG-SCN-006`](../../../../spec/lastenheft.md#gg-scn-006) (Szenario-Fault-Injection)
  — bleibt im Vertrag.
- Berührte Design-Artefakte:
  [`GG-AR-COMP-CORE`](../../../../spec/architecture.md#5-komponentensicht),
  [`GG-AR-COMP-FAULTS`](../../../../spec/architecture.md#5-komponentensicht),
  [`GG-AR-COMP-SCENARIO`](../../../../spec/architecture.md#5-komponentensicht),
  [`GG-AR-P-006`](../../../../spec/architecture.md#2-architekturprinzipien)/[`GG-AR-P-007`](../../../../spec/architecture.md#2-architekturprinzipien),
  [`GG-AR-PORT-DRN-001`](../../../../spec/architecture.md#driven-ports-vom-kern-aufgerufen),
  [`GG-AR-TABU-005`](../../../../spec/architecture.md#architektur-tabus-build-architekturtest).

## Belegte Drift (Grounding 2026-07-16)

1. **ARCH-007/008 — §27.1 unvollständig.** `architecture.md` verortet sie
   **mehrfach** aufwärts:
   - [`GG-ARCH-007`](../../../../spec/lastenheft.md#gg-arch-007) →
     [`GG-AR-COMP-CORE`](../../../../spec/architecture.md#5-komponentensicht) (§5 Z. 306),
     [`GG-AR-P-006`](../../../../spec/architecture.md#2-architekturprinzipien) (§2 Z. 45),
     [`GG-AR-PORT-DRN-001`](../../../../spec/architecture.md#driven-ports-vom-kern-aufgerufen) (Z. 236),
     [`GG-AR-TABU-005`](../../../../spec/architecture.md#architektur-tabus-build-architekturtest) (Z. 292),
     §9-Zeile (Z. 544).
   - [`GG-ARCH-008`](../../../../spec/lastenheft.md#gg-arch-008) →
     [`GG-AR-COMP-CORE`](../../../../spec/architecture.md#5-komponentensicht) (§5 Z. 306),
     [`GG-AR-P-007`](../../../../spec/architecture.md#2-architekturprinzipien) (§2 Z. 46),
     §9-Zeile (Z. 549).

   `traceability.md` §27.1 spiegelt nur einen Teil (007 → PORT-DRN-001 + TABU-005;
   008 → P-007) und **verschweigt** die
   [`GG-AR-COMP-CORE`](../../../../spec/architecture.md#5-komponentensicht)- und
   [`GG-AR-P-006`](../../../../spec/architecture.md#2-architekturprinzipien)-Kante.
2. **SCN-006 — fault-seitig unverzeichnet.**
   [`GG-AR-COMP-FAULTS`](../../../../spec/architecture.md#5-komponentensicht)-Bezug
   (§5 Z. 311) listet nur
   [`GG-FAULT-001`](../../../../spec/lastenheft.md#gg-fault-001)..010. Die
   Szenario-Fault-Injection
   ([`GG-SCN-006`](../../../../spec/lastenheft.md#gg-scn-006)) wird heute
   scenario-seitig verzeichnet (§12.2 Validierungs-Pipeline, Z. 634; **§13
   Fault-Injection-Architektur, Z. 656, nennt SCN-006 nur in Prosa, nicht als
   strukturierten `Bezug`-Zeiger**); die fault-seitige Realisierung ist als
   [`GG-AR-COMP-FAULTS`](../../../../spec/architecture.md#5-komponentensicht)-Bezug-Zeiger
   „sekundär und unverzeichnet" (ADR §2d).

## Umfang / Erwartete Lieferung

1. **SCN-006-Lücke normativ schließen** in `architecture.md`:
   [`GG-SCN-006`](../../../../spec/lastenheft.md#gg-scn-006) in die
   [`GG-AR-COMP-FAULTS`](../../../../spec/architecture.md#5-komponentensicht)-Bezug-Spalte
   (§5 Z. 311) aufnehmen.
   [`GG-SCN-006`](../../../../spec/lastenheft.md#gg-scn-006) bleibt zugleich via
   [`GG-AR-COMP-SCENARIO`](../../../../spec/architecture.md#5-komponentensicht)
   gedeckt → **kein Orphan** (ADR §2d).
2. **ARCH-007/008-Vollständigkeit sichern:** prüfen, dass jede realisierende
   `architecture.md`-Kante konsistent ist, und die **§27.1-Zeilen** für
   [`GG-ARCH-007`](../../../../spec/lastenheft.md#gg-arch-007)/[`GG-ARCH-008`](../../../../spec/lastenheft.md#gg-arch-008)
   so vervollständigen, dass sie **jeden** Aufwärts-Zeiger erfassen (inkl.
   [`GG-AR-COMP-CORE`](../../../../spec/architecture.md#5-komponentensicht)).
   Richtung: architecture.md ist Quelle, §27.1 folgt.
3. **§27.1-Zeile für** [`GG-SCN-006`](../../../../spec/lastenheft.md#gg-scn-006)
   entsprechend ergänzen (bislang nur
   [`GG-SCN-001`](../../../../spec/lastenheft.md#gg-scn-001)..008 →
   [`GG-AR-COMP-SCENARIO`](../../../../spec/architecture.md#5-komponentensicht)):
   die Fault-Komponenten-Kante aufnehmen.

## Verifikationspfad

- `make docs-check` grün (`anchors`/`links`/`matrix`).
- **Konsistenz-Prüfung (Vorgriff auf 086):** jede §27.1-Zeile für
  ARCH-007/008/SCN-006 nennt **die vollständige Menge** ihrer realisierenden
  `architecture.md`-Bezug-Zeiger (ARCH-007 hat deren fünf → **1:N**, nicht 1:1).
  Der Abgleich gilt **nur für diese Anforderungs-Zeilen**, nicht für alle
  architecture-Zeiger (Spec-Zwischenknoten haben keine eigene §27.1-Zeile, s. 086).
  Dieser Slice stellt die Quelle so sauber, dass das spätere Konsistenz-Gate (086)
  sie akzeptiert.

## DoD

- [`GG-AR-COMP-FAULTS`](../../../../spec/architecture.md#5-komponentensicht)-Bezug
  nennt [`GG-SCN-006`](../../../../spec/lastenheft.md#gg-scn-006); §27.1 spiegelt es.
- §27.1-Zeilen ARCH-007/008 vollständig ggü. allen architecture.md-Zeigern.
- **Release-Entscheidung: nein.** Reine architecture/RTM-Hygiene, kein
  Runtime-Delta → `[Unreleased]`.

## Wandert nach

- `in-progress/` bei Aktivierung, dann `done/`.

## Bezug

- [`ADR 0080`](../../adr/0080-three-layer-spec-model.md) §2d + §4.4 (ii),
  „Zwei durchgehende Prerequisites".
- Vorgänger [`083`](../next/083-spezifikation-layer-discipline-core-move.md),
  Nachfolger [`085`](085-spezifikation-layer-qs-families-move.md) /
  [`086`](086-traceability-derived-27-1-finalization.md).
- [`spec/architecture.md`](../../../../spec/architecture.md) §2/§5/§9/§12.2,
  [`docs/plan/traceability.md`](../../traceability.md) §27.1.
