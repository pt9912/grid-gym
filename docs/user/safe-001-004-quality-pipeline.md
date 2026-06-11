# Quality-Pipeline-Audit (`GG-SAFE-001..004`)

**Quelle:** M6-Welle-5a-C2 (Quality-Pipeline-Audit;
[`../plan/planning/done/M6-welle-5a.md`](../plan/planning/done/M6-welle-5a.md)).
**Stand:** 2026-06-06 (Welle-5a-Audit) · `GG-SAFE-004`-Flip
✗ → ✓ 2026-06-11 (M7-Welle-3a-C2, ADR 0052).

Dieses Dokument auditiert die existierende Quality-Pipeline-
Substanz gegen die vier MUSS-Akzeptanzen `GG-SAFE-001..004`
aus dem Lastenheft (§20). Pro ID werden Substanz-Pfade,
Test-Pfade und Lieferstatus dokumentiert.

---

## Übersicht

| ID | Lastenheft-Akzeptanz | Substanz-Pfad | Test-Pfad | Status |
| -- | -------------------- | ------------- | --------- | ------ |
| **GG-SAFE-001** | Ungueltige Daten erkannt: Schema-/Wertebereich-/Einheiten-Fehler → `invalid`-Quality oder Validierungs-Fehler + Alarm/Fehler-Datensatz. | `hexagon/core/scenario/loader.py::load_scenario` (Schema-Validierung) + `adapters/driving/http_api/_schemas.py` (Pydantic-API-Validierung) + `adapters/driven/protocol_opcua/_port.py:312` + `adapters/driven/protocol_iec61850/_port.py:368` (Adapter-`Quality.INVALID`-Emission) | `tests/integration/test_m6_welle_5a_safe_001_004_smoke.py::test_safe_001_invalid_scenario_schema_rejected` + `::test_safe_001_invalid_scenario_wrong_type_rejected` (Schwester fuer Typ-Fehler-Pfad) + `tests/unit/hexagon/core/scenario/test_loader.py` (Loader-Validierung) | ✓ **Produktiv** |
| **GG-SAFE-002** | NaN-Werte rejected: vor Zustandsfortschreibung erkannt, als `nan`-Quality serialisiert + Alarm/typisierter Fehler. | `hexagon/core/serialization/canonical.py::canonical_json` rejected `Decimal("NaN")`/`Decimal("Infinity")` mit `NonFiniteDecimalError` | `tests/integration/test_m6_welle_5a_safe_001_004_smoke.py::test_safe_002_nan_value_rejected_at_serialization` + `tests/unit/hexagon/core/serialization/test_canonical.py` | ✓ **Produktiv** |
| **GG-SAFE-003** | Kommunikationsausfaelle erkannt: betroffene Telemetrie `missing`/`stale` + Alarm mit Ziel/Startzeit/Ursache. | **Teil-produktiv**: `hexagon/core/devices/smart_meter/model.py:202` (SmartMeter-pre-attach → `Quality.MISSING`). Echte Adapter-Verbindungs-Verlust-Erkennung + Alarm-Emission **fehlt**. | `tests/integration/test_m6_welle_5a_safe_001_004_smoke.py::test_safe_003_smart_meter_pre_attach_emits_missing` (Teil-Substanz; voller Akzeptanz-Smoke `pytest.skip`) | ⚠ **Partial Lücke** — siehe [Trigger 035](../plan/planning/open/035-safe-003-comm-failure-missing-quality.md) |
| **GG-SAFE-004** | Veraltete Daten markiert: `max_age`-Ueberschreitung → deterministisch `stale`-Quality. | `hexagon/core/simulation/tick_loop.py::_apply_max_age_stage` (`STALE`-Stage vor dem `TickResult`-Bau; Stream + Persistenz + Replay identisch markiert) + keyword-only Kwarg `max_age_ms` am `TickLoop`-Konstruktor und in `TickLoopWiring`/`build_tick_loop` (ADR 0052; M7-Welle-3a) | `tests/integration/test_m6_welle_5a_safe_001_004_smoke.py::test_safe_004_stale_data_quality_after_max_age` (reaktiviert) + `tests/unit/hexagon/core/simulation/test_tick_loop_welle_3a_max_age.py` (Boundary/Override/Determinismus) | ✓ **Produktiv** (M7-Welle-3a) |

**Legende**:
- ✓ Produktiv: Akzeptanz vollstaendig erfuellt + Smoke-Test
  pinnt das in CI.
- ⚠ Partial Lücke: Sub-Substanz existiert, voller Akzeptanz-
  Umfang nicht abgedeckt; Trigger verankert den Folge-Pfad.
- ✗ Lücke: keine produktive Substanz; Trigger verankert den
  Folge-Pfad.

---

## Detail pro ID

### `GG-SAFE-001` — Ungueltige Daten erkannt

**Lastenheft-Akzeptanz (Z. 1349-1355)**: Schema-,
Wertebereichs- und Einheitenfehler werden vor Uebernahme in
den Simulationskern als Validierungsfehler ODER
Qualitaetsstatus `invalid` gemeldet, plus Fehler-/Alarm-
Datensatz.

