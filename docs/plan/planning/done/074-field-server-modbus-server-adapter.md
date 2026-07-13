# 074 — Field-Server Modbus-Server-Adapter (`DeviceServerPort`, Pull, Read-Serving)

**Status:** **Done (`done/`, 2026-07-12).** Baut auf
[`073`](073-field-server-mqtt-publish-bridge.md) (Push-Seite, done) auf —
nutzt die Kompositions-Schicht-Naht + das Integrationsgeschirr. Hat
[`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) mit
**Closure** auf `Accepted` gezogen (Pull-Seite belegt).
**Fortschritt:** C0 ✓ · C1a ✓ · C1b ✓ · C2 ✓ · adversarialer Review ✓ (1 HIGH float32-Tearing + 1 MEDIUM Robustheit + 3 LOW gefixt).
**Datum:** 2026-07-12
**Quelle:** [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md)
§5 — die **Pull-Seite** (echtes bind/listen/serve), die die driving-Rolle
belegt; zugleich Trager der geteilten Current-Value-Projektion.

---

## Ziel

Einen **Modbus-TCP-Server** (Slave) als `DeviceServerPort` liefern: ein externer
Modbus-**Master** (das EMS als SUT) pollt grid-gyms simulierte Geraete als
Holding-/Input-Register. **Read-Serving only.** Traeger der geteilten
**Current-Value-Projektion**, die jeder kuenftige Pull-Server teilt. Damit ist
die driving/bind-listen-Rolle belegt → [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) wird bei Closure `Accepted`.

**Bewusst NICHT Ziel:** Inbound-Write→Command — ausgegliedert in
[`075`](075-field-server-inbound-write-command.md) (bricht das geschlossene
Self-Replay, eigene Slice + Folge-ADR;
[`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) §7).

## Kontext / Ist

- Nach [`073`](073-field-server-mqtt-publish-bridge.md) existiert die
  Kompositions-Schicht-Naht (Driver-Fan-out + Lifecycle) + das
  Integrationsgeschirr. Der Pull-Server baut darauf, **aber** die Current-Value-
  Projektion + Register-Map + Encode sind **neue** Foundation (nicht „duenn" —
  Review-Korrektur).
- `TelemetryStreamPort` ist fire-and-forget mit Drop-Oldest-FIFO → als Pull-
  Quelle ungeeignet; deshalb die eigene, aus `TickResult.emitted_telemetry`
  gespeiste Projektion
  ([`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md)
  §2.2).
- Das driving-DTO traegt bereits `value: float` (lossy aus Domain-`Decimal`);
  der Register-Encode ist ein **zweiter** Verlustschritt.
- Die driven-`protocol_modbus`-Rolle ist Master
  ([`ADR 0030`](../../adr/0030-device-protocol-port-surface.md)); hier ist
  grid-gym der **Slave/Server** — die Gegenrolle.

## Kern-Decision ([`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md))

`DeviceServerPort` (driving, bind/listen/serve, §2.1) in der Kompositions-Schicht
(§2.3); Server-Lifecycle eigenstaendig — Bind-in-use = harter Fehler,
graceful Drain bei Stop (§2.4). Register-Map fuellt sich aus der geteilten
Current-Value-Projektion (last-write-wins, tick-frame-atomar, §2.2).

## Slice-Schnitt (rollen-getrennt)

