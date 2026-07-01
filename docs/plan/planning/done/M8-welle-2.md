# Welle 2 — M8 SOLLTE-Geraete (`GG-DEV-015..018`)

**Status:** Done (M8-Welle-2, eroeffnet 2026-06-13, geschlossen
2026-06-14) — erstes echtes
Feature von M8: die vier SOLLTE-Geraetemodelle aus Lastenheft §9.4, die M2
bewusst out-of-scope hielt. Reine Core-Domain-Erweiterung, kein neuer
Port/Adapter-Typ. Dieser Plan ist die Welle-2-C0-Substanz.

**Container:** Meilenstein-Scope in [`roadmap.md`](../in-progress/roadmap.md) §4 M8;
Welle-0-Triage in [`M8-welle-0.md`](M8-welle-0.md). Voraussetzung
(M8-Welle 1, Architektur-Cleanup) ist abgeschlossen — `RunExecutionPort`
+ `ignore_imports = []`, sodass neue Geraete-Driving-Adapter (falls fuer
UI/HTTP noetig) keine [`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)-Bridge erben.

**Closure (2026-06-14):** alle vier Sub-Wellen geliefert —
[`2a`](M8-welle-2a.md) / [`2b`](M8-welle-2b.md) / [`2c`](M8-welle-2c.md) /
[`2d`](M8-welle-2d.md) ([`GG-DEV-015`](../../../../spec/lastenheft.md#gg-dev-015)..018) + Welle-2-D8 (generische
`ScenarioFaultEngine`, [`M8-welle-2-d8.md`](M8-welle-2-d8.md),
[`ADR 0059`](../../adr/0059-generic-scenario-fault-engine.md) `Accepted`).
`D-7` (Pre-init-Defense) in Welle 2a adoptiert/aufgeloest. Welle 3
(Netz, `T-020..022`) + Welle 4 (BESS, `T-023/024`) sind eigene Wellen
(siehe §5 Nicht-Ziele), noch nicht eroeffnet.

---

## 1. Zweck + Architektur-Familie

Jedes Geraet folgt dem etablierten Device-Submodul-Muster
(`config.py`/`model.py`/`snapshot.py`, ggf. `commands.py`), wie die fuenf
MVP-MUSS-Geraete (`battery`, `pv`, `load`, `grid_connection`,
`smart_meter`). Pro Geraet: Snapshot-Roundtrip + Determinismus-Property-
Test, `_DEVICE_FACTORIES`-Eintrag in `core/scenario/loader.py`,
Scenario-Validator-Schaerfung der neuen `params`-Felder,
`CRITICAL_COV_TARGETS`-Erweiterung.

| Geraet | ID | Trigger | Muster-ADR | Charakteristik |
|---|---|---|---|---|
| EV-Charger | [`GG-DEV-015`](../../../../spec/lastenheft.md#gg-dev-015) | [`016`](../done-archive/016-sollte-ev-charger-device.md) | [`ADR 0017`](../../adr/0017-grid-connection-device-pattern.md) | Lade-/Entlade-Curves, `plug_state`, optional bidirektional (V2G) |
| Transformer | [`GG-DEV-016`](../../../../spec/lastenheft.md#gg-dev-016) | [`017`](../done-archive/017-sollte-transformer-device.md) | [`ADR 0017`](../../adr/0017-grid-connection-device-pattern.md) | Wandlungsverhaeltnis, Kupfer-/Eisenverluste, Saettigung |
| Wind | [`GG-DEV-017`](../../../../spec/lastenheft.md#gg-dev-017) | [`018`](../done-archive/018-sollte-wind-device.md) | [`ADR 0016`](../../adr/0016-pv-load-device-pattern.md) | Wind-Leistungs-Kurve (kubisch), cut-in/-out/rated |
| Diesel | [`GG-DEV-018`](../../../../spec/lastenheft.md#gg-dev-018) | [`019`](../done-archive/019-sollte-diesel-device.md) | [`ADR 0014`](../../adr/0014-battery-snapshot-schema.md) | Kraftstoff-Vorrat (l), Verbrauch (l/kWh), Ramp-Limits, Start-/Stop-Hysterese |

**Architektur-Erbschaft:** kein neuer Driving-/Driven-Port, keine neue
Adapter-Familie — die Geraete sind `DeviceModel`-Implementierungen im Core
(`hexagon/core/devices/`). Fault-relevante Geraete implementieren zusaetzlich
`FaultInjectableDevice` (Welle-1-`*FaultEngine`-Kompatibilitaet).

## 2. Erfolgskriterien (DoD je Geraet)

- ADR-Folge (Status `Accepted`) mit geraete-spezifischen
  Akzeptanzkriterien, analog der Muster-ADR.
- NEU `devices/<x>/`-Submodul: `<X>Config` (frozen dataclass), `<X>Device`,
  `<X>`-Snapshot (Roundtrip-stabil, kanonische Serialisierung).
- `_DEVICE_FACTORIES["<x>"]`-Eintrag in `core/scenario/loader.py`.
- Scenario-Validator schaerft die neuen `params`-Felder (Pydantic-strict,
  `extra="forbid"`).
- Tests: Snapshot-Roundtrip, Determinismus-Property (`hypothesis`),
  Boundary-/Negative-Pins. `CRITICAL_COV_TARGETS` um `devices/<x>`
  erweitert; `make coverage-gate-critical` ≥ 90 %.
- `make gates` gruen; bei Szenario-/Loader-Aenderung `make
  test-determinism`.

## 3. Tranchierung (Sub-Slicing)

Vier unabhaengige Geraetemodelle ueberschreiten die Sub-Slicing-Schwelle
(> 2 unabhaengige Sub-Bereiche) → Split in vier Sub-Wellen, je **1 ADR +
1 Submodul + Tests**. Jede Sub-Welle aktiviert ihren `open/`-Trigger und
loest ihn bei Closure auf.

- **Welle 2-C0 — Eroeffnung** (dieser Plan): Muster-Bestaetigung gegen
  [`ADR 0014`](../../adr/0014-battery-snapshot-schema.md)/`0016`/`0017`, Reihenfolge-Entscheidung. Sensor: `make docs-check`.
- **Welle 2a — EV-Charger** ([`GG-DEV-015`](../../../../spec/lastenheft.md#gg-dev-015), [`016`](../done-archive/016-sollte-ev-charger-device.md)):
  NEU ADR + `devices/ev_charger/`.
- **Welle 2b — Transformer** ([`GG-DEV-016`](../../../../spec/lastenheft.md#gg-dev-016), [`017`](../done-archive/017-sollte-transformer-device.md)):
  NEU ADR + `devices/transformer/`.
- **Welle 2c — Wind** ([`GG-DEV-017`](../../../../spec/lastenheft.md#gg-dev-017), [`018`](../done-archive/018-sollte-wind-device.md)):
  NEU ADR + `devices/wind/`.
- **Welle 2d — Diesel** ([`GG-DEV-018`](../../../../spec/lastenheft.md#gg-dev-018), [`019`](../done-archive/019-sollte-diesel-device.md)):
  NEU ADR + `devices/diesel/`.

**Reihenfolge-Vorschlag:** nach Muster-Naehe — 2a/2b (GridConnection-Muster,
[`ADR 0017`](../../adr/0017-grid-connection-device-pattern.md)) zusammenhaengend, dann 2c (PV-Muster), 2d (Battery-Muster).
Alternativ Use-Case-Prioritaet: Wind + Diesel zuerst, falls die Inselnetz-
Story (Welle 3, `T-020`) vorgezogen werden soll. Entscheidung in
Welle-2a-C0.

**`D-7`-Adoption:** das Pre-init-Defense-Pattern (Carveout-Index, M5-Welle-6b
Review-Folge) wird in der **ersten** device-iterierenden Sub-Welle adoptiert
und der `D-7`-Eintrag dort aufgeloest.

## 4. Risiken

- **Snapshot-/Hash-Stabilitaet:** neue Geraete-Felder duerfen die
  `EXPECTED_DEMO_*`-Pins nicht brechen ([`ADR 0052`](../../adr/0052-max-age-stale-quality-stage.md)
  §2.1) — neue Geraete sind opt-in im Szenario; der MVP-Demo bleibt
  unveraendert.
- **Determinismus:** kubische Wind-Kurve / Diesel-Ramp-Hysterese brauchen
  `Decimal`-Rundungs-Disziplin ([`AC-NO-RAND`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), kanonische Serialisierung) —
  kein Float-Drift im Snapshot.
- **Coverage-critical:** jedes Submodul MUSS in `CRITICAL_COV_TARGETS`,
  sonst faellt die kritische Domain unter 90 %.

## 5. Nicht-Ziele

- Protokollanschluss (ISO 15118 / OCPP fuer EV, Modbus fuer Transformer)
  — separater Adapter-Slice (M4-Material).
- Multi-EV-Pool / Smart-Charging-ML — eigenes Slice.
- Netzbilanz-Integration (Inselnetz, Transformatorgrenzen, Blindleistung)
  — Welle 3 (`T-020..022`).
- BESS-Telemetry-Erweiterung — Welle 4 (`T-023/024`).

## 6. DoD (Welle 2-C0)

- [x] `M8-welle-2.md` angelegt (dieser Plan).
- [x] Wellen-Nummerierung konsistent (roadmap §4 + `M8-welle-0.md` §1.1:
      Welle 1 = Cleanup, 2 = Geraete, 3 = Netz, 4 = BESS).
- [x] `make docs-check` gruen.
