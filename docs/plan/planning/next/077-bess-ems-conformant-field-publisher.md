# 077 — bess-ems-konformer Feld-Publisher (breiter Snapshot je Tick)

**Status:** **Next — S0 (Design/ADRs) done, S1/S2/S3 offen.** grid-gym-seitige
Haelfte der bess-ems-Kopplung ([`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md)
§7, [`GG-TEST-004`](../../../../spec/lastenheft.md#gg-test-004)). Aktiviert aus einem
externen Change-Request (Schwesterprojekt `bess-ems`).
**Datum:** 2026-07-13
**Quelle:** `bess-ems` **v2.1.0** (Envelope-Schema stabil seit v2.0.0; die Golden-
Vektoren + das Manifest-Schema kamen erst mit v2.1.0 — der CR-Pin „v2.0.0" war stale,
Review-Fund 2) — Feldvertrag lokal verifiziert
(`config/schema/mqtt-telemetry-envelope.schema.json` +
`config/schema/vectors/mqtt-golden-vectors.field.v1.json` + bess-ems' Feldvertrags-ADR).
„Voll modelliert" (User-Entscheid 2026-07-13): echte Battery-Emissionen statt
Adapter-Defaults.

---

## Ziel

Ein externes, **unveraendertes** EMS (`bess-ems`) konsumiert grid-gym als simuliertes
Feld ueber MQTT: **ein breiter Telemetrie-Snapshot je Tick+Asset** auf
`battery/{assetId}/telemetry` (10-Feld-Envelope) + `status`/`fault`-Topics. Der
bestehende schmale Punkt-Publisher (`field_publish_mqtt`) bleibt unveraendert; ohne
Konfiguration byte-identisch (Invariante 073/074/075).

## Kontext / Ist

- 073/074/075 (v0.5.0/v0.6.x) lieferten die Field-Server-Surface: `FieldPublishPort`/
  MQTT-**per-Punkt**-Push, `DeviceServerPort`/Modbus Read + Inbound-Write. bess-ems
  konsumiert aber **einen breiten Frame je Tick** (zehn snake_case-Felder), nicht je
  Punkt — die Kopplung braucht einen Feld-seitigen Aggregator/Uebersetzer.
- grid-gyms Battery emittiert heute `power_kw`/`soc_kwh`/`soc_pct` + opt-in
  `temperature_celsius`/`cell_voltage_delta_v`; sechs Envelope-Felder fehlen bzw. sind
  abzuleiten/umzubenennen.
- Der bess-ems-Vertrag ist **von deren Seite vollstaendig + maschinenlesbar** (Schema +
  Golden-Vektoren liegen lokal vor — entgegen „in Arbeit" im CR).

## Kern-Decision (S0)

Zwei ADRs (Buendelung der Physik, getrennt vom Publisher — User-Entscheid):

- [`ADR 0077`](../../adr/0077-battery-field-envelope-completeness.md) (`Proposed`) —
  **Battery-Field-Envelope-Vollstaendigkeit:** drei additive opt-in Emissionen
  (`soh_percent`/HealthConfig, `dc_voltage`/DcBusConfig, `reactive_power_kvar`/
  ReactiveConfig; Muster [`ADR 0065`](../../adr/0065-battery-thermal-telemetry-pattern.md)/[`ADR 0066`](../../adr/0066-battery-cell-voltage-telemetry-pattern.md))
  + Fault-Status-Surface (`available`/`fault_status` aus den `_<fault>_active`-Flags).
  Modelle simpel/deterministisch, Default = konstant; `dc_bus`↔`cell`-Nennspannung
  validiert.
- [`ADR 0078`](../../adr/0078-bess-ems-field-contract-publisher.md) (`Proposed`) —
  **Field-Contract-Publisher:** zweiter opt-in Encoder in der Driver-Schicht
  (Tick-Frame-Aggregation aus `TickResult.emitted_telemetry`; `FieldPublishPort` bleibt
  per-Punkt). Feld-Mapping inkl. **Vorzeichen-Flip** `active_power_kw = −power_kw` +
  **abgeleitetem** `dc_current = active_power_kw·1000/dc_voltage` (beides gegen den
  Golden-Vektor `telemetry-charging` gepinnt). Topics/Retain/Suppression/Kadenz;
  fail-fast, wenn die 0077-Bloecke fehlen (kein Adapter-Default fuer Pflicht-Physik).

## Slice-Schnitt

| Slice | Inhalt | Rolle / Artefakt |
| --- | --- | --- |
| **S0** ✓ | [`ADR 0077`](../../adr/0077-battery-field-envelope-completeness.md) + [`ADR 0078`](../../adr/0078-bess-ems-field-contract-publisher.md) (`Proposed`): Physik-Modelle + Feldvertrags-Encoder design-first, gegroundet gegen den lokal verifizierten bess-ems-Vertrag (Schema + Golden-Vektoren) | Architect / ADR |
| **S1** | **Battery-Emissionen ([`ADR 0077`](../../adr/0077-battery-field-envelope-completeness.md)):** `HealthConfig`/`DcBusConfig`/`ReactiveConfig`-Bloecke + `soh_percent`/`dc_voltage`/`reactive_power_kvar`-Emissionen + `fault_status`/`available`-Properties; Snapshot-Slots (`_soh_pct`/`_efc`); `dc_bus`↔`cell`-Validierung. Additiv/opt-in (pin-neutral), unit-getestet. **→ ADRs `Provisional`** | Implementation |
| **S2** | **Field-Contract-Publisher ([`ADR 0078`](../../adr/0078-bess-ems-field-contract-publisher.md)):** tick-frame-aggregierender bess-ems-Encoder (Driver-Schicht) + Feld-Mapping (Flip/derive/rename) + `telemetry`/`status`/`fault`-Topics (Retain + Suppression) + `device_id↔asset_id`-Config + Wall-Clock-Kadenz + fail-fast-Wiring. Opt-in, ohne Config byte-identisch | Implementation |
| **S3** | **Abnahme:** JSON-Schema-Validate je Frame (`mqtt-telemetry-envelope.schema.json`) + **struktureller** Golden-Vektor-Vergleich (`mqtt-golden-vectors.field.v1.json`) + bess-ems-MQTT-only-E2E (EMS verlaesst Safety-Fallback, `fault`-Pfad via injiziertem Battery-Fault). **Closure → ADRs `Accepted`** | Implementation |

## DoD

- Jeder `telemetry`-Frame validiert gegen den publizierten Envelope-Schema; Frames
  vergleichen strukturell gegen die Field-Golden-Vektoren.
- `bess-ems` im MQTT-only-SUT-Modus verlaesst den Safety-Fallback + faehrt Regelzyklen
  gegen grid-gym; der `fault`-Topic feuert bei injiziertem Battery-Fault.
- Additiv/opt-in: ohne konfigurierten bess-ems-Encoder + Feldbloecke byte-identisch
  (Demo-Hash-Pins + `scenario_hash` unberuehrt).
- `make gates` + `make docs-check` + `make fullbuild` gruen.
- **Release-Entscheidung:** ja (Minor); SemVer-Ziel naechster Minor.

## Bezug

- [`ADR 0077`](../../adr/0077-battery-field-envelope-completeness.md) (Physik-Modelle +
  Fault-Surface) + [`ADR 0078`](../../adr/0078-bess-ems-field-contract-publisher.md)
  (Aggregation + Feldvertrag).
- [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) §7
  (Anbindungs-Antizipation) + [`ADR 0012`](../../adr/0012-api-simulation-two-processes.md)
  (Driver-Fan-out).
- [`GG-TEST-004`](../../../../spec/lastenheft.md#gg-test-004) (HIL/SUT) +
  [`GG-SAFE-007`](../../../../spec/lastenheft.md#gg-safe-007) (Nur-Sim-Netz).
- Vorgaenger-Arc: 073/074/075 (Field-Server-Surface).

## Risiken

- **`command_ack`-Echo / S3-Bestehbarkeit (Review-Fund 1, HOECHSTE — Entscheidung
  ausstehend).** bess-ems' `MqttCommandSink` published Commands + wartet 2 s auf ein
  Ack → ohne Ack `Failed("ack-timeout")`; der field-authority-Golden erwartet ein
  Always-Accept-Echo (`command-ack-accepted-echo`); bess-ems' Feldvertrags-ADR §6
  markiert die EMS-Ack-Toleranz als **unverifiziert**. Blockiert ein Dispatch-Failure
  die Regelzyklen, ist der S3-DoD nicht bestehbar. **Optionen:** (a) No-Ack-Smoke frueh,
  (b) minimales Always-Accept-Echo in S2, (c) DoD abschwaechen. Muss **vor S2**
  entschieden werden ([`ADR 0078`](../../adr/0078-bess-ems-field-contract-publisher.md) §7).
- **Vorzeichen + `dc_current`-Ableitung** — beides im bess-ems-Schema/ADR **nicht**
  spezifiziert, aus dem Golden abgeleitet (Laden = `−active_power_kw`; `dc_current` mit
  **Frame**-`dc_voltage`, P=V·I). Der Golden ist wertlich in sich inkonsistent
  (`−250.5/798.5≈−313.7` vs. Vektor `−313.1`) → nur Vorzeichen gepinnt (Review-Fund 4).
  Beides mit **einer** Rueckbestaetigung ans bess-ems-Team gebuendelt; kein Blocker (S3
  vergleicht strukturell).
- **Kadenz/Wall-Clock** — `SnapshotMaxAge`-**Default 10 s** (seit v2.1.0 via
  `Bess:SnapshotMaxAge` konfigurierbar, §5.1 umgesetzt — Review-Fund 3); der Publisher
  muss kontinuierlich innerhalb des Fensters pacen, sonst EMS-Dauer-Safe-Stop.
- **opt-in/Pflicht-Spannung** — der Envelope verlangt alle 10 Felder; grid-gyms Physik
  ist opt-in → fail-fast-Wiring statt Schema-invalider Frames
  ([`ADR 0078`](../../adr/0078-bess-ems-field-contract-publisher.md) §2.5).

## Nicht-Ziele

- **Kein** MQTT-`command`/`command_ack`-Konsum (bess-ems haelt den Command-Loop deferred;
  Schreib-Richtung existiert ueber Modbus/[`075`](../done/075-field-server-inbound-write-command.md)).
- **Keine** Aenderung am schmalen Punkt-Publisher (`field_publish_mqtt`).
- **Kein** Produktivanspruch ([`GG-SAFE-007`](../../../../spec/lastenheft.md#gg-safe-007)).

## Aktivierung

Change-Request extern (bess-ems v2.1.0). S0 (ADRs) done 2026-07-13. Nach ADR-Runde +
User-Go → `in-progress/` (S1 Battery-Emissionen zuerst, dann S2 Publisher, S3 Abnahme).
