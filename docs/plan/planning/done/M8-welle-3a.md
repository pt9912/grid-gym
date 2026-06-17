# Welle 3a — Inselnetz-Bilanzmodell (`GG-GRID-005`)

**Status:** Done (M8-Welle-3a, 2026-06-16) — erste Sub-Welle der Netz-Welle,
lokale Schaerfung des `GridModelBilanz`. Geliefert via
[`ADR 0060`](../../adr/0060-island-grid-bilanz-pattern.md) `Accepted`
(`is_islanded`/`forming_device_id` + Forming-Geraet als Slack + opt-in
Snapshot-/Scenario-Hash). Trigger
[`020`](../open/020-sollte-island-grid.md) aufgeloest. Doc-Verschiebung nach
`done/` folgt mit der **Welle-3-Gesamt-Closure** (3a/3b/3c als Gruppe, wie
Welle 2). DoD (§2) erfuellt.

**Container:** [`M8-welle-3.md`](M8-welle-3.md) §3 (Welle-3-C0-Plan,
Reihenfolge 3a → 3b → 3c); [`roadmap.md`](../in-progress/roadmap.md) §4 M8. Design (C1):
NEU ADR-Folge (Schaerfung zu
[`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md), kein Supersede).
Trigger: [`020`](../open/020-sollte-island-grid.md) ([`GG-GRID-005`](../../../../spec/lastenheft.md#gg-grid-005),
Lastenheft §11.5; mit dieser Welle aufzuloesen).

---

## 1. Lieferziel

Ein **Inselnetz-Bilanzmodell** als Erweiterung von `GridModelBilanz`
(`src/grid_gym/hexagon/core/grid_model/bilanz.py`): ein Netz **ohne
externen Slack-Bus**, in dem ein internes Grid-Forming-Geraet (typisch
Diesel-Generator oder Battery-Inverter) die Bilanz schliesst und
Frequenz/Spannung haelt. Heute injiziert der TickLoop den Residual als
Auto-Slack in den `grid_connection`
([`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md) §2.2,
Auto-Schluss; Code in `src/grid_gym/hexagon/core/simulation/tick_loop.py`);
im Inselnetz
entfaellt dieser Pfad, der Residual wird vom Grid-Forming-Geraet
absorbiert.

## 2. DoD (≤ 3 beobachtbare Kriterien)

- [x] **Config + Insel-Fork**: `is_islanded: bool` + `forming_device_id:
      str | None` additiv in `GridModelConfig`
      (`src/grid_gym/hexagon/core/grid_model/config.py`), Default
      `False`/`None`; **Presence-Validierung** am Config-Rand
      (Biconditional: `forming_device_id` gesetzt **gdw** `is_islanded`);
      Inselnetz-Imbalance ohne `grid_connection`-Slack; ≥ 100-Tick-
      Determinismus-Property. YAML-`grid_model`-Sektion liest die Felder.
- [x] **TickLoop-Auto-Close**: im Inselnetz Residual-Injektion auf das
      `forming_device_id`-Geraet statt `grid_connection` (Vorzeichen pro
      `_BILANZ_SOURCE_BUCKETS`: Generation `-residual`, Storage `+residual`);
      deterministische Forming-Election (explizite ID); **Existence-
      Validierung im TickLoop-Wiring** (`_validate_forming_device` →
      `TickLoopUnknownFormingDeviceError`, nicht in der Config);
      **`is_islanded=False` bit-genau wie heute** (Connected-Pfad textlich
      unveraendert; `EXPECTED_DEMO_*` via opt-in Snapshot-/Scenario-Hash
      unberuehrt, [`ADR 0060`](../../adr/0060-island-grid-bilanz-pattern.md)
      §2.4).
- [x] **Gates**: lint/format/typecheck/arch/test-unit/`coverage-gate-critical`
      ≥ 90 % auf `grid_model` (kein neuer Target — config 100 % / snapshot
      92 % / tick_loop 97 %) + `docs-check` + `accept-pin-check` gruen
      (`dep-audit` flaggt nur Bestands-CVEs in `cryptography`/`starlette`,
      von 3a unberuehrt); NEU
      [`ADR 0060`](../../adr/0060-island-grid-bilanz-pattern.md) `Accepted`;
      Trigger 020 aufgeloest.

## 3. Design-Skizze (C1)

- **Config** (`grid_model/config.py`): zwei additive Felder.
  `__post_init__` prueft nur **Presence** — `forming_device_id` gesetzt
  wenn `is_islanded` (Config-Error-Pattern wie
  `BatteryConfigInvalidValueError`). `GridModelConfig` kennt **keine
  Device-Registry** → keine Existenz-Pruefung an dieser Stelle.
- **Auto-Close** (`tick_loop.py`): heute `pre_grid_residual = generation
  - load - storage`, dann `set_power_kw := -residual` auf den
  `grid_connection`. Insel-Pfad: Residual-Ziel = Grid-Forming-Geraet;
  `grid_connection` wird **nicht** als Slack genutzt (oder ist im
  Inselnetz-Szenario abwesend). **Existence-Check hier**: beim Aufloesen
  des `forming_device_id` (analog dazu, wie
  `_apply_grid_connection_auto_close` das `grid_dev` aufloest) — eine
  unbekannte ID ist ein Wiring-Fehler, kein Config-Fehler.
- **Frequenz/Spannung**: `GridModelBilanz` haelt sie weiter proportional;
  ohne externe Referenz greifen die Insel-Toleranzbaender. Kein
  Droop-Detailmodell (out-of-scope, §5).
- **Election**: ausschliesslich per `forming_device_id` — kein impliziter
  „erstes Geraet"-Tie-Break (Determinismus).

## 4. Risiken / offene Design-Fragen

- **Forming-Ueberlast**: Residual > Kapazitaet des Forming-Geraets →
  Clamp + Constraint-Signal? Moegliche Wiederverwendung des
  `GridConstraintViolationEvent` aus [`M8-welle-3b.md`](M8-welle-3b.md);
  C1-Entscheidung.
- **Forming-Geraet faellt aus** (Fault): Black-Start minimal (Init ohne
  Netzanschluss); Multi-Insel-Recovery out-of-scope.
- **Default-Stabilitaet**: `is_islanded=False` muss den bestehenden
  Single-Bus-Pfad bit-identisch lassen — Regressions-Pin zwingend.

## 5. Nicht-Ziele (dieser Slice)

- Schwarzstart-Synchronisation zwischen mehreren Inselnetzen — eigener
  Trigger ([`020`](../open/020-sollte-island-grid.md) Out-of-scope).
- Droop-/Detail-Regelung der Frequenzhaltung — vereinfachte Bilanz bleibt.
- Lastabwurf / Load-Shedding — Multi-Agent-Kontext, separater Trigger.
- Blindleistungs-Spannungshaltung — [`M8-welle-3c.md`](M8-welle-3c.md).
