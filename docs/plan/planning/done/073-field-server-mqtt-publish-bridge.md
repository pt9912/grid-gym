# 073 — Field-Server MQTT-Publish-Bridge (`FieldPublishPort`, Push)

**Status:** **Done — geliefert 2026-07-12** (C0–C4 + adversariales
Code-Review-Hardening).
[`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) auf
`Provisional` gezogen (Push-Seite `FieldPublishPort` belegt; `Accepted` folgt mit
der Pull-Seite/074). Runtime-Delta → CHANGELOG `[Unreleased]`; **Release
deferred** bis die Pull-Seite da ist (gemeinsamer Field-Server-Release).
`make gates` 10/10 + `make docs-check` 0 + `make test-integration` 166 passed
gruen.
**Fortschritt:** C0–C4 ✓ + adversarialer Code-Review + Hardening ✓ (2026-07-12;
2 unabhaengige Reviewer, 11 Funde adressiert — s.u.) → **Closure 2026-07-12**
([`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) →
`Provisional`; Release deferred bis Pull-Seite/074).
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
Value-Projektion und macht [`074`](../next/074-field-server-modbus-server-adapter.md)
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
| **C2** ✓ | **Produktions-Driver-Verdrahtung:** Field-Publish-Fan-out (`_publish_field`, Domaenen-Point direkt) + `start`/`stop`-Lifecycle im `_run_loop` (`_start_field_publish`/`_stop_field_publish`, resolve-once + graceful Degrade bei Start-Failure) im `_tick_loop_driver`; Kompositions-Seam = `_field_publish_provider`-Closure liest `app.state.field_publish` (getattr; fehlt → `None`). **Der public Setter/Adapter-Injektion folgt mit C3** ([`AC-NO-GOD-UTILS`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert): `app.py`-Public-Surface bleibt bei 5). Pins: `None`-Skip byte-identisch, Fan-out je Punkt, Lifecycle-Start/Stop im echten Run-Pfad, Start-Failure-Degrade, Publish-Exception-Survival | Implementation |
| **C3** ✓ | `adapters/driven/field_publish_mqtt/` — publish-only MQTT-Adapter (`MqttFieldPublishAdapter` impl. `FieldPublishPort`; paho-mqtt, `ClientFactory`-Injektion, `loop_start`; Topic `{prefix}/{device_id}/{metric}`; Payload via `canonical_json` (Domaenen-`TelemetryPoint`, `Decimal`-Fidelity, [`AC-NO-JSON`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)); `MqttFieldPublish*`-Fehler als `FieldPublishPort`-Vertragsfehler-Subklassen; Config-Validierung; Sim-/Nur-Sim-Netz-Doku [`GG-SAFE-007`](../../../../spec/lastenheft.md#gg-safe-007)). Unit: Lifecycle/idempotent, Publish-Mapping, Connect-/Publish-/Disconnect-Fehler, Config-Validierung | Implementation |
| **C4** ✓ | **Injektions-Wiring:** `GRID_GYM_FIELD_PUBLISH_MQTT_BROKER=host[:port]` → `_configure_field_publish_from_env` konstruiert `MqttFieldPublishAdapter` → `app.state.field_publish` (opt-in; unset → `None` → byte-identisch); Unit-Test env set/unset. **Integrationsgeschirr:** testcontainers-Smoke `MqttFieldPublishAdapter` → Mosquitto-Sibling → paho-Subscriber (`bess-ems`-Platzhalter) empfaengt die exponierte Telemetrie (`Decimal`-Fidelity ueber den ganzen Pfad). Adapter-Level-Smoke (Muster `test_mqtt_compose_smoke`), nicht Full-API-Container-E2E. **166 integration passed** | Implementation |

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

## Code-Review + Hardening (2026-07-12)

Zwei unabhaengige, adversariale Reviewer (Concurrency/Lifecycle + Vertrag/
Korrektheit/Coverage) gegen die C0–C4-Implementierung; 4 Hypothesen wurden
adversarial **widerlegt** (Cancel-Race, Doppel-Stop, Connect-Leak, Determinismus
— sauber). Adressierte Funde (Owner-Beschluss: alles fixen inkl. Multi-Run):

- **#1 (HIGH) Blocking-I/O auf dem Event-Loop:** `start()`/`stop()` (paho
  connect/disconnect) laufen jetzt via `asyncio.to_thread` — kein Event-Loop-
  Stall bei unerreichbarem Broker.
- **#2 (HIGH) env-Port-Parse:** typisierter `MqttFieldPublishConfigEndpointError`
  statt bare `ValueError` (kein Lifespan-Crash); `[ipv6]:port`-Support.
- **#3 (HIGH/MED) Multi-Run:** `build_run_driver` (`POST /runs/{id}/start`)
  verdrahtet Field-Publish jetzt mit **run-eindeutiger `client_id`** (kein
  Shared-Client-Session-Kick).
- **#4 (MED) F2-Ordering:** Field-Publish-Wiring VOR `repository.save`.
- **#5 (MED) Topic-Injection:** `device_id`/`metric` mit `/`,`+`,`#` oder leer →
  typisierter Reject (kein Fehlrouting / stiller Verlust).
- **#6 (MED) Lifecycle:** `_start_field_publish` IM `try/finally` (Provider-
  Exception ueberspringt `finalize()` nicht mehr).
- **#7 (MED) Log-Rate-Limit + Reconnect-Backoff:** Publish-Fehler pro Run
  gezaehlt (Summe am Ende) statt pro Punkt geloggt; `reconnect_delay_set`.
- **#8 (MED) Degrade-Status:** `DemoTickLoopDriver.field_publish_status`
  (`off`/`active`/`degraded`) macht einen stillen HIL-Feed-Ausfall beobachtbar.
- **#9/#10/#11:** Coverage (`stop()`-Disconnect-Fehler), staerkeres Integrations-
  Assert (2 Punkte, alle 10 Felder, QoS), `_encode_point`-Parity-Test gegen
  `protocol_mqtt.encode_telemetry`.
- **#13 (LOW):** stop-Reihenfolge `disconnect()` vor `loop_stop()` (graceful
  drain).

Offen (bewusst, niedrige Prio): #13 last-frame-Verlust bei QoS>0 (Default 0
fire-and-forget); #12 resolve-once-Asymmetrie (dokumentiert). Full-Endpoint-
Surfacing des Degrade-Status (`/healthcheck`-JSON) ist Folge-Kandidat.

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
- Folge-Slice: [`074`](../next/074-field-server-modbus-server-adapter.md) (Pull-Server,
  eigene Schwester-Port-Rolle).

## Entsperrt

[`074`](../next/074-field-server-modbus-server-adapter.md) (nutzt die Kompositions-
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