| Slice | Inhalt | Rolle / Artefakt |
| --- | --- | --- |
| **C0** ✓ | **Server-Profil-Sektion** in [`spec/protocol_profiles.md`](../../../../spec/protocol_profiles.md) angelegt (**Server-Profile — `DeviceServerPort`**, getrennt vom driven-Master-Index): Register-Map `(device_id,metric)`→Adresse, `float32`-Datatype (2 Register), Quality→Discrete-Input, Read-only FC03/FC04, Unit-ID Default 1. **Encode-Oracle** festgezurrt: Vergleich gegen die **deterministische `float32`-Quantisierung** (`struct.pack/unpack('>f', float(decimal))`) statt `Decimal==decoded` (Praezisionsgrenze explizit). [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) bleibt `Provisional` (Accepted bei Closure) | Architect / Profil |
| **C1a** ✓ | `hexagon/ports/driving/device_server.py` (`DeviceServerPort`, bind/listen/serve + `*Error`) + `adapters/driving/_field_current_value.py` (`CurrentValueProjection`: last-write-wins pro `(device_id, metric)`, **lock-frei tick-frame-atomar** via Referenz-Swap, aus `emitted_telemetry`) + Driver-Wiring (`device_server_provider`/`current_value_projection`-Kwargs; `_start/_stop_device_server` via `asyncio.to_thread`, **Bind-in-use propagiert hart**; `_update_projection` pro Tick). Unit: Port-Shape, Projektion-Semantik/Atomizitaet, Lifecycle + Bind-Failure + Stop-Fehler-Swallow | Implementation |
| **C1b** ✓ | `adapters/driving/device_server_modbus/` — **pymodbus-freier Kern + Adapter-Shell**: `_config` (`ModbusServerConfig`/`RegisterMapping`, fail-fast + Overlap-Check), `_register_map` (`encode_float32` = Encode-Oracle `struct.pack('>f', float(v))` + on-demand-`RegisterMap` aus der Projektion: Holding = `float32`-2-Register-Big-Endian, Discrete-Input = Quality-`VALID`-Flag), `_errors` (typisiert, `DeviceServerPort`-Subklassen), `_adapter` (`ModbusDeviceServerAdapter` via **Runner-Injektion** + `_preflight_bind` = synchroner Bind-in-use-Hard-Error, [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) §2.4). **Kern + Lifecycle + Bind-Fehler unit-getestet** (Fake-Runner, echter Socket fuer Preflight). **Befund:** pymodbus 3.13 hat den Datastore auf `SimData`/`SimDevice` umgebaut — der alte `ModbusServerContext`/`ModbusDeviceContext`-Shim serviert **nur statisch** (`async_setValues` → `DEVICE_BUSY`, kein Live-Update). Der reale, dynamisch aus der Projektion gespeiste pymodbus-Server ist darum nur mit echtem pollenden Master verifizierbar → nach **C2** verschoben; `_default_server_runner` faehrt den realen Bind-Check + verweist fuers Serving auf C2 | Implementation |
| **C2** ✓ | **Realer pymodbus-Server + Read-Pfad-E2E:** `_default_server_runner` startet den echten pymodbus-3.13-Server im adapter-internen Loop-Thread über ein `SimDevice`/`SimCore` (non-shared Blöcke: Holding=`REGISTERS`, Discrete-Input=`BITS`); ein **Refresh-Task** pusht die on-demand aus der Projektion gerechneten `RegisterMap`-Werte via `server.async_setValues` (initialer Push vor `start()`-Freischaltung → erster Poll deterministisch; Adressierung 1:1). **Read-E2E** (`test_read_e2e.py`, `tests/unit/`): echter pymodbus-`ModbusTcpClient`-Master pollt in-Process; Holding-Register matchen `encode_float32` (Oracle) tick-genau, Quality korrekt als Discrete-Input, Update nach neuem Tick sichtbar. Quality-Marker ([`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md)) korrekt exponiert. **Closure (nach adversarialem Review) → [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) `Accepted`** | Implementation |

## DoD

- Ein externer Modbus-Master liest grid-gyms simulierte Geraetewerte als
  Register (Read-E2E gruen); ein Poll zu beliebiger Zeit sieht den letzten
  gueltigen Wert pro Metrik (Projektion, nicht Stream-Luecke).
- **Gleichheits-Oracle definiert:** der Vergleich Register-Wert ↔ Domain-Wert
  beruecksichtigt **beide** Verlustschritte (`Decimal→float`-DTO +
  `Decimal→16-bit`-Register) und ist mit den Decimal-String-Determinismus-Pins
  des Repos versoehnt.
- Determinismus/Replay: ohne `DeviceServerPort` byte-identisch; die Projektion
  ist reine Funktion der emittierten Telemetrie (kein Server-State im Snapshot,
  [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) §2.5).
- Pin-neutral: alle Bestands-Pins unveraendert.
- [`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)/[`AC-ADAPTER-LIGHTWEIGHT`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)
  gruen; Server-Stack adapter-intern gekapselt.
- `make gates` + `make docs-check` + `make fullbuild` gruen.
- **Release-Entscheidung:** ja (Minor — Pull-Server + geteilte Projektion);
  SemVer-Ziel naechster Minor nach [`073`](073-field-server-mqtt-publish-bridge.md).

## Bezug

- [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md)
  (§2.1 `DeviceServerPort`, §2.2 Projektion, §2.4 Server-Lifecycle).
- [`ADR 0030`](../../adr/0030-device-protocol-port-surface.md) (Master-
  Gegenrolle, `pymodbus`-Sync-Naht) + [`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md)
  (Quality-Marker im Frame).
- [`GG-MODB-001`](../../../../spec/lastenheft.md#gg-modb-001) (Modbus-Profil-
  Anker, driven-Seite) + [`GG-TEST-004`](../../../../spec/lastenheft.md#gg-test-004)
  (HIL) + [`GG-SAFE-007`](../../../../spec/lastenheft.md#gg-safe-007) (Nur-Sim).
- Vorgaenger: [`073`](073-field-server-mqtt-publish-bridge.md); Folge:
  [`075`](075-field-server-inbound-write-command.md) (Inbound-Write).

## Risiken

- **`Decimal→float→Register`-Doppelverlust** — der DTO-`float`-Cast **plus**
  Register-Encode; das Repo pinnt Decimal-Strings. Der Gleichheits-Oracle muss
  in C0 definiert sein, bevor Code entsteht (sonst nicht-verifizierbarer E2E).
- **Projektion-Frame-Atomizitaet** — ein Poll darf nie einen halb-aktualisierten
  Tick-Frame sehen; last-write-wins pro `(target, metric)`, atomarer Frame-Swap.
- **Auth/Security** — Modbus-TCP hat keine; Nur-Sim-Netz-Deployment-Note
  ([`GG-SAFE-007`](../../../../spec/lastenheft.md#gg-safe-007)).
- **pymodbus-3.13-Datastore-Rewrite (C1b-Befund)** — der alte
  `ModbusServerContext`/`ModbusDeviceContext`/`ModbusSequentialDataBlock`-Shim
  ist deprecated (Entfernung in v4) und serviert nur statisch
  (`async_setValues` → `DEVICE_BUSY`). C2 muss das neue `SimData`/`SimDevice`-
  Modell (ggf. `SimAction`/`ModbusSimulatorContext`) nutzen; der Adress-Offset
  (kein `zero_mode` mehr) ist per Master-E2E zu pinnen.

## Aktivierung

Aktiviert nach [`073`](073-field-server-mqtt-publish-bridge.md)-Closure
(2026-07-12), umgesetzt C0→C2 + adversarialer Review, dann nach `done/`
verschoben. [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md)
auf `Accepted` gezogen (beide Schwester-Ports belegt). Gemeinsamer
Field-Server-Release (mit [`073`](073-field-server-mqtt-publish-bridge.md))
ausstehend — Runtime-Delta unter CHANGELOG `[Unreleased]`.
