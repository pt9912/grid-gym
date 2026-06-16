# Welle 3b — Transformatorgrenzen im Netzbilanzmodell (`GG-GRID-006`)

**Status:** Done (M8-Welle-3b, 2026-06-16) — zweite Sub-Welle der Netz-Welle.
Geliefert via [`ADR 0061`](../../adr/0061-transformer-limit-bilanz-pattern.md)
`Accepted` (`TransformerLimitConfig` + Single-Zonen-Thermomodell +
`GridConstraintViolationEvent`). Trigger
[`021`](../open/021-sollte-transformer-limits.md) aufgeloest. Doc-Verschiebung
nach `done/` folgt mit der Welle-3-Gesamt-Closure (3a/3b/3c als Gruppe).
DoD (§2) erfuellt.

**Container:** [`M8-welle-3.md`](M8-welle-3.md) §3 (Welle-3-C0-Plan,
Reihenfolge 3a → 3b → 3c); [`roadmap.md`](roadmap.md) §4 M8. Design (C1):
NEU ADR-Folge (Schaerfung zu
[`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md), kein Supersede).
Trigger: [`021`](../open/021-sollte-transformer-limits.md) (`GG-GRID-006`,
Lastenheft §11.5; mit dieser Welle aufzuloesen).

---

## 1. Lieferziel

**Transformatorgrenzen auf Bilanz-Ebene** als Erweiterung von
`GridModelBilanz` — eine Wandlungs-/Belastungsgrenze im Netzmodell:
`max_apparent_power_kva`, Ueberlast-Zeit-Strom-Kennlinie und ein simples
Thermomodell (Top-Oil/Hot-Spot). Bei Verletzung wird ein **pro-Tick**
`GridConstraintViolationEvent` emittiert.

**Klar abgegrenzt** vom Transformer-**Geraet** (Welle 2b,
[`M8-welle-2b.md`](../done/M8-welle-2b.md)): das Geraet clamped nur seine
eigene Per-Device-Saettigung; 3b ist die **Netz-Grenze im Bilanzmodell**.

## 2. DoD (≤ 3 beobachtbare Kriterien)

- [x] **Config-Block**: NEU `TransformerLimitConfig` (nested, opt-in) in
      `GridModelConfig` (`src/grid_gym/hexagon/core/grid_model/config.py`) —
      `max_apparent_power_kva` + Thermomodell-Parameter, Default
      **inaktiv** (`None` = keine Grenze = bit-genau heutiges Verhalten);
      die Top-Oil-Zeitkonstante traegt die Zeit-Strom-Kennlinie;
      ≥ 100-Tick-Determinismus-Property. YAML-`transformer_limit`-Block.
- [x] **Pro-Tick-Grenz-Check** in `GridModelBilanz.update(...)` →
      `GridConstraintViolationEvent` (NEU frozen Domain-Event) bei
      Hot-Spot-Ueberschreitung, gedrained in `TickResult.emitted_grid_events`;
      Boundary-Pins (unter Grenze nie / moderate Dauer-Ueberlast nach
      Zeit-Akkumulation / kurze Ueberlast nie).
- [x] **Gates**: lint/format/typecheck/arch/test-unit/`coverage-gate-critical`
      ≥ 90 % auf `grid_model` (config 100 % / bilanz 98 % / snapshot 93 %) +
      `docs-check` + `accept-pin-check` gruen; NEU
      [`ADR 0061`](../../adr/0061-transformer-limit-bilanz-pattern.md)
      `Accepted`; Trigger 021 aufgeloest. (`is_islanded=False`/inaktiv
      bit-genau; `EXPECTED_DEMO_*` via opt-in Snapshot-/Scenario-Hash
      unberuehrt.)

## 3. Design-Skizze (C1)

- **Scheinleistungs-Basis** (C1-Entscheidung): was fliesst durch den
  Modell-Trafo — die Import/Export-Scheinleistung am `grid_connection`
  oder ein designierter Transformer-Durchsatz? Trigger 021 =
  Bilanzmodell-Erweiterung → netz-/`grid_connection`-seitig. **Bis 3c gilt
  S ≈ |P|** (nur Wirkleistung); [`M8-welle-3c.md`](M8-welle-3c.md)
  erweitert die Basis auf `S = sqrt(P² + Q²)`.
- **Ueberlast-Zeit-Strom-Kennlinie**: kurze Ueberlast erlaubt, dauerhafte
  nicht — akkumulierende Ueberlast-Zeit, `Decimal`-deterministisch.
- **Thermomodell simpel**: Top-Oil-/Hot-Spot-Temperatur als Funktion der
  Belastung (vereinfacht; kein IEC-Loading-Guide-Detail, §5).
- **Event-Pattern**: `GridConstraintViolationEvent` ist ein **pro-Tick
  emittiertes Laufzeit-Event** — Praezedenz `LoadEvent`
  (`src/grid_gym/hexagon/core/grid_model/loads.py`, dasselbe Modul, das
  3b erweitert) bzw. der Event-Domaintyp
  (`src/grid_gym/hexagon/core/domain/event.py`). **Nicht** eine
  Config-Construction-Exception — die Validierung der Grenzwert-Config
  selbst folgt separat dem Config-Error-Pattern.

## 4. Risiken / offene Design-Fragen

- **Scheinleistungs-Basis vor 3c**: solange nur `|P|`, ist die Grenze eine
  Wirkleistungs-Naeherung — explizit dokumentieren; 3c-Verzahnung (Grenze
  auf `S = sqrt(P² + Q²)` statt `|P|`). **3c re-pinnt die Boundary-Tests
  dieser Grenze** beim Wechsel auf `S` (Verhaltens-/Pin-Wechsel an der
  Grenze).
- **Abgrenzung zum Geraet (2b)**: die Doppeldeutigkeit „Transformer" muss
  klar bleiben (Geraet = Per-Device-Saettigung, 3b = Netz-Grenze).
- **Determinismus** der Zeit-Strom-Integration (`Decimal`-Akkumulation,
  `AC-NO-RAND`).

## 5. Nicht-Ziele (dieser Slice)

- Schutzgeraete-Logik (Distanz-/Differentialschutz) — M4-Material
  (Protokolladapter zu Schutzrelais).
- Reparatur-Zeiten / Asset-Lifecycle — Domain ist elektrisches Verhalten.
- IEC-Loading-Guide-Detailthermik (Mehr-Zonen-Modell) — vereinfachtes
  Thermomodell genuegt.
