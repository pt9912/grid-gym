# Offene Plaene und Trigger-Watch

Dieses Verzeichnis sammelt **trigger-getriebene Folgearbeit** und
**Vorabklaerungen**, die noch nicht in die aktive Roadmap aufgenommen
wurden.

Eintraege wandern entweder:

- nach `next/`, sobald ein Scope skizziert ist, aber noch kein Slice aktiv,
- nach `in-progress/`, wenn sie direkt aktiviert werden, oder
- nach `archive/`, wenn sie bewusst verworfen werden.

Aufgeloeste Trigger werden mit der aufloesenden Slice-Closure
(rename-only) nach [`../done/`](../done/) verschoben — bei
gebuendelter Meilenstein-Closure nach
[`../done-archive/`](../done-archive/) — und sind dort gelistet,
nicht hier.

---

## Bestand

Alle Eintraege sind Trigger-Watch-Notizen (`Status: Open`) ohne
harten Aktivierungs-Zwang. Die `Aktivierung`-Spalte beschreibt den
konkreten Anlass, der eine Aktivierung ausloesen soll.

**Spec-Schichtung — Migrations-Arc ([`ADR 0080`](../../adr/0080-three-layer-spec-model.md)):**

Diese drei sind **geschnittene Arc-Slices** (nicht trigger-getrieben; s.
[`roadmap.md`](../in-progress/roadmap.md) Kopf-Status), sequenziell nach
[`083`](../next/083-spezifikation-layer-discipline-core-move.md) (in `next/`).
Der gesamte Arc 083–086 ist doku-/config-/kommentar-only → **kein Release**.

