# 073 — Field-Server MQTT-Publish-Bridge (`FieldPublishPort`, Push)

**Status:** **Aktiv — in Arbeit (seit 2026-07-12).** Bleibt in `next/` bis zur
Closure → dann Self-Move nach `done/` (Muster Slice 070/071/072, kein
`in-progress/`-Zwischenstopp). Liefert die Field-Server-Push-Seite aus
[`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md)
(`Proposed`); ADR wird bei **073-Closure** auf `Provisional` gezogen.
**Fortschritt:** C0 ✓ · C1 ✓ · C2/C3/C4 offen.
**Datum:** 2026-07-12
**Quelle:** Architektur-Sichtung 2026-07-12 (alle fuenf Protokolladapter sind
Client/Master, [`ADR 0030`](../../adr/0030-device-protocol-port-surface.md)) +
zwei adversariale Reviews, die den ersten Entwurf (ein geteilter Port am
Kern-`TickLoop`) verwarfen.

---

## Ziel

Die **Push-Seite** der Field-Server-Surface liefern und die **Kompositions-
Schicht-Naht** + das grid-gym↔`bess-ems`-Integrationsgeschirr etablieren:
`FieldPublishPort` (driven) + ein MQTT-Publish-Adapter, der emittierte
Geraetetelemetrie an einen Broker exponiert. Niedrigstes Risiko: reiner Publish,
kein Listening-Socket, keine Register-Map.

**Bewusst NICHT Ziel** (Review-Korrektur): dieser Slice baut **keine** Current-
Value-Projektion und macht [`074`](074-field-server-modbus-server-adapter.md)
**nicht** „duenn" — Push und Pull sind verschiedene Rollen (Schwester-Ports,
[`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) §2.1).
Was 073 fuer 074 vor-entlastet, ist die **Integrations-Plumbing + Driver-
Lifecycle-Verdrahtung**, nicht die Pull-Foundation.

## Kontext / Ist

- Der Telemetry-Fan-out lebt **im API-Prozess-Driver**
  (`_tick_loop_driver._publish_emitted_telemetry` liest
  `TickResult.emitted_telemetry`), **nicht** im Kern-`TickLoop`; per
  [`ADR 0012`](../../adr/0012-api-simulation-two-processes.md) laeuft der
  Kern-Loop produktiv im `simulation`-Worker. Deshalb wird der Field-Publish
  **wie `telemetry_stream`/`alarm_stream`** in der Driver-Schicht verdrahtet
  ([`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md)
  §2.3) — **kein** Kern-Kwarg.
- Die driven-`protocol_mqtt`-Client-Rolle (`client.publish()` gegen einen
  externen Broker, um Geraete **anzusteuern**) ist eine andere Rolle: hier
  exponiert grid-gym **eigenen** simulierten Zustand.
- **`start_protocol_ports()` wird produktiv nie aufgerufen** (nur in Tests) —
  die Field-Publish-Lifecycle-Verdrahtung ist echte neue Driver-Arbeit (C2),
  kein `protocol_ports`-Copy-Paste.

## Kern-Decision ([`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md))

`FieldPublishPort` (driven, `publish(point)`, §2.1) in der Kompositions-/Driver-
Schicht (§2.3); Lifecycle connect+publish mit `None`-Skip (§2.4); Replay ohne
Broker-Connect, byte-identisch ohne Port (§2.5); Sim-/Test-Deployment-Note
(§2.6). Telemetrie-out-only.

## Slice-Schnitt (rollen-getrennt)

