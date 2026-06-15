# Welle 3a — Inselnetz-Bilanzmodell (`GG-GRID-005`)

**Status:** Geplant (M8-Welle-3a) — erste Sub-Welle der Netz-Welle, lokale
Schaerfung des `GridModelBilanz`. **Noch nicht umgesetzt** — DoD (§2) offen.

**Container:** [`M8-welle-3.md`](M8-welle-3.md) §3 (Welle-3-C0-Plan,
Reihenfolge 3a → 3b → 3c); [`roadmap.md`](roadmap.md) §4 M8. Design (C1):
NEU ADR-Folge (Schaerfung zu
[`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md), kein Supersede).
Trigger: [`020`](../open/020-sollte-island-grid.md) (`GG-GRID-005`,
Lastenheft §11.5; mit dieser Welle aufzuloesen).

---

## 1. Lieferziel

Ein **Inselnetz-Bilanzmodell** als Erweiterung von `GridModelBilanz`
(`src/grid_gym/hexagon/core/grid_model/bilanz.py`): ein Netz **ohne
externen Slack-Bus**, in dem ein internes Grid-Forming-Geraet (typisch
Diesel-Generator oder Battery-Inverter) die Bilanz schliesst und
Frequenz/Spannung haelt. Heute injiziert der TickLoop den Residual als
Auto-Slack in den `grid_connection`
([`ADR 0017`](../../adr/0017-grid-connection-device-pattern.md) §2.7,
`src/grid_gym/hexagon/core/simulation/tick_loop.py`); im Inselnetz
entfaellt dieser Pfad, der Residual wird vom Grid-Forming-Geraet
absorbiert.

## 2. DoD (≤ 3 beobachtbare Kriterien)

- [ ] **Config + Insel-Fork**: `is_islanded: bool` + `forming_device_id:
      str | None` additiv in `GridModelConfig`
      (`src/grid_gym/hexagon/core/grid_model/config.py`), Default
      `False`/`None`; Inselnetz-Imbalance ohne `grid_connection`-Slack;
      ≥ 100-Tick-Determinismus-Property.
- [ ] **TickLoop-Auto-Close**: im Inselnetz Residual-Injektion auf das
      `forming_device_id`-Geraet statt `grid_connection`; deterministische
      Forming-Election (explizite ID, Config-Error bei fehlender/
      unbekannter ID); **`is_islanded=False` bit-genau wie heute**
      (Regressions-Pin auf `EXPECTED_DEMO_*`).
- [ ] **Gates**: `make gates` gruen (`coverage-gate-critical` ≥ 90 % auf
      `grid_model`, kein neuer Target); NEU ADR `Accepted`; Trigger 020
      aufgeloest.

## 3. Design-Skizze (C1)

- **Config** (`grid_model/config.py`): zwei additive Felder; Validierung
  im `__post_init__` — `forming_device_id` MUSS gesetzt sein wenn
  `is_islanded` (Config-Error-Pattern wie `BatteryConfigInvalidValueError`).
- **Auto-Close** (`tick_loop.py`): heute `pre_grid_residual = generation
  - load - storage`, dann `set_power_kw := -residual` auf den
  `grid_connection`. Insel-Pfad: Residual-Ziel = Grid-Forming-Geraet;
  `grid_connection` wird **nicht** als Slack genutzt (oder ist im
  Inselnetz-Szenario abwesend).
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
