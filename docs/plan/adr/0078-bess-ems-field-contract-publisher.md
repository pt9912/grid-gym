# ADR 0078 — bess-ems-konformer Field-Publisher: Tick-Frame-Aggregation + Feldvertrags-Encoder

**Status:** Proposed (2026-07-13) — die **Richtung** ist entschieden (ein zweiter,
opt-in tick-frame-aggregierender Encoder in der Driver-Schicht, der grid-gyms
Battery-Telemetrie in den bess-ems-Feldenvelope uebersetzt), die Implementierung steht
aus. Konsumiert die Emissionen aus [`ADR 0077`](0077-battery-field-envelope-completeness.md).
**Datum:** 2026-07-13
**Bezug:**

- [`ADR 0075`](0075-field-server-surface-device-endpoint-port.md) §2.1/§2.2/§7 — die
  Field-Server-Push-Seite (`FieldPublishPort`, **per-Punkt**) + der Placement-Vertrag
  (Fan-out lebt im **API-Prozess-Driver**, nicht im Kern-`TickLoop`); dieser ADR ist
  die bess-ems-seitige Konkretisierung der in §7 antizipierten Anbindung.
- [`ADR 0077`](0077-battery-field-envelope-completeness.md) — die Battery-Emissionen
  (`soh_percent`/`dc_voltage`/`reactive_power_kvar`) + Fault-Status-Surface, die dieser
  Encoder in den Envelope schreibt. **Harte Voraussetzung** (§2.5).
- [`ADR 0012`](0012-api-simulation-two-processes.md) (Fan-out im Driver, Persistenz-Bus)
  + [`ADR 0038`](0038-telemetry-stream-port.md) (Drop-Oldest-Stream ≠ die
  vollstaendige `TickResult.emitted_telemetry`, aus der der Frame aggregiert wird).
- **bess-ems-Feldvertrag** (Schwesterrepo, lokal verifiziert, **Stand v2.1.0** —
  Envelope-Schema stabil seit v2.0.0, Golden-Vektoren + Manifest-Schema seit v2.1.0):
  `config/schema/mqtt-telemetry-envelope.schema.json` (`$defs.telemetry`, 10 required
  Felder) + `config/schema/vectors/mqtt-golden-vectors.field.v1.json` (struktureller
  Abnahme-Vektor) + bess-ems' Feldvertrags-ADR (Topic-/Retain-/Suppression-/Kadenz-Semantik).