| Slice | Inhalt | Rolle / Artefakt |
| --- | --- | --- |
| **C0** ✓ | [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) §2.1 geschaerft: `FieldPublishPort.publish(point)` nutzt den **Domaenen**-`TelemetryPoint` ([`GG-DATA-001`](../../../../spec/lastenheft.md#gg-data-001), wie `DeviceProtocolPort` — kein driven→driving-Import, volle `Decimal`-Fidelity), `start()`/`stop()`-Lifecycle driver-getrieben. ADR bleibt `Proposed` (→ `Provisional` bei 073-Closure, Muster [`ADR 0030`](../../adr/0030-device-protocol-port-surface.md)). Anforderungs-Verankerung = HIL-Konkretisierung von [`GG-TEST-004`](../../../../spec/lastenheft.md#gg-test-004) (keine eigene `GG-*`-ID; [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) §7) | Architect / ADR |
| **C1** ✓ | `hexagon/ports/driven/field_publish.py` (`FieldPublishPort`-Protocol `start`/`publish`/`stop`, Stub-Form Docstring + `...` eigene Zeile) + `*Error`-Hierarchie (`FieldPublishPortError`-Familie). Domaenen-`TelemetryPoint` (kein driving-Import) | Implementation |
| **C2** | **Produktions-Driver-Verdrahtung:** Field-Publish-Fan-out + Lifecycle-Caller im http_api-Driver (analog `_publish_emitted_telemetry`), Field-Server-Entrypoint in der App-Komposition. Pins: `None`-Skip byte-identisch, Lifecycle-Start/Stop im echten Run-Pfad (nicht nur test-lokal) | Implementation |
| **C3** | `adapters/driven/field_publish_mqtt/` — MQTT-Publish-Adapter (paho-mqtt, adapter-interner Loop/Queue), Topic-Schema, typisierte Fehler, Sim-/Test-Docstring + Nur-Sim-Netz-Note ([`GG-SAFE-007`](../../../../spec/lastenheft.md#gg-safe-007)). Unit: Publish-Mapping, Fehleruebersetzung | Implementation |
| **C4** | **Integrationsgeschirr gegen den Produkt-Surface:** Compose mit Broker (Mosquitto-Sibling) + grid-gym-API-Container + ein Subscriber-Assert-Loop (Platzhalter fuer `bess-ems`) — externer Konsument empfaengt die exponierte Telemetrie. testcontainers | Implementation |

## DoD

- Ein Run mit konfiguriertem `FieldPublishPort` published emittierte
  `TelemetryPoint`s an den Broker ueber den **Produktions**-Driver-Pfad; ein
  externer Subscriber empfaengt sie (C4 gruen).
- Determinismus/Replay: kein Field-Publish-Port → **byte-identisch** zu heute
  (kein Broker-Connect, keine Snapshot-Aenderung;
  [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) §2.5).
- Pin-neutral: alle Bestands-Pins (`make accept`, `scenario_hash`, Snapshot-
  Hashes) unveraendert.
- `FieldPublishPort` haelt [`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert):
  der Adapter importiert `core.*` nicht.
- `make gates` + `make docs-check` gruen; Slice-Closure zusaetzlich
  `make fullbuild`.
- **Release-Entscheidung:** ja (Minor — additive Feature-Surface); SemVer-Ziel
  **v0.5.0** (v0.4.0 = GG-FAULT-Release 2026-07-12). Gebunden an „kein
  Doku-only-Release" + `make fullbuild` vor Tag.

## Bezug

- [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md)
  (Field-Server-Surface, §2.1/§2.3/§2.4).
- [`ADR 0012`](../../adr/0012-api-simulation-two-processes.md) (Zwei-Prozess-
  Naht) + [`ADR 0038`](../../adr/0038-telemetry-stream-port.md) (Driver-Fan-out-
  Praezedenz) + [`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md)
  ([`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)).
- [`GG-TEST-004`](../../../../spec/lastenheft.md#gg-test-004) (HIL) +
  [`GG-NONGOAL-001`](../../../../spec/lastenheft.md#gg-nongoal-001) /
  [`GG-SAFE-007`](../../../../spec/lastenheft.md#gg-safe-007) (Sim/Prod).
- Folge-Slice: [`074`](074-field-server-modbus-server-adapter.md) (Pull-Server,
  eigene Schwester-Port-Rolle).

## Entsperrt

[`074`](074-field-server-modbus-server-adapter.md) (nutzt die Kompositions-
Schicht-Naht + das Integrationsgeschirr; baut den Pull-Port + die Projektion
selbst).

## Risiken

- **paho-mqtt-Callback→Sync-Marshal** — wie bei der driven-MQTT-Client-Naht
  ([`ADR 0030`](../../adr/0030-device-protocol-port-surface.md) §2.1); hier
  einfacher, weil reiner Publish (kein `on_message`-Marshal).
- **Neue Driver-Lifecycle-Verdrahtung** (C2) — der `protocol_ports`-Lifecycle
  wird produktiv nie gerufen; C2 baut echten Run-Pfad-Code, nicht Copy-Paste.
- **Security der exponierten Surface** — Broker-Exposure ohne Auth; Nur-Sim-
  Netz-Note in C3 ([`GG-SAFE-007`](../../../../spec/lastenheft.md#gg-safe-007)).

## Aktivierung

Owner-Go (Slice scharf schalten; Anforderungs-Verankerung entschieden). Bis
dahin `next/`. Bei Aktivierung → [`../in-progress/`](../in-progress/); nach
C4-Closure + `make fullbuild` → [`../done/`](../done/).
