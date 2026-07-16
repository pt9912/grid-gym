# Next

Plan- und Slice-Notizen fuer **konkret geplante, aber noch nicht
aktive** Arbeit.

## Bestand

**Aktiver `next/`-Eintrag: [`083`](083-spezifikation-layer-discipline-core-move.md)**
— erster Slice des Migrations-Arcs zur Spec-Schichtung
([`ADR 0080`](../../adr/0080-three-layer-spec-model.md)): Spezifikations-Schicht
anlegen + Disziplin-Kern (`GG-PRINC-*`/`GG-CC-*`/`GG-SEED-*`) umziehen, Vertrag
atomar/zuletzt. Aktivierungsbereit. Danach in `open/`:
[`084`](../open/084-architecture-bezug-drift-fix.md) (Bezug-Drift-Fix),
[`085`](../open/085-spezifikation-layer-qs-families-move.md) (QS-Familien),
[`086`](../open/086-traceability-derived-27-1-finalization.md)
(Traceability-Finalisierung). Der gesamte Arc ist doku-/config-only → kein Release.

Slice [`077`](../done/077-bess-ems-conformant-field-publisher.md)
(bess-ems-konformer Feld-Publisher) ist **abgeschlossen + released als v0.7.0** (ADRs
[`0077`](../../adr/0077-battery-field-envelope-completeness.md)/[`0078`](../../adr/0078-bess-ems-field-contract-publisher.md)
`Accepted`, realer bess-ems-MQTT-only-E2E) und liegt in [`../done/`](../done/README.md).

Die Field-Server-Surface
([`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md),
`Accepted`; **zwei Schwester-Ports** in der Kompositions-Schicht) ist mit
Push-Seite [`073`](../done/073-field-server-mqtt-publish-bridge.md) +
Pull-Seite [`074`](../done/074-field-server-modbus-server-adapter.md) +
Inbound-Write [`075`](../done/075-field-server-inbound-write-command.md)
([`ADR 0076`](../../adr/0076-inbound-write-exogenous-input-recording.md) `Accepted`)
**komplett geliefert + review-gehaertet → v0.5.0/v0.6.x (2026-07-13)**. Slice 077 ist
die **naechste** HIL-Konkretisierung von
[`GG-TEST-004`](../../../../spec/lastenheft.md#gg-test-004) (keine eigene `GG-*`-ID).

*(`072` (dedizierter `stale_data`-Quality-Fault → [`GG-FAULT-002`](../../../../spec/lastenheft.md#gg-fault-002), Slice B) ist 2026-07-12 nach [`../done/072-gg-fault-002-stale-data.md`](../done/072-gg-fault-002-stale-data.md) abgeschlossen — die GG-FAULT-Konsolidierung (002/003/004) ist damit vollstaendig geliefert. `041`/`042` sind mit M8-Welle-0 2026-06-13 nach [`../in-progress/`](../in-progress/) aktiviert — [`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)-Rueckbau + Fault-Engine-Naming. `replay-source-integration.md` ist mit M7-Welle-1-C0 nach `../done-archive/M7-welle-1.md` aktiviert — [`GG-MVP-002`](../../../../spec/lastenheft.md#gg-mvp-002), sub-sliced 1a/1b, **Done 2026-06-09**. `abnahme-cli.md` ist mit M7-Welle-2-C0 nach `../done-archive/M7-welle-2.md` aktiviert — [`GG-MVP-003`](../../../../spec/lastenheft.md#gg-mvp-003). `051` (Durchsetzungsschicht) ist 2026-06-19 nach [`../in-progress/`](../in-progress/) aktiviert (Harness-Haertung).)*