| Datei | Inhalt | Aktivierung |
| ----- | ------ | ----------- |
| [`084-architecture-bezug-drift-fix.md`](084-architecture-bezug-drift-fix.md) | Bezug-Drift-Fix (ARCH-007/008-Vollstaendigkeit + SCN-006-Luecke), [`ADR 0080`](../../adr/0080-three-layer-spec-model.md) §4.4 (ii) | nach [`083`](../next/083-spezifikation-layer-discipline-core-move.md) |
| [`085-spezifikation-layer-qs-families-move.md`](085-spezifikation-layer-qs-families-move.md) | QS-/Abnahme-Familien-Umzug (`GG-QA-*`/`GG-QG-*`/`GG-COV-*`/`GG-TESTTYPE-*`/`GG-ARCHTEST-*`), groesster Cut | nach 084 |
| [`086-traceability-derived-27-1-finalization.md`](086-traceability-derived-27-1-finalization.md) | [`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)-Amendment + §27.1 authored→derived + Konsistenz-Gate (Cross-Repo-Abh. d-check) | nach 085 |

**Tooling / Build / Type-System:**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`004-canonical-encoder-alternative-adr.md`](004-canonical-encoder-alternative-adr.md) | ADR fuer Performance-/Implementierungs-Alternativen (orjson, msgspec) | bei messbarem Perf-Druck am Telemetrie-Pfad |
| [`005-pyright-vs-mypy-reeval.md`](005-pyright-vs-mypy-reeval.md) | Re-Eval mypy vs. pyright bei generischen Protocols | sobald `ports/*` Generic-Protocols einfuehrt |
| [`007-pyright-precommit-adr.md`](007-pyright-precommit-adr.md) | ADR fuer pyright als Pre-Commit-Hook | bei Editor-Parity-Druck |

*(Trigger 048/050 (d-check-`matrix`) — **Resolved 2026-06-17** via Slice
[`049`](../done/049-sdp-matrix-doku-umbau.md), mit der M8-Closure nach
[`../done-archive/`](../done-archive/) archiviert; nicht mehr hier.)*

**Quality-Gates / Sensoren:**

*(Trigger 054 (pytest-Marker-Drift `determinism`/`fault`) — **Resolved
2026-07-10** via Slice-054-Closure; nach
[`../done/054-pytest-marker-drift-sensor-targets.md`](../done/054-pytest-marker-drift-sensor-targets.md)
verschoben und dort gelistet, nicht mehr hier. Keine offenen Sensor-Trigger.)*

**Doku-/Versions-Hygiene (Slice-038-Session-Befunde):**

*(Trigger 056 (ADR-Index-Status-Sync) + 057 (App-/Tool-Version-Single-Source)
— **Resolved 2026-07-10** als Buendel via Slice
[`059`](../done/059-hygiene-bundle-adr-index-app-version.md); nach
[`../done/`](../done/) verschoben und dort gelistet, nicht mehr hier.)*

**Harness-Regelwerk-Adoption (v1.2.0-Delta):**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- || [`052-carveout-modul07-audit-trichter.md`](052-carveout-modul07-audit-trichter.md) | Carveout-Disziplin Modul 07: Audit-Slice pro Welle-Closure + Werkzeug-Wahl-Trichter (Granularitaet vor Temporalitaet) — v1.2.0-Schaerfung ueber `MR-003` hinaus | Naechste Welle-/M8-Closure mit faelligem Carveout-Audit ODER `carveouts.md` ≥ 50 Eintraege (`MR-003` §4) |

**M3-/Multi-Agent-Folge:**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`011-mlrandomport-subseed-width.md`](011-mlrandomport-subseed-width.md) | `MLRandomPort` Sub-Seed-Wortbreite ([`ADR 0007`](../../adr/0007-random-port.md) §5.2/§6) | bei `> 10⁶` Sub-Ports / hochskalierter Multi-Agent-Welle |
| [`026-bess-simulation-reserve-market-spike.md`](026-bess-simulation-reserve-market-spike.md) | Lokale BESS-Simulation als Vorlage fuer Reserve-Market-/LER-Strategien | bei Reserve-Market-Agent, BESS-SOC-Management-Agent oder LER-Demo |
| [`030-rl-adapter.md`](030-rl-adapter.md) | RL-Adapter ueber den Multi-Agent-Bus ([`GG-FUTURE-001`](../../../../spec/lastenheft.md#gg-future-001)/002) | bei konkreter RL-Stakeholder-Anforderung (M7+-Material) |

**Multi-Node-Deployment-Familie (M6-Welle-6-Audit-Folge):**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`037-deploy-007-010-multi-node-deployment.md`](037-deploy-007-010-multi-node-deployment.md) | [`GG-DEPLOY-007`](../../../../spec/lastenheft.md#gg-deploy-007)..010 Kubernetes-Manifeste + Rolling-Updates + Zero-Downtime + Rollback — komplett Lücke; Architektur §16 Z. 916 fordert „Trigger-getriebene Folgearbeit" (diese Notiz erfuellt die Verankerungs-Pflicht) | Stakeholder-Bedarf fuer Multi-Node-/K8s-Deployment ODER Skalierungs-/Compliance-Druck |

**Protokolladapter-Erweiterungen:**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`047-device-management-protocol-adapters.md`](047-device-management-protocol-adapters.md) | SNMP/LwM2M als Device-Management- und Telemetry-Simulationsadapter ([`GG-SNMP-001`](../../../../spec/lastenheft.md#gg-snmp-001), [`GG-LWM2M-001`](../../../../spec/lastenheft.md#gg-lwm2m-001)) — noch ohne Profil-ADR, Adapter-Code oder Smoke-Test | Stakeholder-Bedarf fuer SNMP-/LwM2M-Demo ODER Integrationspartner-Mapping ODER Validation-Befund zu Device-Management-Protokollen |

**Anforderungs-Luecken (MUSS — aus Slice-060-Traceability-Audit):**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`061-replay-time-multipliers.md`](061-replay-time-multipliers.md) | [`GG-RT-006`](../../../../spec/lastenheft.md#gg-rt-006) (MUSS): Replay-Zeit-Multiplikatoren `0.5x/1x/10x/unbounded` fehlen — Tick-Frequenz ist Aufrufer-Sache | Slice am Run-/Replay-Pacing ODER formelle MUSS-Abnahme |
| [`062-run-deletion-operation.md`](062-run-deletion-operation.md) | [`GG-PERSIST-009`](../../../../spec/lastenheft.md#gg-persist-009) (MUSS): Lauf-Loeschung fehlt — kein `DELETE`-Endpoint / Repository-`delete` | Slice an der Run-Persistenz-/API-Surface ODER formelle MUSS-Abnahme |

**Security-Temp-Deferral (vulnignore, [`ADR 0044`](../../adr/0044-generated-trivyignore-permit.md)):**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`065-otel-collector-go-1265-cve.md`](065-otel-collector-go-1265-cve.md) | [`GG-QG-002`](../../../../spec/lastenheft.md#gg-qg-002): `CVE-2026-39822` (Go1.26.4→1.26.5, os.Root-Traversal) im OTel-Collector-Sidecar — kein gepatchtes Image; vulnignore-Deferral bis Upstream-Fix (`expires 2026-10-09`) | OTel-Collector-Stable mit go1.26.5+ verfuegbar ODER `expires`-Ablauf |
| [`069-vulnignore-expires-max-enforce.md`](069-vulnignore-expires-max-enforce.md) | `tools/render_trivyignore.py` erzwingt nur `expires >= heute`, nicht den [`ADR 0044`](../../adr/0044-generated-trivyignore-permit.md)-`+90-Tage`-**Max** (Review-N3a) | Nächster Security-/Tooling-Slice ODER zweiter vulnignore-Eintrag |

**Tooling — d-check-`doc-*`-Module (Handbuch-Review v0.41.0):**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`068-doc-modules-targets-commits-vcs.md`](068-doc-modules-targets-commits-vcs.md) | `targets`/`commits`/`vcs` scharf schalten — **C1 (`targets`, gate-phantom) erledigt**; offen: C1b (gate-undocumented, 38 Utility-Targets), C2 (`commits`, Vorwärts-Traceability), C3 (`vcs`, ADR-Immutabilität, braucht [`ADR 0028`](../../adr/0028-link-maintenance-accepted-adr-bezug.md)-C0) | Tooling-/Disziplin-Slice; C3 als eigener Slice mit Amendment |

**ADR-Konvention / Doku-Hygiene:**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`076-adr-delivery-agnostic-convention.md`](076-adr-delivery-agnostic-convention.md) | ADRs liefer-agnostisch halten (keine spezifischen `[Slice NNN]`-Refs im ADR-Body; Delivery-Mapping in ADR-Index/Roadmap). [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) folgt es bereits; [`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md)/[`ADR 0030`](../../adr/0030-device-protocol-port-surface.md) nachziehen | Naechste ADR-Hygiene-/Doku-Runde ODER neuer ADR wirft die Frage erneut auf |

**SOLLTE — M2-Welle-7-Erbschaft (mit M8 aufgeloest):** die neun
SOLLTE-Geraete-/Netz-/BESS-Trigger `016`..`024` sind mit M8
(Welle 2/3/4) auf `Resolved` gesetzt und mit der M8-Closure
(Welle 5, [`M8-welle-5.md`](../done/M8-welle-5.md)) nach
[`../done-archive/`](../done-archive/) archiviert — dort gelistet,
nicht mehr hier. Belege: [`M8-results.md`](../done/M8-results.md) §2.

Architektonische offene Punkte ([`GG-AR-OPEN-002`](../../../../spec/architecture.md#19-offene-architektonische-punkte)..010) leben weiterhin
in `architecture.md` §19 und sind dort die kanonische Liste. Wenn
einer dieser Punkte einen konkreten Scope-Trigger erhaelt, wandert
eine Notiz auch hier nach `open/`.
