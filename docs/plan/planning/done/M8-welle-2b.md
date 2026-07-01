# Welle 2b — Transformer (`GG-DEV-016`, ADR 0056)

**Status:** Done (M8-Welle-2b, geschlossen 2026-06-14) — zweites SOLLTE-
Geraet aus [`M8-welle-2.md`](M8-welle-2.md) §3. Reine Core-Domain-
Erweiterung + die acht Verdrahtungs-Naehte (Checkliste aus
[`M8-welle-2a.md`](M8-welle-2a.md) §4).

**Container:** [`M8-welle-2.md`](M8-welle-2.md) (Welle-2-C0-Plan);
[`roadmap.md`](../in-progress/roadmap.md) §4 M8. Design (C1):
[`ADR 0056`](../../adr/0056-transformer-device-pattern.md) `Accepted`.
Trigger: [`017`](../done-archive/017-sollte-transformer-device.md) (mit dieser
Welle aufgeloest).

---

## 1. Lieferziel

Das Transformator-Modell ([`GG-DEV-016`](../../../../spec/lastenheft.md#gg-dev-016), Lastenheft §9.4) als
`DeviceModel` + `FaultInjectableDevice` im Core, mit Wandlungsverhaeltnis,
Eisen-/Kupferverlusten, Saettigungs-Hard-Cap und `winding_fault`-
Schutzausloesung ([`ADR 0056`](../../adr/0056-transformer-device-pattern.md)).
Folgt dem GridConnection-Set-Power-Muster
([`ADR 0017`](../../adr/0017-grid-connection-device-pattern.md)).

## 2. DoD (≤ 3 beobachtbare Kriterien)

- [x] **Modell + Tests**: NEU `hexagon/core/devices/transformer/`
      (`config`/`commands`/`snapshot`/`model`) — Verlust-/Saettigungs-
      Math (inkl. Energie-Konsistenz), Snapshot-Roundtrip, ≥ 100-Tick-
      Determinismus + `winding_fault`
      ([`test_transformer_device.py`](../../../../tests/unit/hexagon/core/devices/transformer/test_transformer_device.py),
      [`test_fault_injection.py`](../../../../tests/unit/hexagon/core/devices/transformer/test_fault_injection.py)).
- [x] **End-to-End-Verdrahtung** (8 Naehte): `_DEVICE_FACTORIES`,
      `DEVICE_DECIMAL_PARAMS`, `_DEVICE_TYPE_BY_CLASS_NAME`, Alarm-Mapper,
      `_FAULT_TYPE_TO_DEVICE_TYPE`, `_runs_router`-State-Subset,
      `CRITICAL_COV_TARGETS`; Szenario-Beispiel
      [`transformer_demo.yaml`](../../../../tests/integration/scenarios/transformer_demo.yaml)
      + Smoke
      ([`test_transformer_scenario.py`](../../../../tests/integration/test_transformer_scenario.py)).
- [x] **Gates**: `make gates` gruen (10 A-1-Gates), inkl.
      `coverage-gate-critical` ≥ 90 % auf `devices/transformer`;
      `make docs-check` gruen. [`ADR 0056`](../../adr/0056-transformer-device-pattern.md)
      `Accepted`, Trigger 017 aufgeloest.

## 3. Realization-Notes (Abweichungen ggue. ADR-Wortlaut)

- **All-Decimal-Config** (5 Felder) — einfacher als EV-Charger (das
  einen nicht-numerischen `initial_plug_state` hatte): `config.py`/
  `snapshot.py`/`_config_from_params` spiegeln 1:1 das GridConnection-
  Muster, `from_snapshot` baut die Config per `**decimals`-Splat ohne
  `# type: ignore`.
- **Standalone-Device-Vereinfachung**: bei `primary_power_kw == 0` ist
  der Eisen-/Leerlaufverlust weiterhin praesent (`loss_kw =
  no_load_loss_kw`, `secondary_power_kw = 0`). Die netzseitige
  Verlust-Verrechnung (Bilanz) ist Trigger 021 ([`GG-GRID-006`](../../../../spec/lastenheft.md#gg-grid-006)), nicht
  dieses Geraet ([`ADR 0056`](../../adr/0056-transformer-device-pattern.md)
  §2.4).
- **Saettigung = harter Knie-Cap** bei `rated_power_kw` (Command-seitig
  `LIMITED` + Alarm; kein zustandsabhaengiger Per-Tick-Re-Clamp noetig,
  da der Cap konstant ist — anders als EV-SoC). Weiche Kennlinie ist
  Welle-3+-Schaerfung.
- **`fault_state`-Block + alarm_mappers-Vereinfachung**: `winding_fault_active`
  liegt im additiven `fault_state`-Block
  ([`ADR 0025`](../../adr/0025-fault-recovery-pattern.md) §2.2). Der
  `dispatch_alarm_mapper`-`isinstance` nutzt jetzt den `PowerDeviceAlarm`-
  Union-Alias statt der inline-Aufzaehlung (DRY; bei 6 Power-Device-
  Alarms wurde die Inline-Liste zu lang).

## 4. Lerneintrag (Closure-Pflicht)

**Bestaetigte Regel:** Die „8-Naht"-Checkliste aus
[`M8-welle-2a.md`](M8-welle-2a.md) §4 hat fuer das zweite Geraet
**vollstaendig getragen** — kein vergessener Integrationspunkt, beide
Drift-Tests (`test_loader_factory_sync` + `test_yaml_loader_allowlist`)
blieben gruen, weil `TransformerConfig` direkt in die Config-Klassen-
Liste des Allowlist-Tests aufgenommen wurde. **Neue Schaerfung:** die
`alarm_mappers`-`PowerDeviceAlarm`-Union ist die richtige Single-Source
fuer den `isinstance`-Dispatch — neue Power-Device-Alarms nur dort
ergaenzen, nicht in einer zweiten Inline-Liste (sonst Drift + Zeilen-
Laenge). Damit ist die Checkliste fuer 2c (Wind) / 2d (Diesel)
verlaesslich.

## 5. Review-Folge

High-effort `/code-review` (Rollentrennung, separate Finder-Kontexte).
Device-Math- + Integrations-Finder: **0 Befunde** (Verlust-/Sign-Math,
Floor, Fault-Freeze, Snapshot-Roundtrip, Determinismus, alle 8 Naehte +
`isinstance(PowerDeviceAlarm)` verifiziert). **Adressiert** (Test-
Schaerfung):

- NEU `test_throughput_uses_dt_conversion_at_default_tick_ms` — die
  `throughput = |secondary| * (tick_ms / 3_600_000)`-Konversion war nur
  am 1-h-Tick (dt == 1, degeneriert) gepinnt; jetzt am Default
  `tick_ms=1000` mit exaktem Wert (ein falscher Divisor faellt auf).
- Floor-Fall (`loss > input`): zusaetzlich `throughput_kwh == 0` +
  `efficiency == 0` gepinnt (ein `|primary|`-statt-`|secondary|`-
  Akkumulations-Bug faellt auf).
- `winding_fault`-Freeze ueber **mehrere** gefaultete Ticks gepinnt
  (Safety-Invariante).

**Bewusst deferred:**

- `_winding_fault_from_state` ist die **4. Kopie** des optionalen
  `fault_state`-Bool-Readers (Battery/GridConnection/EV/Transformer) —
  reif fuer einen geteilten `snapshot_codec.assert_optional_fault_flag`-
  Helper, aber der Refactor beruehrt vier Devices + Tests: eigener
  Dedup-Folge-Slice (Erbschaft aus [`M8-welle-2a.md`](M8-welle-2a.md)
  §5).
- Command-getriebener Integration-E2E: das generische Command-Routing
  durch den TickLoop ist via Agents/Battery-Integration bereits gedeckt;
  der Transformer-`apply_command` ist Unit-gepinnt. Kein
  scenario-scheduled-Command-Mechanismus im `devices`-Block — wie 2a
  faehrt der Smoke idle. Getrackt als Trigger
  [`046`](046-command-driven-integration-e2e.md).
- `abs(primary)`/`abs(secondary)`-Mehrfachberechnung pro Tick
  (vernachlaessigbar; die Staticmethod-Aufteilung favorisiert
  Lesbarkeit).
