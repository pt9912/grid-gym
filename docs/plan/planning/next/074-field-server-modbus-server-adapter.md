# 074 — Field-Server Modbus-Server-Adapter (`DeviceServerPort`, Pull, Read-Serving)

**Status:** **Geplant (`next/`, 2026-07-12)** — konkret geplant, noch nicht
aktiv; **haengt an** [`073`](073-field-server-mqtt-publish-bridge.md)
(Kompositions-Schicht-Naht + Integrationsgeschirr). Zieht
[`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) mit
**Closure** auf `Accepted`.
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
| **C0** | Modbus-Server-Profil in einer **neuen** `DeviceServerPort`-/Server-Sektion von [`spec/protocol_profiles.md`](../../../../spec/protocol_profiles.md) (Register-Map-Schema, Unit-ID, `Decimal→float→Register`-Encode + Gleichheits-Oracle, Quality→Discrete-Input-Mapping). **Keine** Einmischung in den driven-Master-Index. [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) bleibt `Provisional` (Accepted erst bei Closure) | Architect / Profil |
| **C1a** | `hexagon/ports/driving/device_server.py` (`DeviceServerPort`) + Current-Value-**Projektion** (last-write-wins pro `(target, metric)`, tick-frame-atomar, aus `emitted_telemetry`) + Driver-Lifecycle-Verdrahtung (bind/listen, Bind-in-use hart, graceful Stop). Unit: Projektion-Semantik, Lifecycle-Failure | Implementation |
| **C1b** | `adapters/driving/device_server_modbus/` — `pymodbus`-Server (Datastore aus Projektion), adapter-interner Loop-Thread, Register-Encode (`Decimal→float→16-bit` mit definiertem Oracle), Quality→Discrete-Input/Flag-Mapping, typisierte Fehler, Sim-/Test-Docstring + Nur-Sim-Netz-Note | Implementation |
| **C2** | **Read-Pfad-E2E:** externer Modbus-Master (testcontainers) pollt Holding/Input-Register; Werte matchen die emittierte Telemetrie tick-genau **gemaess definiertem Oracle**; Quality-Marker ([`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md)) korrekt exponiert. **Closure → [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) `Accepted`** | Implementation |

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

## Aktivierung

**Nach** [`073`](073-field-server-mqtt-publish-bridge.md)-Closure. Bis dahin
`next/`. Bei Aktivierung → [`../in-progress/`](../in-progress/); nach C2-Closure
+ `make fullbuild` → [`../done/`](../done/).
