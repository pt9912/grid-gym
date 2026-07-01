# M8 — SOLLTE-Geraete & Netz — Closure-Ergebnisse

**Status:** Done (2026-07-01). **SOLLTE-Geraete & Netz sind
geliefert** — M8-Abschluss-Kriterium (Welle-5-D-4): alle vier
SOLLTE-Geraete ([`GG-DEV-015`](../../../../spec/lastenheft.md#gg-dev-015)..018),
das komplette SOLLTE-Netzmodell
([`GG-GRID-005`](../../../../spec/lastenheft.md#gg-grid-005)..007) und die zwei
BESS-Telemetrie-IDs ([`GG-BESS-006`](../../../../spec/lastenheft.md#gg-bess-006)/007)
produktiv; die parallel abgearbeiteten Post-MVP-Trigger
(039/040/046 + Slice 051) aufgeloest. **Release v0.2.0**
(Welle-5-D-5, Minor-Bump — additive Gerätemodelle) mit der
Closure geschnitten. M8-Abschluss-Gate `make gates` cache-frei
gruen; `make docs-check` gruen (Trigger-Move-Fan-out gefangen);
`make fullbuild` gruen vor Tag-Push (OTel-CVE-Defer aufgehoben,
Trigger 033 `Resolved 2026-06-18`). **Alle M8-ADRs
(0050/0051/0054/0055..0071) sind bereits `Accepted`** — je mit
ihrer Substanz-Welle produktiv belegt; die Closure-Welle traegt
keinen ADR-Status-Flip (Welle-5-D-2).
**Bezug:** Meilenstein-Vorbelegung
[`roadmap.md §4 M8`](../in-progress/roadmap.md); Welle-Slice-Docs
[`M8-welle-0.md`](M8-welle-0.md),
[`M8-welle-2.md`](M8-welle-2.md) (Gruppenplan),
[`M8-welle-2a.md`](M8-welle-2a.md),
[`M8-welle-2b.md`](M8-welle-2b.md),
[`M8-welle-2c.md`](M8-welle-2c.md),
[`M8-welle-2d.md`](M8-welle-2d.md),
[`M8-welle-2-d8.md`](M8-welle-2-d8.md),
[`M8-welle-3.md`](M8-welle-3.md) (Gruppenplan),
[`M8-welle-3a.md`](M8-welle-3a.md),
[`M8-welle-3b.md`](M8-welle-3b.md),
[`M8-welle-3c.md`](M8-welle-3c.md),
[`M8-welle-4.md`](M8-welle-4.md) (Gruppenplan),
[`M8-welle-4a.md`](M8-welle-4a.md),
[`M8-welle-4b.md`](M8-welle-4b.md),
[`M8-welle-5.md`](M8-welle-5.md) (Closure);
Roadmap [`../in-progress/roadmap.md`](../in-progress/roadmap.md)
§M8.

---

## 1. Welle-Tabelle

Hash-Stacks liegen kanonisch im jeweiligen Welle-Doc; diese
Tabelle ist der Quick-Glance mit Datum, Lieferung und ADR.

| Welle | Datum | Lieferung | ADR |
| ----- | ----- | --------- | --- |
| 0 | 2026-06-13 | Slice-Plan-Eroeffnung + Trigger-Triage; v0.1.1-Doku-Cut bewusst verworfen. NEU [`M8-welle-0.md`](M8-welle-0.md). | — |
| 1 | 2026-06-13 | Architektur-Cleanup: [`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)-`ignore_imports` → `[]` (Slice [`041`](../done/041-adapter-pure-ignore-imports-rueckbau.md)) + Fault-Engine-Rename (Slice [`042`](../done/042-fault-engine-location-and-naming.md)) + NEU `composition/`-Paket/ASGI-Entrypoint. | [`0050`](../../adr/0050-adapter-pure-bridge-retirement.md)/[`0051`](../../adr/0051-fault-engine-location-and-naming.md)/[`0054`](../../adr/0054-composition-asgi-entrypoint-and-scenario-hook.md) |
| 2a | 2026-06-14 | EV-Charger ([`GG-DEV-015`](../../../../spec/lastenheft.md#gg-dev-015)): SoC + CC/CV-Kennlinie + V2G + `connection_loss`. Trigger 016 aufgeloest; `D-7` adoptiert. | [`0055`](../../adr/0055-ev-charger-device-pattern.md) |
| 2b | 2026-06-14 | Transformer ([`GG-DEV-016`](../../../../spec/lastenheft.md#gg-dev-016)): Wandlungsverhaeltnis + Eisen-/Kupferverluste + Saettigung + `winding_fault`. Trigger 017 aufgeloest. Codec-Dedup-Slice [`045`](../done/045-fault-state-flag-codec-dedup.md). | [`0056`](../../adr/0056-transformer-device-pattern.md) |
| 2c | 2026-06-14 | Wind-Turbine ([`GG-DEV-017`](../../../../spec/lastenheft.md#gg-dev-017)): kubische cut-in/rated/cut-out-Kennlinie, stochastischer seeded `RandomPort`-Windeingang (erster echter `RandomPort`-Konsument). Trigger 018 aufgeloest. | [`0057`](../../adr/0057-wind-turbine-device-pattern.md) |
| 2d | 2026-06-14 | Diesel-Generator ([`GG-DEV-018`](../../../../spec/lastenheft.md#gg-dev-018)): Kraftstoff + Verbrauch + Ramp + Anfahr-/Abstell-Hysterese + `genset_fault`. Trigger 019 aufgeloest. **Welle 2 (alle vier SOLLTE-Geraete) komplett.** | [`0058`](../../adr/0058-diesel-generator-device-pattern.md) |
| 2-D8 | 2026-06-15 | Cross-Cutting-Review-Folge: generische `ScenarioFaultEngine` (eine Engine ueber `supported_types`) generalisiert Battery/Grid; `connection_loss`/`winding_fault`/`genset_fault` end-to-end ueber YAML. Carveout D-8 aufgeloest. | [`0059`](../../adr/0059-generic-scenario-fault-engine.md) |
| 3a | 2026-06-16 | Inselnetz-Bilanz ([`GG-GRID-005`](../../../../spec/lastenheft.md#gg-grid-005)): `is_islanded`/`forming_device_id`, Forming-Geraet als Slack. Trigger 020 aufgeloest. | [`0060`](../../adr/0060-island-grid-bilanz-pattern.md) |
| 3b | 2026-06-16 | Trafo-Grenzen ([`GG-GRID-006`](../../../../spec/lastenheft.md#gg-grid-006)): `transformer_limit`-Thermomodell → pro-Tick `GridConstraintViolationEvent`, opt-in, inaktiv bit-genau. Trigger 021 aufgeloest. | [`0061`](../../adr/0061-transformer-limit-bilanz-pattern.md) |
| 3c | 2026-06-16 | Blindleistung ([`GG-GRID-007`](../../../../spec/lastenheft.md#gg-grid-007), re-tranchiert): Q-Bilanz `imbalance_kvar` + Q-Spannungskopplung (Snapshot v2→v3, 3c-a); PV-Q(U) + Spannungs-Feedback (3c-b-1); GridConnection-Q-Residual + Transformer-S=√(P²+Q²) (3c-b-2). Trigger 022 aufgeloest. **Welle 3 (Netz) komplett.** | [`0062`](../../adr/0062-reactive-power-bilanz-pattern.md)/[`0063`](../../adr/0063-pv-volt-var-q-emission-pattern.md)/[`0064`](../../adr/0064-grid-connection-q-transformer-apparent-power.md) |
| 4a | 2026-06-17 | BESS-Temperatur ([`GG-BESS-006`](../../../../spec/lastenheft.md#gg-bess-006)): `temperature_celsius` aus Lastfaktor + Umgebung + Zeitkonstante; opt-in, pin-neutral. Trigger 023 aufgeloest. | [`0065`](../../adr/0065-battery-thermal-telemetry-pattern.md) |
| 4b | 2026-06-17 | BESS-Zellspannung ([`GG-BESS-007`](../../../../spec/lastenheft.md#gg-bess-007)): `cell_voltages_v`-Tuple + opt-in per-Zelle-Rauschen via `RandomPort.sub_port`; `cell_voltage_delta_v`-Telemetrie. Trigger 024 aufgeloest. **Welle 4 (BESS-Telemetrie) komplett.** | [`0066`](../../adr/0066-battery-cell-voltage-telemetry-pattern.md) |
| 5 | 2026-07-01 | **Closure** ([`M8-welle-5.md`](M8-welle-5.md)): Trigger-Archival `open/016..024` → `done-archive/`; `M8-results.md` (dieses Dokument); `roadmap.md` M8 → `Done` + Post-M8-Trigger-Watch; Release v0.2.0. Kein ADR-Flip (alle bereits `Accepted`, Welle-5-D-2). | — |

**Parallele Post-MVP-Wellen** (Trigger-Watch, keine
SOLLTE-Feature-Welle; im M8-Zeitraum geliefert):

| Welle | Datum | Lieferung | ADR |
| ----- | ----- | --------- | --- |
| Replay-Paar 039+040 | 2026-06-18 | Core-Run-End-Naht + Partial-Run ([`040`](../done/040-replay-finalize-headless-run-end-seam.md)) + API-Replay-Binding-Persistenz ([`039`](../done/039-api-replay-trigger-surface.md) Phase A) + Phase-B-Konsumnaht. | [`0067`](../../adr/0067-run-end-seam-and-partial-run.md)/[`0068`](../../adr/0068-api-replay-binding-persistence.md) |
| Multi-Run-Execution | 2026-06-18 | Scenario-Store (`POST /scenarios`) + per-Run-`RunDriverRegistry` + `POST /runs/{id}/start` + Replay-Konsumnaht (S1..S4). | [`0069`](../../adr/0069-multi-run-execution-and-scenario-store.md) |
| Scenario-Commands (Trigger 046) | 2026-06-18 | Top-Level-`commands`-Block + `ScenarioCommandEngine` + TickLoop-A0s; vier SOLLTE-Geraete fuehren nicht-idle Command-E2E. | [`0070`](../../adr/0070-scenario-scheduled-device-commands.md) |
| Harness-Durchsetzungsschicht (Slice 051) | 2026-06-19 | Tool-Call-Gate + Handoff-Gate + Workflow-Skelett via `.claude/hooks` (Docker-only + Gates-vor-Handoff mechanisch gebunden). Kein Runtime-Delta. | [`0071`](../../adr/0071-enforcement-layer-hooks.md) |

---

## 2. Abnahme-Belege

| Lastenheft-Kategorie | Stand nach M8 |
| -------------------- | ------------- |
| [`GG-DEV-015`](../../../../spec/lastenheft.md#gg-dev-015) | ✓ produktiv (Welle 2a): EV-Charger als `DeviceModel` + `FaultInjectableDevice` ([`ADR 0055`](../../adr/0055-ev-charger-device-pattern.md)). |
| [`GG-DEV-016`](../../../../spec/lastenheft.md#gg-dev-016) | ✓ produktiv (Welle 2b): Transformer-Geraet ([`ADR 0056`](../../adr/0056-transformer-device-pattern.md)). |
| [`GG-DEV-017`](../../../../spec/lastenheft.md#gg-dev-017) | ✓ produktiv (Welle 2c): Wind-Turbine, erster stochastischer `RandomPort`-Konsument ([`ADR 0057`](../../adr/0057-wind-turbine-device-pattern.md)). |
| [`GG-DEV-018`](../../../../spec/lastenheft.md#gg-dev-018) | ✓ produktiv (Welle 2d): Diesel-Generator mit Hysterese + Kraftstoff ([`ADR 0058`](../../adr/0058-diesel-generator-device-pattern.md)). **Alle vier SOLLTE-Geraete produktiv.** |
| [`GG-GRID-005`](../../../../spec/lastenheft.md#gg-grid-005) | ✓ produktiv (Welle 3a): Inselnetz-Bilanzmodell ([`ADR 0060`](../../adr/0060-island-grid-bilanz-pattern.md)). |
| [`GG-GRID-006`](../../../../spec/lastenheft.md#gg-grid-006) | ✓ produktiv (Welle 3b): Transformatorgrenzen im Netzbilanzmodell ([`ADR 0061`](../../adr/0061-transformer-limit-bilanz-pattern.md)). |
| [`GG-GRID-007`](../../../../spec/lastenheft.md#gg-grid-007) | ✓ produktiv (Welle 3c): Blindleistung im Netzbilanzmodell ([`ADR 0062`](../../adr/0062-reactive-power-bilanz-pattern.md)/[`ADR 0063`](../../adr/0063-pv-volt-var-q-emission-pattern.md)/[`ADR 0064`](../../adr/0064-grid-connection-q-transformer-apparent-power.md); Snapshot v2→v3). **SOLLTE-Netzmodell komplett.** |
| [`GG-BESS-006`](../../../../spec/lastenheft.md#gg-bess-006) | ✓ produktiv (Welle 4a): Battery-Temperatur-Telemetrie ([`ADR 0065`](../../adr/0065-battery-thermal-telemetry-pattern.md)). |
| [`GG-BESS-007`](../../../../spec/lastenheft.md#gg-bess-007) | ✓ produktiv (Welle 4b): Battery-Zellspannung-Telemetrie ([`ADR 0066`](../../adr/0066-battery-cell-voltage-telemetry-pattern.md)). |

**MVP-Bestand unberuehrt:** die vier [`GG-MVP-001`](../../../../spec/lastenheft.md#gg-mvp-001)..004
und die vier [`GG-SAFE-001`](../../../../spec/lastenheft.md#gg-safe-001)..004 bleiben produktiv
(M1..M7-Bestand); M8 ist rein additiv — Bestands-Szenarien ohne
neue Geraete/Netz-/Telemetrie-Felder sind bit-genau unveraendert
([`GG-SIM-001`](../../../../spec/lastenheft.md#gg-sim-001)/004,
[`GG-MVP-002`](../../../../spec/lastenheft.md#gg-mvp-002)).

---

## 3. Pro-Welle-Reviews

Jede Substanz-Welle wurde mit frischem Reviewer-Kontext geprueft;
Findings sind im jeweiligen Welle-Doc §Review verankert. Leitende
Befunde:

- **Welle 2a/2b** — Review-Deferral zu Fault-Flag-Codec-Dedup →
  eigener Slice [`045`](../done/045-fault-state-flag-codec-dedup.md)
  (`assert_optional_fault_flag`, vier Device-Snapshots migriert).
- **Welle 2c/2d** — `RandomPort`-Resume-Mechanik real aktiviert
  (2c); `_BILANZ_SOURCE_BUCKETS`-`generation`-Lerneintrag proaktiv
  in 2d uebernommen (+ NEU `snapshot_codec.assert_bool`).
- **Welle 2-D8** — Cross-Cutting-Generalisierung der Fault-Engine
  ([`ADR 0059`](../../adr/0059-generic-scenario-fault-engine.md)); `make gates`/`docs-check`/`test-integration` gruen.
- **Welle 3a/3b/3c** — Q-frei bit-genaue Pin-Neutralitaet als
  durchgaengiger Regressionspin (3b-Boundary via
  Transformer-S=√(P²+Q²) in 3c-b-2 re-gepinnt).
- **Welle 4a/4b** — opt-in + pin-neutral; keine Bilanz-Beruehrung,
  additive Snapshot-Erweiterung.
- **Multi-Run-Welle** — Welle-Review S1–S4: `POST /runs/{id}/start`
  faengt `GridGymError` → 422 statt 500; Execution-Seed aus
  `RunMetadata.seed`; Registry-Cap zaehlt aktive Driver; terminale
  Laeufe → 409.

---

## 4. Welle-5-Verifikations-Sweep

- **S-1 M8-Trigger-Sweep:** aufgeloest — 016..019 (Welle 2),
  020..022 (Welle 3), 023/024 (Welle 4), 046 (Scenario-Commands),
  039/040 (Replay-Paar), 051 (Harness). Welle 5 vollzieht die
  **physische Archivierung** von 016..024 nach `done-archive/`
  (Welle-5-D-3). Offen bleiben Post-M8: 037 (Multi-Node), 038
  (volle [`GG-TERM-002`](../../../../spec/lastenheft.md#gg-term-002)/003-Matrix), 047
  (SNMP/LwM2M), 004/005/007/011/026/030 (Trigger-Gated-Bestand,
  [`carveouts.md`](../in-progress/carveouts.md)).
- **S-2 Sub-Slicing-Schwelle:** Welle 2 → 2a/2b/2c/2d + D8; Welle
  3 → 3a/3b/3c, 3c → 3c-a/3c-b-1/3c-b-2 (Q-Kopplung stufenweise);
  Welle 4 → 4a/4b — je per Welle-N-D-Beschluss dokumentiert.
- **S-3 Default-Gates:** `make gates` cache-frei gruen ohne
  Override am Closure-Hash (Doku-only-Welle, Test-Counts
  unveraendert); `make docs-check` gruen (Trigger-Move-Fan-out +
  ADR-Index).
- **S-4 Release-Pfad:** `make fullbuild` gruen (OTel-CVE-Defer
  aufgehoben, Trigger 033 `Resolved`); Tag `v0.2.0` → erster
  Minor-Release ueber [`release.yml`](../../../../.github/workflows/release.yml)
  ([`ADR 0042`](../../adr/0042-sbom-tool-and-release-pattern.md)): GHCR-Image + 5 Assets + SBOM.
- **S-5 ADR-Erweiterungs-Pattern:** M8 = **20 ADRs `Accepted`**
  (0050/0051 aus M7 in Welle 1 aufgeloest; 0054..0071 neu). Der
  hohe Zaehlwert reflektiert die **eingefaltete Post-MVP-Arbeit**
  (0067..0071 aus parallelen Trigger-Wellen), nicht nur die
  SOLLTE-Feature-Wellen. Die reinen SOLLTE-ADRs (0055..0066 =
  12) liegen im erwartbaren Feature-Meilenstein-Rahmen.
- **S-6 Lastenheft-Coverage-Sweep:** SOLLTE-Geraete/Netz/BESS
  komplett ([`GG-DEV-015`](../../../../spec/lastenheft.md#gg-dev-015)..018,
  [`GG-GRID-005`](../../../../spec/lastenheft.md#gg-grid-005)..007,
  [`GG-BESS-006`](../../../../spec/lastenheft.md#gg-bess-006)/007 ✓); verbleibende
  Kategorien ([`GG-DEPLOY-007`](../../../../spec/lastenheft.md#gg-deploy-007)..010,
  GG-TERM-Vollmatrix, SNMP/LwM2M, `GG-FUTURE-*`) sind ueber
  Trigger + [`carveouts.md`](../in-progress/carveouts.md) verankert.

---

## 5. Welle-5-Erbschaft (Post-M8)

- **Offene `open/`-Trigger:** 037
  ([`GG-DEPLOY-007`](../../../../spec/lastenheft.md#gg-deploy-007)..010 Multi-Node/K8s),
  038 (volle [`GG-TERM-002`](../../../../spec/lastenheft.md#gg-term-002)/003-Equality-Matrix),
  047 (SNMP/LwM2M-Device-Management-Adapter,
  [`GG-SNMP-001`](../../../../spec/lastenheft.md#gg-snmp-001)/[`GG-LWM2M-001`](../../../../spec/lastenheft.md#gg-lwm2m-001)),
  048/050 (d-check-matrix-Folge, Resolved-Doc-Archiv), 052
  (Carveout-Modul-07-Audit-Trichter, aktivierungs-gated auf
  `carveouts.md ≥ 50` bzw. faellige Welle-Closure).
- **Tooling-Querschnitt-Trigger:** 004 (Canonical-Encoder-
  Alternative), 005 (mypy vs. pyright), 007 (pyright-Pre-Commit),
  011 (`MLRandomPort`-Sub-Seed-Breite) — laufen unabhaengig, kein
  M8-Lieferpunkt.
- **Forschungs-Spikes:** 026 (BESS-Reserve-Market), 030
  (RL-Adapter) — Stakeholder-getrieben.
- **Trigger-Gated-Bestand-Index:**
  [`../in-progress/carveouts.md`](../in-progress/carveouts.md).

---

## 6. M8-Wandert-Nach + Post-M8-Modus

- `M8-results.md` (dieses Doc) + `M8-welle-5.md` liegen in
  `done/` (wie die uebrigen M8-Welle-Docs). Die neun aufgeloesten
  SOLLTE-Trigger [`016`](../done-archive/016-sollte-ev-charger-device.md)..[`024`](../done-archive/024-sollte-battery-cell-voltage.md)
  liegen nach C1 in `done-archive/`.
- **Post-M8-Modus: Trigger-Watch, kein Auto-Open.** Die
  SOLLTE-Geraete-/Netz-Cluster sind geliefert; es gibt kein
  offenes MUSS-Mandat. Die offenen Trigger (§5) tragen
  dokumentierte Aktivierungs-Bedingungen; ein neuer Meilenstein
  (M9+) entsteht erst bei Trigger-Aktivierung oder
  Stakeholder-Mandat (Pattern analog M7-Welle-X-D-4 +
  M6-welle-7-Review-Befund 3).

---

## 7. M8-ADR-Decision-Sweep

Alle M8-ADRs sind `Accepted` — je mit ihrer Substanz-Welle
produktiv belegt (Welle-5-D-2). Die Closure-Welle traegt keinen
Status-Flip.

| ADR | Titel | Welle | Status |
| --- | ----- | ----- | ------ |
| [`0050`](../../adr/0050-adapter-pure-bridge-retirement.md) | [`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) Bridge-Rueckbau | 1 (Slice 041) | Accepted (M7-WX-D-2-Deferral aufgeloest) |
| [`0051`](../../adr/0051-fault-engine-location-and-naming.md) | Fault-Engine-Standort + Naming | 1 (Slice 042) | Accepted (M7-WX-D-2-Deferral aufgeloest) |
| [`0054`](../../adr/0054-composition-asgi-entrypoint-and-scenario-hook.md) | `composition`-Paket + ASGI-Entrypoint + Scenario-Hook | 1 | Accepted |
| [`0055`](../../adr/0055-ev-charger-device-pattern.md) | EV-Charger-Device-Pattern | 2a | Accepted |
| [`0056`](../../adr/0056-transformer-device-pattern.md) | Transformer-Device-Pattern | 2b | Accepted |
| [`0057`](../../adr/0057-wind-turbine-device-pattern.md) | Wind-Turbine-Device-Pattern | 2c | Accepted |
| [`0058`](../../adr/0058-diesel-generator-device-pattern.md) | Diesel-Generator-Device-Pattern | 2d | Accepted |
| [`0059`](../../adr/0059-generic-scenario-fault-engine.md) | Generische `ScenarioFaultEngine` | 2-D8 | Accepted |
| [`0060`](../../adr/0060-island-grid-bilanz-pattern.md) | Inselnetz-Bilanz-Pattern | 3a | Accepted |
| [`0061`](../../adr/0061-transformer-limit-bilanz-pattern.md) | Transformer-Limit-Bilanz-Pattern | 3b | Accepted |
| [`0062`](../../adr/0062-reactive-power-bilanz-pattern.md) | Reactive-Power-Bilanz-Pattern | 3c-a | Accepted |
| [`0063`](../../adr/0063-pv-volt-var-q-emission-pattern.md) | PV-Volt-Var-Q-Emission-Pattern | 3c-b-1 | Accepted |
| [`0064`](../../adr/0064-grid-connection-q-transformer-apparent-power.md) | GridConnection-Q + Transformer-Scheinleistung | 3c-b-2 | Accepted |
| [`0065`](../../adr/0065-battery-thermal-telemetry-pattern.md) | Battery-Thermal-Telemetry-Pattern | 4a | Accepted |
| [`0066`](../../adr/0066-battery-cell-voltage-telemetry-pattern.md) | Battery-Cell-Voltage-Telemetry-Pattern | 4b | Accepted |
| [`0067`](../../adr/0067-run-end-seam-and-partial-run.md) | Run-End-Naht + Partial-Run | Slice 040 | Accepted |
| [`0068`](../../adr/0068-api-replay-binding-persistence.md) | API-Replay-Binding-Persistenz | Slice 039 (Phase A) | Accepted |
| [`0069`](../../adr/0069-multi-run-execution-and-scenario-store.md) | Multi-Run-Execution + Scenario-Store | Multi-Run-Welle | Accepted |
| [`0070`](../../adr/0070-scenario-scheduled-device-commands.md) | Scenario-Scheduled Device Commands | Trigger 046 | Accepted |
| [`0071`](../../adr/0071-enforcement-layer-hooks.md) | Durchsetzungsschicht (Enforcement-Layer-Hooks) | Slice 051 | Accepted |

Mehrere Accepted-ADRs sind
[`ADR-0011`](../../adr/0011-schaerfung-ohne-abloesung.md)-Schaerfungen
bestehender Vertraege (0060..0064 → [`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md);
0065/0066 → [`ADR 0014`](../../adr/0014-battery-snapshot-schema.md)) — kein
Supersedes; die geschaerften ADRs bleiben textlich unveraendert.

---

## 8. Nicht-vollzogene Items (bewusst)

- **Verteiltes Deployment ([`GG-DEPLOY-007`](../../../../spec/lastenheft.md#gg-deploy-007)..010)** —
  Post-M8, Trigger 037 (M10-Vorbelegung, Anti-Scope M8).
- **Volle [`GG-TERM-002`](../../../../spec/lastenheft.md#gg-term-002)/003-Equality-Matrix** —
  MVP-Preflight deckt 5 `RunMetadata`-Felder; Vollausbau ueber
  Trigger 038 (M9-Vorbelegung).
- **SNMP/LwM2M-Device-Management-Adapter** — Trigger 047, ohne
  Profil-ADR/Adapter-Code; Stakeholder-getrieben.
- **Oeffentliche API-Replay-Bedienung (`POST /runs` `replay_of`)**
  — Multi-Run-Execution liefert die interne Naht; die volle
  oeffentliche Bedienungs-Semantik bleibt M9-Material (Anti-Scope
  M8, [`roadmap.md §4 M8`](../in-progress/roadmap.md)).
- **Carveout-Modul-07-Audit-Trichter** — Trigger 052,
  aktivierungs-gated (`carveouts.md ≥ 50` bzw. faellige
  Welle-Closure), aktuell nicht faellig.

---

## References

- [`M8-welle-5.md`](M8-welle-5.md) — Closure-Welle
  (Decisions 5-D-1..D-5).
- [`M8-welle-0.md`](M8-welle-0.md) — M8-Eroeffnungs-Decisions.
- [`M7-results.md`](M7-results.md) + [`M6-results.md`](M6-results.md)
  — Results-Doc-Vorbilder.
- [`carveouts.md`](../in-progress/carveouts.md) — Cross-Meilenstein-
  Carveout-Index.
- ADR-Index [`../../adr/README.md`](../../adr/README.md).