**Status**: ✓ **Produktiv** ueber drei orthogonale Pfade:

1. **Scenario-Loader-Validierung** (`hexagon/core/scenario/
   loader.py::load_scenario`):
   - Wirft typisierte `ScenarioWrongTypeError`/
     `ScenarioMissingKeysError`/`ScenarioInvalidLoadTargetError`/
     etc. bei Schema-Verletzungen.
   - Beleg: `tests/unit/hexagon/core/scenario/test_loader.py`
     + Welle-5a-Smoke `test_safe_001_invalid_scenario_schema_
     rejected`.
2. **HTTP-API-Pydantic-Validierung** (`adapters/driving/
   http_api/_schemas.py`):
   - FastAPI rejected ungueltige REST-Inputs mit 422-Response.
   - Beleg: existierende Endpoint-Tests pruefen 422-Antworten
     fuer Schema-Verletzungen.
3. **Adapter-`Quality.INVALID`-Emission**:
   - `adapters/driven/protocol_opcua/_port.py:312` und
     `adapters/driven/protocol_iec61850/_port.py:368`:
     String-Lese-Faelle emittieren `Quality.INVALID`.

**Alarm-Datensatz**: nicht alle Pfade emittieren einen
typisierten Alarm. Reine Validierungs-Fehler (Scenario-Loader
+ Pydantic-API) erfuellen die Acceptance via „Validierungs-
fehler" (typed exception). Adapter-Quality-Emission erfuellt
die Acceptance via „`invalid`-Quality"; Alarm-Pflicht koennte
strenger interpretiert werden — als Forward-Defense ist das
in Welle-5b/5c oder M6-Welle-7-Closure adressierbar.

### `GG-SAFE-002` — NaN-Reject

**Lastenheft-Akzeptanz (Z. 1357-1363)**: NaN-Werte werden vor
Zustandsfortschreibung erkannt, als Qualitaetsstatus `nan`
serialisiert + Alarm/typisierter Fehler.

**Status**: ✓ **Produktiv**:

- **`canonical_json`-NaN-Reject**: `hexagon/core/
  serialization/canonical.py::canonical_json` wirft
  `NonFiniteDecimalError` (Subklasse von
  `CanonicalSerializationError`) bei `Decimal("NaN")` /
  `Decimal("Infinity")`. Das ist eine **typisierte Fehler-
  Substanz** im Sinne der Acceptance.
- Beleg: `tests/unit/hexagon/core/serialization/test_canonical.
  py` + Welle-5a-Smoke `test_safe_002_nan_value_rejected_at_
  serialization`.

**`Quality.NAN`-Enum-Wert** existiert (`hexagon/core/domain/
quality.py:28`), wird aber heute nicht produktiv emittiert —
weil der NaN-Reject auf der Serialisierungs-Ebene greift,
nicht auf der Quality-Pipeline-Ebene. Das ist eine bewusste
Architekturwahl (M2-Welle-0a Trigger 014): NaN ist
deterministisch nicht-serialisierbar, nicht-replay-faehig,
daher ist Reject die kanonisch korrekte Substanz.

### `GG-SAFE-003` — Kommunikationsausfall

**Lastenheft-Akzeptanz (Z. 1365-1371)**: Kommunikationsausfaelle
erzeugen einen dokumentierten Fehlerstatus, betroffene
Telemetrie wird als `missing` oder `stale` markiert und ein
Alarm mit Ziel, Startzeit und Ursache wird erzeugt.

**Status**: ⚠ **Partial Lücke**:

**Teil-produktiv**:

- `SmartMeterDevice` emittiert `Quality.MISSING` wenn
  Source-Devices nicht via `attach_sources(...)`-Hook attached
  sind (`hexagon/core/devices/smart_meter/model.py:202` + ADR
  0018 §2.3). Das ist **Konfigurations-Pre-Attach-Zustand**,
  NICHT Kommunikationsausfall im engeren Sinn.

**Fehlend**:

- **Real-Kommunikations-Ausfall-Erkennung**: kein Adapter hat
  Verbindungs-Verlust-Lifecycle-Hook mit Quality-Emission.
- **Alarm-Emission**: keiner der existierenden Pfade emittiert
  einen typisierten `Alarm`-Datensatz fuer SAFE-003-
  Akzeptanz.

**Folge-Pfad**: [Trigger 035](../plan/planning/open/035-safe-003-comm-failure-missing-quality.md)
verankert die erwartete Lieferung (Adapter-Lifecycle-Hook +
Quality-Emission + Alarm-Emission pro Protocol-Adapter-
Familie).

### `GG-SAFE-004` — `max_age`-stale-Markierung

**Lastenheft-Akzeptanz (Z. 1373-1378)**: Werte deren
Simulationszeitstempel die konfigurierte `max_age`
ueberschreiten erhalten deterministisch den Qualitaetsstatus
`stale`.

