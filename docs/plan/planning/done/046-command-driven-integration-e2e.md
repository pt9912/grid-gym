# 046 — Command-getriebener Integration-E2E fuer die SOLLTE-Geraete

**Status:** **Resolved 2026-06-18 (`done/`)** — Voll-Mechanismus-Welle
[`ADR 0070`](../../adr/0070-scenario-scheduled-device-commands.md) `Accepted`
+ [`Slice-Plan`](scenario-scheduled-device-commands.md) (S0..S3 geliefert):
`commands`-Block + ScenarioCommandEngine + A0s-Naht + 4 nicht-idle SOLLTE-E2E
(EV/Transformer/Diesel reagieren, Wind `IGNORED`). `make fullbuild` gruen.
Vormals: Forward-Gap aus M8-Welle-2a..2d ("Bewusst deferred")
**Datum:** 2026-06-15
**Quelle:** M8-Welle-2a..2d Anti-Scope; erstmals als Folge-Slice in
[`ADR 0055`](../../adr/0055-ev-charger-device-pattern.md) §6 vermerkt
(EV-Charger), in 2b/2c/2d identisch wiederholt.

---

## Kontext

Jedes der vier SOLLTE-Geraete (EV-Charger, Transformer, Wind-Turbine,
Diesel-Generator; [`GG-DEV-015`](../../../../spec/lastenheft.md#gg-dev-015)..018) bringt eine `apply_command`-
Implementierung mit (Geraete-`_protocol.py`-Vertrag,
`src/grid_gym/hexagon/core/devices/_protocol.py`). Die zugehoerigen
Szenario-Smokes — `tests/integration/test_ev_charger_scenario.py`,
`tests/integration/test_transformer_scenario.py`,
`tests/integration/test_wind_turbine_scenario.py`,
`tests/integration/test_diesel_scenario.py` — fahren das Geraet jedoch
**idle**: kein Command wird ueber die Szenario-Schiene injiziert.

Grund: der Szenario-YAML-Layer (`src/grid_gym/scenario_yaml.py`) kennt
**keinen** scenario-scheduled-Command-Mechanismus fuer den
`devices`-Block — Faults werden tick-genau geplant, Commands nicht. Das
generische Command-Routing durch den `TickLoop` ist stattdessen gedeckt
durch:

- `tests/integration/test_agents_demo_e2e.py` — Agents treiben Commands
  end-to-end durch den Loop;
- die Battery-Command-Surface
  (`src/grid_gym/hexagon/core/devices/battery/commands.py`) — reichster
  Command-Konsument, Unit- + Integration-gepinnt.

Pro Geraet ist `apply_command` zusaetzlich **unit**-gepinnt. Der
Mechanismus ist damit abgedeckt; es fehlt allein der geraetespezifische
E2E-Pfad „Command kommt via Szenario rein → Geraet reagiert sichtbar im
Snapshot".

## Offene Substanz (dieser Trigger)

- Ein **scenario-scheduled-Command-Mechanismus** im `devices`-Block des
  Szenario-YAML (analog zur bestehenden Fault-Planung), der Commands
  tick-genau an ein Geraet zustellt.
- Darauf aufsetzend je ein **nicht-idle Integration-E2E** pro
  SOLLTE-Geraet, das ein Command einplant und die Geraete-Reaktion im
  Snapshot assertet (statt des heutigen Idle-Smokes).

## Aktivierungs-Bedingung

- Einfuehrung eines scenario-scheduled-Command-Mechanismus im
  `devices`-Block (z. B. durch eine spaetere Welle/Demo mit
  zeitgesteuerten Geraete-Commands) — dann wird der E2E-Pfad
  Vorbedingung statt Nachlauf.
- ODER konkreter Bedarf an geraetespezifischer Command-Routing-
  Abdeckung jenseits der generischen Agents/Battery-Deckung (z. B. ein
  Reviewer-/Stakeholder-Befund, dass `apply_command` eines
  SOLLTE-Geraets nur unit-, nicht integrationsgedeckt ist).

## Wandert nach

`done/`, sobald der `devices`-Block scenario-scheduled Commands
unterstuetzt und mindestens ein SOLLTE-Geraet einen nicht-idle
Command-E2E fuehrt (Snapshot-Assertion auf die Command-Reaktion).

## References

- [`../done/M8-welle-2a.md`](M8-welle-2a.md) §5 — erste „Bewusst
  deferred"-Notiz (EV-Charger; Smoke faehrt idle).
- [`../done/M8-welle-2b.md`](M8-welle-2b.md) /
  [`../done/M8-welle-2c.md`](M8-welle-2c.md) /
  [`../done/M8-welle-2d.md`](M8-welle-2d.md) — identische
  Wiederholung (Transformer/Wind/Diesel).
- [`ADR 0055`](../../adr/0055-ev-charger-device-pattern.md) §6 —
  kanonische Folge-Slice-Notiz (Scenario-Fault-Engine + Command-E2E).
