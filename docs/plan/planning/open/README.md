# Offene Plaene und Trigger-Watch

Dieses Verzeichnis sammelt **trigger-getriebene Folgearbeit** und
**Vorabklaerungen**, die noch nicht in die aktive Roadmap aufgenommen
wurden.

Eintraege wandern entweder:

- nach `next/`, sobald ein Scope skizziert ist, aber noch kein Slice aktiv,
- nach `in-progress/`, wenn sie direkt aktiviert werden, oder
- nach `archive/`, wenn sie bewusst verworfen werden.

Aufgeloeste Trigger werden mit der aufloesenden Slice-Closure
nach [`../done/`](../done/) verschoben (rename-only) und sind
dort in der `done/`-Bestand-Tabelle gelistet — nicht hier.

---

## Bestand

Alle Eintraege sind Trigger-Watch-Notizen (`Status: Open`) ohne
harten Aktivierungs-Zwang. Die `Aktivierung`-Spalte beschreibt den
konkreten Anlass, der eine Aktivierung ausloesen soll.

**Tooling / Build / Type-System:**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`004-canonical-encoder-alternative-adr.md`](004-canonical-encoder-alternative-adr.md) | ADR fuer Performance-/Implementierungs-Alternativen (orjson, msgspec) | bei messbarem Perf-Druck am Telemetrie-Pfad |
| [`005-pyright-vs-mypy-reeval.md`](005-pyright-vs-mypy-reeval.md) | Re-Eval mypy vs. pyright bei generischen Protocols | sobald `ports/*` Generic-Protocols einfuehrt |
| [`007-pyright-precommit-adr.md`](007-pyright-precommit-adr.md) | ADR fuer pyright als Pre-Commit-Hook | bei Editor-Parity-Druck |
| [`048-dcheck-matrix-modul.md`](048-dcheck-matrix-modul.md) | d-check-`matrix`-Modul (Referenzrichtungs-Gate, SDP) — **Resolved 2026-06-17**: Option A (Voll-SDP) via Slice [`049`](../done/049-sdp-matrix-doku-umbau.md); `matrix` aktiv, Spec-Straten zeitlos, `make docs-check` gruen | **Resolved** (Doc-Archiv mit M8-Closure) |
| [`050-dcheck-matrix-supersede-lineage.md`](050-dcheck-matrix-supersede-lineage.md) | d-check-`matrix`-Supersede-Lineage-Carve-out (CR, Folge aus Slice 049) — **Resolved 2026-06-17**: d-check v0.11.0 liefert `allow-supersede-lineage`; Pin + `.d-check.yml`-Config + [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md)-Lineage-Link migriert, `make docs-check` gruen (Boundary verifiziert) | **Resolved** (Doc-Archiv mit M8-Closure) |
**Harness-Regelwerk-Adoption (v1.2.0-Delta):**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`051-durchsetzungsschicht-enforcement-layer.md`](051-durchsetzungsschicht-enforcement-layer.md) | Durchsetzungsschicht (Tool-Call-Gate + Handoff-Gate + Workflow-Skelett) — v1.2.0-Mechanik, im Repo abwesend (nur `.claude/settings.local.json`-Allowlist, keine Hooks); harte Regeln nur inferential feedforward in `AGENTS.md` | Steering-Loop ≥ 3× Handoff-/Docker-only-Drift ODER bewusste Harness-Haertung vor M8-Closure |
| [`052-carveout-modul07-audit-trichter.md`](052-carveout-modul07-audit-trichter.md) | Carveout-Disziplin Modul 07: Audit-Slice pro Welle-Closure + Werkzeug-Wahl-Trichter (Granularitaet vor Temporalitaet) — v1.2.0-Schaerfung ueber `MR-003` hinaus | Naechste Welle-/M8-Closure mit faelligem Carveout-Audit ODER `carveouts.md` ≥ 50 Eintraege (`MR-003` §4) |

