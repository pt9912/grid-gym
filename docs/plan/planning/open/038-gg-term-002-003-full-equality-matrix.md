# 038 — Volle `GG-TERM-002/003`-Equality-Matrix (1b-Carveout)

**Status:** Open — dokumentierter Scope-Carveout aus M7-Welle-1b
**Datum:** 2026-06-09
**Quelle:** M7-Welle-1b-a-C0 (Decision 1b-a-D-6;
[`docs/plan/planning/done/M7-welle-1b-a.md`](../done/M7-welle-1b-a.md)).

---

## Lastenheft-Akzeptanz

`GG-TERM-002` (Determinismus) + `GG-TERM-003` (Reproduzierbarkeit)
sind normative Begriffsdefinitionen
([`spec/lastenheft.md`](../../../../spec/lastenheft.md)):

> **GG-TERM-002:** Determinismus bedeutet: Bei gleicher Version,
> gleicher Plattformarchitektur, gleichen Eingabedaten, gleicher
> Szenario-Datei, gleicher Konfiguration und gleichem Seed erzeugt
> ein Simulationslauf dieselben fachlichen Ausgaben in derselben
> Tick-Reihenfolge.
>
> **GG-TERM-003:** … speichert alle zur Wiederholung notwendigen
> Metadaten, mindestens Version, Szenario-Hash, Konfiguration,
> Startzeit im Simulationszeitmodell, Seed, Tick-Groesse und
> aktivierte Adapter.

Der *testbare* Determinismus-Vertrag traced auf `GG-AR-P-008`
(`GG-SIM-001/002/003`, `GG-RT-002`); `GG-TERM-002/003` liefern die
normative Feld-/Akzeptanz-Definition (n/a in der Impl-Matrix,
Lastenheft Z. 2203).

## Carveout-Stand (M7-Welle-1b-a-C0 2026-06-09)

M7-Welle-1b implementiert per **1b-a-D-6** nur einen **MVP-E2E-
Replay-Preflight** ueber die bereits stabil strukturierten
`RunMetadata`-Felder:

- ✓ `scenario_hash`
- ✓ `schema_version`
- ✓ `seed`
- ✓ `tick_ms`
- ✓ `tool_version`

Preflight-Vertrag (formal in ADR 0049, 1b-b): „Replay-Diff wird
nur ausgefuehrt, wenn die vorhandenen deterministischen
Vergleichsmetadaten gleich sind; fehlende Vollfelder bleiben als
dokumentierter `GG-TERM-002/003`-Carveout offen." Boundary-Pins
einzeln fuer die 5 Felder (1b-b).

## Offene Vollfelder (dieser Trigger)

Die folgenden Lastenheft-Pflichtfelder sind **noch nicht**
strukturiert in `RunMetadata` verankert und damit **nicht** im
1b-Preflight:

- ✗ **Plattformarchitektur** (`platform_arch`).
- ✗ **Aktivierte Adapter / Adapterprofile** (`enabled_adapters`).
- ✗ **Startzeit im Simulationszeitmodell** (`sim_start_time`) —
  heute nur Wall-Clock `started_at`/`ended_at`
  (`src/grid_gym/hexagon/core/domain/run.py`), nicht
  Simulationszeit.
- ✗ **Separater kanonischer Konfigurations-Hash** (`config_hash`)
  ueber `scenario_hash` hinaus.

## Substanz-Skizze (bei Aufloesung)

- `RunMetadata`-Erweiterung **oder** NEU `ReplayComparisonMetadata`-
  Envelope (Speicherort-Entscheidung im aufloesenden C0).
- Alembic-Migration fuer die neuen Felder.
- Canonicalization-Regeln (`platform_arch`-Normalform,
  `enabled_adapters`-Sortier-Kanonik, `sim_start_time`-Format,
  `config_hash`-Hash-Verfahren) — Reject-Semantik fuer fehlende/
  abweichende Werte **vor** Diff-Klassifikation.
- Parametrisierte Boundary-Tests pro Vollfeld (ein generischer
  Mismatch-Test reicht nicht).
- ADR-0011-Schaerfung an ADR 0049 (additiv zum Preflight-
  Vertrag, kein Bruch).

## Wandert nach

`done/`, sobald die volle `GG-TERM-002/003`-Matrix strukturiert,
kanonisiert und per-Feld-Boundary-getestet im Replay-Preflight
verankert ist.

## References

- [`../done/M7-welle-1b-a.md`](../done/M7-welle-1b-a.md)
  — 1b-a-D-6 (Equality-Scope-Beschluss + Carveout-Begruendung).
- [`../in-progress/M7-welle-1.md`](../in-progress/M7-welle-1.md)
  — GG-MVP-002-Gruppenplan (§2.5 + R4 auf Preflight korrigiert).
- [`../../../../spec/lastenheft.md`](../../../../spec/lastenheft.md)
  — `GG-TERM-002`/`GG-TERM-003` normative Definitionen.
- [`../../adr/0011-schaerfung-ohne-abloesung.md`](../../adr/0011-schaerfung-ohne-abloesung.md)
  — Schaerfungs-Pattern fuer die additive Vollausbau-ADR.
