# Next

Plan- und Slice-Notizen fuer **konkret geplante, aber noch nicht
aktive** Arbeit.

## Bestand

Field-Server-Surface ([`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md),
`Proposed`; **zwei Schwester-Ports** in der Kompositions-Schicht, nach zwei
adversarialen Reviews vom Kern-`TickLoop`-Kwarg-Entwurf revidiert). Anforderungs-
Verankerung entschieden: **HIL-Konkretisierung von**
[`GG-TEST-004`](../../../../spec/lastenheft.md#gg-test-004) (keine eigene
`GG-*`-ID; [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md)
§7). Aktivierungsbereit:

- [`073-field-server-mqtt-publish-bridge.md`](073-field-server-mqtt-publish-bridge.md)
  — `FieldPublishPort` (driven, Push): MQTT-Publish-Adapter + Kompositions-
  Schicht-Naht (Driver-Lifecycle + Fan-out) + grid-gym↔`bess-ems`-Integrations-
  geschirr. Zieht [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md)
  auf `Provisional`. Baut **keine** Current-Value-Projektion.
- [`074-field-server-modbus-server-adapter.md`](074-field-server-modbus-server-adapter.md)
  — `DeviceServerPort` (driving, Pull): Modbus-Server Read-Serving + die geteilte
  Current-Value-Projektion. Zieht
  [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) bei
  Closure auf `Accepted`. Haengt an `073`. **Read-serving only.**
- [`075-field-server-inbound-write-command.md`](075-field-server-inbound-write-command.md)
  — Inbound-Write→Command, **ausgegliedert** samt dedizierter Folge-ADR: ein
  Live-Master-Write ist exogener Input und bricht das geschlossene Self-Replay.
  Haengt an `074`.

*(`072` (dedizierter `stale_data`-Quality-Fault → [`GG-FAULT-002`](../../../../spec/lastenheft.md#gg-fault-002), Slice B) ist 2026-07-12 nach [`../done/072-gg-fault-002-stale-data.md`](../done/072-gg-fault-002-stale-data.md) abgeschlossen — die GG-FAULT-Konsolidierung (002/003/004) ist damit vollstaendig geliefert. `041`/`042` sind mit M8-Welle-0 2026-06-13 nach [`../in-progress/`](../in-progress/) aktiviert — [`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)-Rueckbau + Fault-Engine-Naming. `replay-source-integration.md` ist mit M7-Welle-1-C0 nach `../done-archive/M7-welle-1.md` aktiviert — [`GG-MVP-002`](../../../../spec/lastenheft.md#gg-mvp-002), sub-sliced 1a/1b, **Done 2026-06-09**. `abnahme-cli.md` ist mit M7-Welle-2-C0 nach `../done-archive/M7-welle-2.md` aktiviert — [`GG-MVP-003`](../../../../spec/lastenheft.md#gg-mvp-003). `051` (Durchsetzungsschicht) ist 2026-06-19 nach [`../in-progress/`](../in-progress/) aktiviert (Harness-Haertung).)*