**M3-/Multi-Agent-Folge:**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`011-mlrandomport-subseed-width.md`](011-mlrandomport-subseed-width.md) | `MLRandomPort` Sub-Seed-Wortbreite ([`ADR 0007`](../../adr/0007-random-port.md) §5.2/§6) | bei `> 10⁶` Sub-Ports / hochskalierter Multi-Agent-Welle |
| [`026-bess-simulation-reserve-market-spike.md`](026-bess-simulation-reserve-market-spike.md) | Lokale BESS-Simulation als Vorlage fuer Reserve-Market-/LER-Strategien | bei Reserve-Market-Agent, BESS-SOC-Management-Agent oder LER-Demo |
| [`030-rl-adapter.md`](030-rl-adapter.md) | RL-Adapter ueber den Multi-Agent-Bus ([`GG-FUTURE-001`](../../../../spec/lastenheft.md#gg-future-001)/002) | bei konkreter RL-Stakeholder-Anforderung (M7+-Material) |

**Quality-/Determinismus-Lücken (M6-Welle-5a/5c-Audit-Folge):**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`038-gg-term-002-003-full-equality-matrix.md`](038-gg-term-002-003-full-equality-matrix.md) | Volle [`GG-TERM-002`](../../../../spec/lastenheft.md#gg-term-002)/003-Equality-Matrix — `platform_arch`, `enabled_adapters`, `sim_start_time`, separater `config_hash` (Lastenheft [`GG-TERM-002`](../../../../spec/lastenheft.md#gg-term-002)/003); M7-Welle-1b liefert per 1b-a-D-6 nur den MVP-Preflight ueber die 5 vorhandenen `RunMetadata`-Felder | Compliance-/Audit-Bedarf fuer vollstaendige Reproduzierbarkeits-Metadaten ODER Multi-Plattform-/Multi-Adapter-Replay |

**Multi-Node-Deployment-Familie (M6-Welle-6-Audit-Folge):**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`037-deploy-007-010-multi-node-deployment.md`](037-deploy-007-010-multi-node-deployment.md) | [`GG-DEPLOY-007`](../../../../spec/lastenheft.md#gg-deploy-007)..010 Kubernetes-Manifeste + Rolling-Updates + Zero-Downtime + Rollback — komplett Lücke; Architektur §16 Z. 916 fordert „Trigger-getriebene Folgearbeit" (diese Notiz erfuellt die Verankerungs-Pflicht) | Stakeholder-Bedarf fuer Multi-Node-/K8s-Deployment ODER Skalierungs-/Compliance-Druck |

**Protokolladapter-Erweiterungen:**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`047-device-management-protocol-adapters.md`](047-device-management-protocol-adapters.md) | SNMP/LwM2M als Device-Management- und Telemetry-Simulationsadapter ([`GG-SNMP-001`](../../../../spec/lastenheft.md#gg-snmp-001), [`GG-LWM2M-001`](../../../../spec/lastenheft.md#gg-lwm2m-001)) — noch ohne Profil-ADR, Adapter-Code oder Smoke-Test | Stakeholder-Bedarf fuer SNMP-/LwM2M-Demo ODER Integrationspartner-Mapping ODER Validation-Befund zu Device-Management-Protokollen |

**SOLLTE — M2-Welle-7-Erbschaft** (Quelle: [`../done/M2-devices.md`](../done-archive/M2-devices.md) §4 Out-of-Scope):

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`016-sollte-ev-charger-device.md`](016-sollte-ev-charger-device.md) | EV-Charger-Device ([`GG-DEV-015`](../../../../spec/lastenheft.md#gg-dev-015), Lastenheft §9.4) | wenn konkreter Bedarf — eigener Slice |
| [`017-sollte-transformer-device.md`](017-sollte-transformer-device.md) | Transformer-Device ([`GG-DEV-016`](../../../../spec/lastenheft.md#gg-dev-016), Lastenheft §9.4) | wenn konkreter Bedarf — eigener Slice |
| [`018-sollte-wind-device.md`](018-sollte-wind-device.md) | Wind-Device ([`GG-DEV-017`](../../../../spec/lastenheft.md#gg-dev-017), Lastenheft §9.4) | wenn konkreter Bedarf — eigener Slice |
| [`019-sollte-diesel-device.md`](019-sollte-diesel-device.md) | Diesel-Device ([`GG-DEV-018`](../../../../spec/lastenheft.md#gg-dev-018), Lastenheft §9.4) | wenn konkreter Bedarf — eigener Slice |
| [`020-sollte-island-grid.md`](020-sollte-island-grid.md) | Inselnetz-Bilanzmodell ([`GG-GRID-005`](../../../../spec/lastenheft.md#gg-grid-005), Lastenheft §11.5) | wenn konkreter Bedarf — eigener Slice |
| [`021-sollte-transformer-limits.md`](021-sollte-transformer-limits.md) | Transformatorgrenzen im Netzbilanzmodell ([`GG-GRID-006`](../../../../spec/lastenheft.md#gg-grid-006), Lastenheft §11.5) | wenn konkreter Bedarf — eigener Slice |
| [`022-sollte-reactive-power.md`](022-sollte-reactive-power.md) | Blindleistung im Netzbilanzmodell ([`GG-GRID-007`](../../../../spec/lastenheft.md#gg-grid-007), Lastenheft §11.5) | wenn konkreter Bedarf — eigener Slice |
| [`023-sollte-battery-temperature.md`](023-sollte-battery-temperature.md) | Battery-Temperatur-Telemetry ([`GG-BESS-006`](../../../../spec/lastenheft.md#gg-bess-006), Lastenheft §10.6) | wenn konkreter Bedarf — eigener Slice |
| [`024-sollte-battery-cell-voltage.md`](024-sollte-battery-cell-voltage.md) | Battery-Zellspannung-Telemetry ([`GG-BESS-007`](../../../../spec/lastenheft.md#gg-bess-007), Lastenheft §10.6) | wenn konkreter Bedarf — eigener Slice |

**SOLLTE-Geraete — M8-Welle-2-Test-Erbschaft:**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`046-command-driven-integration-e2e.md`](046-command-driven-integration-e2e.md) | Command-getriebener Integration-E2E fuer die SOLLTE-Geraete ([`GG-DEV-015`](../../../../spec/lastenheft.md#gg-dev-015)..018) — die vier Szenario-Smokes fahren idle, das generische Command-Routing ist via `test_agents_demo_e2e.py` + Battery gedeckt; kein scenario-scheduled-Command-Mechanismus im `devices`-Block (M8-Welle-2a..2d Anti-Scope) | scenario-scheduled-Command-Mechanismus im `devices`-Block ODER Bedarf an geraetespezifischer Command-Routing-Abdeckung jenseits Agents/Battery |

Architektonische offene Punkte ([`GG-AR-OPEN-002`](../../../../spec/architecture.md#19-offene-architektonische-punkte)..010) leben weiterhin
in `architecture.md` §19 und sind dort die kanonische Liste. Wenn
einer dieser Punkte einen konkreten Scope-Trigger erhaelt, wandert
eine Notiz auch hier nach `open/`.