- [`GG-TEST-004`](../../../spec/lastenheft.md#gg-test-004) (HIL/SUT-Konsum) +
  [`GG-SAFE-007`](../../../spec/lastenheft.md#gg-safe-007) (Nur-Sim-Netz).

---

## 1. Kontext

`bess-ems` konsumiert **einen breiten Telemetrie-Snapshot je Tick+Asset** auf
`battery/{assetId}/telemetry` (ein JSON-Objekt, zehn snake_case-Felder). grid-gyms
Push-Seite ([`ADR 0075`](0075-field-server-surface-device-endpoint-port.md)) publisht
heute je **schmalem Punkt** auf `{topic_prefix}/{device_id}/{metric}`
(`canonical_json` eines Domaenen-`TelemetryPoint`). Beide Formen sind fuer sich
korrekt; die Kopplung braucht einen **Uebersetzer auf der Feld-Seite** — die
Frame-Aggregation, die bess-ems' Feldvertrags-ADR §1 antizipiert.

Die drei physikalisch nicht adapter-erfindbaren Groessen + der Fault-Zustand kommen aus
[`ADR 0077`](0077-battery-field-envelope-completeness.md). Dieser ADR entscheidet die
**Aggregation + das Feld-Mapping + die Topic-/Kadenz-Semantik**.

---

## 2. Entscheidung

### §2.1 Zweiter opt-in Encoder in der Driver-Schicht (Frame-Aggregation)

Ein **bess-ems-konformer Publisher** als **zweiter, opt-in Encoder/Adapter** neben
`field_publish_mqtt`. Der bestehende schmale Punkt-Publisher bleibt **unveraendert**;
**ohne Konfiguration byte-identisch** (dieselbe Invariante wie 073/074/075).

- **Placement: Driver-Schicht.** Dort liegt der Telemetrie-Fan-out und
  `TickResult.emitted_telemetry` ist je Tick **vollstaendig** sichtbar
  ([`ADR 0075`](0075-field-server-surface-device-endpoint-port.md) §2.3); der Encoder
  aggregiert alle Punkte eines `(device, tick)` zu **einem** breiten Objekt und flusht
  am Tick-Ende. **`FieldPublishPort` selbst bleibt per-Punkt**
  ([`ADR 0075`](0075-field-server-surface-device-endpoint-port.md) §2.2) — die
  Frame-Bildung ist Driver-, keine Port-Aenderung.
- Quelle ist `TickResult.emitted_telemetry` (vollstaendig), **nicht** der
  Drop-Oldest-[`ADR 0038`](0038-telemetry-stream-port.md)-Stream.

### §2.2 Feld-Mapping (Battery-Metrik → Envelope-Feld)

Adapter-seitige Uebersetzung je `battery`-Device und Tick:

| Envelope-Feld | Quelle / Regel |
| --- | --- |
| `offset_millis` (**integer**) | `simulation_time` (ms seit Lauf-Start, Relativ-Offset — semantisch deckungsgleich) |
| `soc_percent` | `soc_pct` (Umbenennung) |
| `active_power_kw` | **`−power_kw`** — Vorzeichen-Flip: grid-gym laedt mit **+** ([`ADR 0077`](0077-battery-field-envelope-completeness.md)-Modell), der Golden-Vektor `telemetry-charging` zeigt Laden als **`active_power_kw: −250.5`** |
| `dc_voltage` | `dc_voltage` ([`ADR 0077`](0077-battery-field-envelope-completeness.md) §2.3) |
| `dc_current` | **abgeleitet** `= active_power_kw·1000 / dc_voltage` (P=V·I; Vorzeichen folgt `active_power_kw`) |
| `soh_percent` | `soh_percent` ([`ADR 0077`](0077-battery-field-envelope-completeness.md) §2.2) |
| `reactive_power_kvar` | `reactive_power_kvar` ([`ADR 0077`](0077-battery-field-envelope-completeness.md) §2.4) |
| `temperature_celsius` | `temperature_celsius` ([`ADR 0065`](0065-battery-thermal-telemetry-pattern.md)) |
| `available` / `fault_status` | Fault-Status-Surface ([`ADR 0077`](0077-battery-field-envelope-completeness.md) §2.5) |

**Encoding.** Werte kommen als JSON-**Zahlen** an (`canonical_json`-Fixed-Point ist
kompatibel; `Decimal`-als-String waere ein Typ-Bruch gegen das Schema); `offset_millis`
als JSON-**integer**. `available` als JSON-`boolean`, `fault_status` als String.

**`dc_current`-Ableitung + Golden (Review-Fund, praezisiert).** Die Ableitung nutzt
die **Frame-eigene** `dc_voltage` (die momentane Klemmenspannung, nicht die nominale) —
`dc_current = active_power_kw·1000 / dc_voltage`. **Gegen den Golden ist nur das
Vorzeichen gepinnt, nicht der Wert:** der `telemetry-charging`-Vektor ist in sich
**nicht** konsistent (`−250.5 kW·1000 / 798.5 V ≈ −313.7 A`, der Vektor nennt aber
`−313.1`; `−313.1` ergibt sich nur aus **800 V nominal**, auf eine Dezimale gerundet).
Da S3 nur **strukturell** vergleicht (§2.6), bricht das keinen Test — aber der ADR
behauptet **nicht** Wertgleichheit. Die offene Frage „Frame-`dc_voltage` vs. nominal in
der Ableitung" (Antwort hier: **Frame**, P=V·I mit momentaner Spannung) wird mit der
Vorzeichen-Rueckbestaetigung ans bess-ems-Team gebuendelt (§6/Slice-Risiken).

### §2.3 Topic-Schema + ID-Mapping

- `battery/{assetId}/telemetry` — **retained**, alle 10 Felder.
- `battery/{assetId}/status` — **retained**, `{available, fault_status, offset_millis}`.
- `battery/{assetId}/fault` — **non-retained**, `{fault_status, offset_millis}`, **nur**
  wenn `fault_status ∉ {ok, ""}` (sonst **keine** Nachricht auf dem Draht —
  Golden-Fall `fault-suppressed-ok`).
- `device_id ↔ asset_id`-Zuordnung **konfigurierbar** (Default: identitaet).

### §2.4 Kadenz (Wall-Clock-Pacing)

bess-ems misst Telemetrie-Frische **beim Empfang** (`InMemorySnapshotStore`,
**Default 10 s**, seit bess-ems v2.1.0 via `Bess:SnapshotMaxAge` konfigurierbar —
§5.1 umgesetzt; das Risiko bleibt der 10-s-Default, nicht mehr eine Hartkodierung).
Der Publisher muss
**kontinuierlich innerhalb des Fensters** publizieren (Wall-Clock-getaktet, wie der
Driver-Tick-Loop bereits laeuft), sonst laeuft das EMS in Dauer-Safe-Stop. Das Pacing
ist **exogen** (Wall-Clock) — es geht **nicht** in den Determinismus-Vertrag ein
(dieselbe Ehrlichkeit wie die Push-Seite: der Feld-Feed ist ein optionaler Add-on, die
Sim ist primaer).

### §2.5 Harte Voraussetzung: die Envelope-Pflichtfelder brauchen die 0077-Bloecke

Der Envelope verlangt **alle** zehn Felder (`required`), darunter
`temperature_celsius`/`soh_percent`/`dc_voltage`/`reactive_power_kvar` — in grid-gym
**opt-in** ([`ADR 0077`](0077-battery-field-envelope-completeness.md) + `ThermalConfig`).
Ein konformer Frame ist nur bildbar, wenn diese Bloecke **aktiv** sind. Darum:
**fail-fast bei Konstruktion** — ist der bess-ems-Encoder fuer ein `asset_id`
konfiguriert, dessen Battery **nicht** die vollstaendigen Feldbloecke traegt, wirft der
Composition-Root einen typisierten Konfig-Fehler (statt still ein Schema-invalides Frame
zu senden). Kein Adapter-Default fuer Pflicht-Physik (User-Entscheid „voll
modelliert", [`ADR 0077`](0077-battery-field-envelope-completeness.md) §1).

### §2.6 Abnahme

- Jeder emittierte `telemetry`-Frame **validiert** gegen
  `mqtt-telemetry-envelope.schema.json` (`$defs.telemetry`).
- Frames/Nachrichten vergleichen **strukturell** (feld-normativ: Namen/Praesenz/Typen/
  Null-Weglassung; **nicht** wertgenau/byte-Reihenfolge) gegen
  `mqtt-golden-vectors.field.v1.json` (liegt lokal vor).
- **E2E:** `bess-ems` im MQTT-only-SUT-Modus gegen grid-gym verlaesst den
  Safety-Fallback + faehrt Regelzyklen (heute nur gegen dessen `bess-field-sim` belegt);
  der `fault`-Pfad wird ueber einen injizierten Battery-Fault
  ([`ADR 0077`](0077-battery-field-envelope-completeness.md) §2.5) real exercisiert.

### §2.7 Determinismus + Snapshot-Grenze

Der Encoder ist eine **zustandslose Projektion** von `TickResult.emitted_telemetry` +
der Fault-Surface (kein Snapshot-Slot, wie die Push-Seite,
[`ADR 0075`](0075-field-server-surface-device-endpoint-port.md) §2.5). Das
Wall-Clock-Pacing ist exogen. Ohne Konfiguration byte-identisch.

### §2.8 Sim-/Test-Charakter + Sicherheit

MQTT ohne Auth/TLS → **Nur-Sim-Netz** ([`GG-SAFE-007`](../../../spec/lastenheft.md#gg-safe-007));
keine produktive Anlagensteuerung. Der Sim-/Testcharakter steht im Adapter-Docstring.

### §2.9 Minimales `command_ack`-Empfangs-Echo (Review-Fund 1, entschieden: Option b)

Der bess-ems-Encoder **subscribed** `battery/{assetId}/command` und **published** auf
`battery/{assetId}/command/ack` (non-retained) ein **Always-Accept**-`command_ack`:
`{command_id` (aus dem empfangenen Command echoed)`, accepted: true, dispatched_at`
(Wall-Clock)`, reason: "accepted"}` — deckt `$defs.command_ack` (required
`command_id`/`accepted`/`dispatched_at`) + den field-authority-Golden-Case
`command-ack-accepted-echo`.

**Echo ≠ Feldeffekt (die tragende Grenze).** grid-gym **wirkt nicht** auf den
`command` (kein Sollwert-Effekt ueber MQTT); der Sollwert-**Effekt**-Pfad bleibt
Modbus ([`ADR 0076`](0076-inbound-write-exogenous-input-recording.md)/Slice 075). Das
Echo ist ein reines **Empfangs-Ack**, das bess-ems' `MqttCommandSink` davon abhaelt,
in `Failed("ack-timeout")` → Safety-Fallback zu laufen (macht den S3-DoD „EMS verlaesst
den Fallback" bestehbar). **Warum in Scope trotz CR-Nicht-Ziel:** die Quelle (bess-ems
wartet aktiv auf ein Ack; der publizierte Golden erwartet das Echo) widerlegt die
CR-Annahme „telemetry-read-only"; das **verfeinerte** Nicht-Ziel ist „kein command-
**Wirkung**", nicht „kein Ack".

**Determinismus unberuehrt:** `dispatched_at` ist Wall-Clock (**exogen**, wie das
Pacing §2.4); kein Snapshot-State. Ohne konfigurierten Encoder byte-identisch.

---

## 3. Begruendung

- **Frame-Aggregation im Driver, nicht im Port.** Der Envelope ist ein
  Tick-Frame-Konzept; `FieldPublishPort` bleibt per-Punkt
  ([`ADR 0075`](0075-field-server-surface-device-endpoint-port.md) §2.2) — die
  Aggregation dort, wo `TickResult` vollstaendig ist (Driver), vermeidet einen
  Port-Vertrags-Bruch.
- **Golden-Vektor als Oracle.** Vorzeichen-Flip + `dc_current`-Ableitung sind gegen den
  publizierten `telemetry-charging`-Vektor gepinnt (nicht aus der — dort offenen —
  ADR-Prosa geraten).
- **Fail-fast statt Schema-invalider Frames.** Die opt-in/Pflicht-Spannung (grid-gym
  opt-in vs. Envelope required) wird bei Konstruktion aufgeloest, nicht auf dem Draht.
- **Additiv/opt-in.** Der Bestands-Punkt-Publisher bleibt unberuehrt; ohne den zweiten
  Encoder byte-identisch.

---

## 4. Alternativen

- **`FieldPublishPort` frame-basiert machen (verworfen):** braeche den per-Punkt-Vertrag
  ([`ADR 0075`](0075-field-server-surface-device-endpoint-port.md) §2.2) + die anderen
  Push-Konsumenten. Aggregation ist eine Driver-, keine Port-Sache.
- **Per-Punkt publizieren, bess-ems reassembliert (verworfen):** bess-ems erwartet
  **einen** breiten Frame je Tick; die Reassemblierung dort widersprache dessen
  publiziertem Vertrag (bess-ems' Feldvertrags-ADR §1).
- **Adapter-Defaults fuer die Pflicht-Physik (verworfen):** siehe
  [`ADR 0077`](0077-battery-field-envelope-completeness.md) §4 (Safe-Stop-E2E waere
  nicht belegbar).

---

## 5. Lieferschnitt

Design-first (diese ADR); Implementierung im [`Slice 077`](../planning/in-progress/077-bess-ems-conformant-field-publisher.md)-S2
(Encoder + Feld-Mapping + Topics + Kadenz + Wiring) nach S1
([`ADR 0077`](0077-battery-field-envelope-completeness.md)-Emissionen). S3 = Abnahme
(Schema + Golden-Vektoren + bess-ems-E2E).

---

## 6. Konsequenzen

- **Positiv:** ein externes, unveraendertes EMS (`bess-ems`) konsumiert grid-gym als
  simuliertes Feld ([`GG-TEST-004`](../../../spec/lastenheft.md#gg-test-004)); die
  Kopplung ist gegen den publizierten Vertrag (Schema + Golden) abgenommen.
- **Neutral:** ein zweiter Encoder + `device_id↔asset_id`-Config + Wall-Clock-Pacing.
- **Bewusste Grenze:** telemetry-read-only (kein MQTT-`command`-Konsum, §7); der
  konforme Encoder verlangt die vollen 0077-Feldbloecke (§2.5).

---

## 7. Nicht Gegenstand dieser ADR

- **MQTT-`command`-Feldeffekt** — grid-gym **wirkt** nicht auf einen MQTT-`command`
  (der Sollwert-Schreibpfad ist Modbus, [`ADR 0076`](0076-inbound-write-exogenous-input-recording.md)/Slice 075).
  Ein **Empfangs-Ack-Echo** (kein Effekt) ist dagegen in Scope — §2.9 (Review-Fund 1,
  **entschieden: Option b**, damit der S3-DoD bestehbar ist).
- **Die Emissionsmodelle** (soh/dc_voltage/reactive/Fault-Surface) —
  [`ADR 0077`](0077-battery-field-envelope-completeness.md).
- **Aenderung am schmalen Punkt-Publisher** (`field_publish_mqtt`) — bleibt unveraendert.
- **Produktivanspruch** — Nur-Sim-Netz ([`GG-SAFE-007`](../../../spec/lastenheft.md#gg-safe-007)).
