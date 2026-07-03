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

**Tooling / Build / Type-System:**

| Datei | Trigger | Aktivierung |
| ----- | ------- | ----------- |
| [`004-canonical-encoder-alternative-adr.md`](004-canonical-encoder-alternative-adr.md) | ADR fuer Performance-/Implementierungs-Alternativen (orjson, msgspec) | bei messbarem Perf-Druck am Telemetrie-Pfad |
| [`005-pyright-vs-mypy-reeval.md`](005-pyright-vs-mypy-reeval.md) | Re-Eval mypy vs. pyright bei generischen Protocols | sobald `ports/*` Generic-Protocols einfuehrt |
| [`007-pyright-precommit-adr.md`](007-pyright-precommit-adr.md) | ADR fuer pyright als Pre-Commit-Hook | bei Editor-Parity-Druck |

*(Trigger 048/050 (d-check-`matrix`) — **Resolved 2026-06-17** via Slice
[`049`](../done/049-sdp-matrix-doku-umbau.md), mit der M8-Closure nach
[`../done-archive/`](../done-archive/) archiviert; nicht mehr hier.)*

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