**Status**: ✓ **Produktiv** (M7-Welle-3a-C2, 2026-06-11;
[ADR 0052](../plan/adr/0052-max-age-stale-quality-stage.md)):

- **`STALE`-Stage im TickLoop-Spine**
  (`hexagon/core/simulation/tick_loop.py::_apply_max_age_stage`):
  unmittelbar vor dem `TickResult`-Bau wird jeder gesammelte
  `TelemetryPoint` geprueft — `(now - point.simulation_time) >
  max_age_ms` (strikt `>`; Gleichheit ist nicht „ueberschritten")
  flippt die Quality via `dataclasses.replace` auf
  `Quality.STALE`. Eine Stelle, drei Konsumenten: Live-Stream,
  Persistenz und Replay sehen identisch markierte Punkte.
- **Konfiguration**: keyword-only Kwarg `max_age_ms: int | None
  = None` am `TickLoop`-Konstruktor + `TickLoopWiring`/
  `build_tick_loop`-Symmetrie. `None` (Default) = Stage aus;
  `<= 0` → typisierter `TickLoopInvalidMaxAgeMsError`. Bewusst
  **kein** Scenario-Schema-Feld (Hash-Pin-Schutz; ADR 0052 §2.1).
- **Severity-Override**: `STALE` (Severity 3) ersetzt nur
  `VALID`/`ESTIMATED`/`LIMITED` (0..2); schwerere Befunde
  (`FAULT_INJECTED`/`INVALID`/`NAN`/`MISSING`) dominieren.
- **Determinismus**: Vergleich nur ueber Sim-Zeit (`AC-NO-TIME`
  gewahrt) — zwei gleich-konfigurierte Laeufe markieren
  identische Punkte.
- **Bewusste Grenze** (ADR 0052 §6): heutige produktive Devices
  emittieren frische Punkte (Alter 0); das Demo-Wiring laesst
  die Stage aus (`None`), weil keine konkrete Stakeholder-
  Schwelle existiert. Der Akzeptanz-Beleg lebt im reaktivierten
  Smoke + den Unit-Boundary-Tests mit nachlaufenden
  Test-Emittern.
- Beleg: `tests/integration/test_m6_welle_5a_safe_001_004_smoke.
  py::test_safe_004_stale_data_quality_after_max_age`
  (reaktiviert) + `tests/unit/hexagon/core/simulation/
  test_tick_loop_welle_3a_max_age.py`.

---

## Quality-Enum-Referenz

`hexagon/core/domain/quality.py` definiert die acht
Qualitaetsstatuswerte (`GG-DATA-003`):

- `VALID` (Severity 0): regulaerer Mess-Wert.
- `STALE` (3): veraltet (`GG-SAFE-004`; ✓ produktiv seit
  M7-Welle-3a via `max_age`-Stage, ADR 0052).
- `ESTIMATED` (1): geschaetzt.
- `LIMITED` (2): clipped/limited (Device-Saturation).
- `INVALID` (5): semantisch ungueltig (`GG-SAFE-001`).
- `NAN` (6): NaN/Inf (`GG-SAFE-002`; produktiv ueber
  `canonical_json`-Reject statt Enum-Emission).
- `MISSING` (7): fehlend (`GG-SAFE-003`; partial Lücke).
- `FAULT_INJECTED` (4): durch Fault-Injection markiert.

`QUALITY_SEVERITY`-Ranking siehe `hexagon/core/domain/quality.
py:33-42`.

---

## Verwandte Triggers

- [`open/034-safe-004-max-age-stale-quality.md`](../plan/planning/open/034-safe-004-max-age-stale-quality.md)
  — `GG-SAFE-004` Lücke; **aufgeloest via M7-Welle-3a**
  (Trigger-Close mit 3a-C3/C4a).
- [`open/035-safe-003-comm-failure-missing-quality.md`](../plan/planning/open/035-safe-003-comm-failure-missing-quality.md)
  — `GG-SAFE-003` partial Lücke (Active in M7-Welle-3b).

## Verwandte ADRs

- [ADR 0014](../plan/adr/0014-battery-snapshot-schema.md) +
  [0016](../plan/adr/0016-pv-load-device-pattern.md) +
  [0017](../plan/adr/0017-grid-connection-device-pattern.md) +
  [0018](../plan/adr/0018-smart-meter-device-pattern.md) —
  Device-Quality-Emission-Pattern.
- [ADR 0021](../plan/adr/0021-scenario-loader-and-tick-loop-event-wiring.md)
  — Scenario-Loader-Validierungs-Substanz.
- [ADR 0022](../plan/adr/0022-fault-injection-protocol.md) +
  [0025](../plan/adr/0025-fault-recovery-pattern.md) —
  Fault-Injection-`FAULT_INJECTED`-Quality.
- [ADR 0040](../plan/adr/0040-alarm-aggregation-and-stream-port.md)
  — Alarm-Emission via `AlarmStreamPort`.
- [ADR 0052](../plan/adr/0052-max-age-stale-quality-stage.md)
  — `max_age`-`STALE`-Stage (`GG-SAFE-004`, M7-Welle-3a).
