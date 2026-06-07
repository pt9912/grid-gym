# Carveout-Index

**Status:** Lebend ab 2026-06-04 (M5-Closure-Folge-Sync).
**Zweck:** Eine **einzige Cross-Meilenstein-Sicht** auf alle
Scope-Entscheidungen, die bewusst auf spaetere Meilensteine /
spaetere Wellen verschoben wurden. Ergaenzt — ersetzt nicht —
die vier bestehenden Carveout-Surfaces des Repos:

| Surface | Granularitaet | Wo |
| ------- | ------------- | -- |
| Per-Welle `§1.3 Anti-Scope`-Block | feinste Aufloesung pro Welle | jede Welle-Slice-Doc unter `done/M{N}-welle-*.md §1.3` |
| Pro-M-Closure `§5 Erbschaft` + `§7/§8 Nicht-vollzogen` | aggregiert pro Meilenstein | [`../done/M3-results.md`](../done/M3-results.md), [`../done/M4-results.md`](../done/M4-results.md), [`../done/M5-results.md`](../done/M5-results.md) |
| `open/`-Trigger-Docs | formal-akzeptierter Trigger-Watch | [`../open/`](../open/) Bestand-Tabelle |
| `roadmap.md §4 M{N+1}`-Vorbelegung | DoD-Checkbox-Skizze | [`roadmap.md`](roadmap.md) §3 M6 |

**Warum dieses Dokument trotzdem?** Bisher mussten Reviewer
fuer eine vollstaendige Carveout-Sicht **drei M-results-Docs**
zusammen mit **17 `open/`-Trigger-Docs** und den Welle-Anti-
Scope-Bloecken querverlinken. Dieses Doc ist die zentrale
Index-Tabelle ueber alle aktiven Carveouts; jede Zeile zeigt
auf die kanonische Source, die im Welle/M-Closure verankert
wurde.

---

## 1. Konvention

**Carveout** = bewusster Verzicht im aktuellen Lieferumfang.
Vier Typen (siehe `Typ`-Spalte in jeder §2.x-Tabelle):

| Typ | Definition | Lebenszeit |
| --- | ---------- | ---------- |
| **`Deferred`** | Klares Ziel-M / Welle vorgesehen; wird geliefert | Bis Resolution; wandert dann in §3 Resolved und spaeter nach `done/M-results.md §5`. |
| **`Trigger-Gated`** | Wartet auf externe Bedingung; aktiviert sobald Bedingung eintritt | Gleich wie `Deferred` falls Bedingung eintritt; bleibt sonst unbegrenzt offen. Formaler Trigger-Doc in [`../open/`](../open/) ist Pflicht. |
| **`Out-of-Scope`** | Strukturell ausgeschlossen; **kein** Aufloesungs-Plan | Permanent im Index als Audit-Trail; Forward-Pointer auf Lastenheft- oder ADR-Begruendung. Wandert nicht. |
| **`Pattern-Forward`** | Welle-internes Hardening-Idiom als Generalisierungs-Empfehlung fuer spaetere Adopter | Bleibt bis zur ersten Adoptions-Welle; dann wandert die Generalisierungs-Lieferung in eine Welle und der Index-Eintrag wandert nach §3. |

**Status-Werte** (orthogonal zum Typ):

- `Open` — Forward-Pointer aktiv, keine Aufloesungs-Welle
  vorgesehen.
- `In Trigger Watch` — formaler Trigger-Doc in
  [`../open/`](../open/) mit Aktivierungs-Bedingung.
- `Active in M{N}-Welle-X` — Carveout in aktiver Welle in
  Bearbeitung.
- `Resolved {date} ({M-Welle-Hash})` — geschlossen; Eintrag
  wandert in §3 Resolved-Block oder raus.

**Typ vs. Status:** `Out-of-Scope`-Eintraege bleiben
permanent auf `Open` (kein Resolve-Pfad); `Deferred` und
`Trigger-Gated` durchlaufen typischerweise `Open` → `In
Trigger Watch` → `Active in M{N}-Welle-X` → `Resolved`;
`Pattern-Forward` bleibt `Open` bis zur ersten Adoption.

---

## 2. Aktive Carveouts

### 2.1 M5-Erbschaft fuer M6+ (6 Items)

Quelle: [`../done/M5-results.md §5`](../done/M5-results.md)
„Welle-7-Erbschaft fuer M6+" + §8 „Nicht-vollzogene Items".

| Item | Typ | Quell-Welle | Status | Aktivierungs-Bedingung | Trigger-Doc |
| ---- | --- | ----------- | ------ | ---------------------- | ----------- |
| Snapshot-Envelope-v2-Body-Serialisierung (`GET /snapshot`) | `Deferred` | Welle 1 (Stub) + ADR 0015 v2 | Open | M6-Replay-Surface oder eigener Slice | — (kein Open-Trigger) |
| CSV/JSONL-Export-Endpunkte | `Deferred` | Welle 6c §1.3 + `GG-ACCEPT-003` | Open | M6 oder eigener Slice | — |
| Inline-SVG-Geraete-Grafik | `Deferred` | Welle 6b §1.3 + Decision 23 | Open | M6 (UI-Polish-Welle) | — |
| Dynamische Fault-Activation ueber `POST /faults` | `Deferred` | Welle 6a Decision 19 | Open | M6 (Fault-Pipeline-Erweiterung) | — |
| URL-Versionierung `/api/v1`-Mount-Prefix | `Deferred` | Welle 6b §10.1 URL-Realization-Note | Open | vor naechster URL-Kollision oder M6-Welle-X | — |
| WebSocket-Live-Stream `/devices` | `Deferred` | Welle 6b §1.3 | Open | M6 (UI-Live-Updates statt 1s-Polling) | — |
| Welle-3-Pre-init-Defense-Pattern verallgemeinern | `Pattern-Forward` | Welle 6b Review-Folge F2 (`cd7cfc6`) | Open | M6-Welle-X-Adapter-Hardening-Sweep | — |

### 2.2 M4-Erbschaft (2 Items; ueber M5 weitergereicht)

Quelle: [`../done/M4-results.md §5`](../done/M4-results.md) +
[`../done/M5-results.md §5`](../done/M5-results.md) +
[`../open/`](../open/).

| Item | Typ | Quelle | Status | Aktivierungs-Bedingung | Trigger-Doc |
| ---- | --- | ------ | ------ | ---------------------- | ----------- |
| IEC-61850-In-Process-Smoke Reaktivierung | `Trigger-Gated` | M4-Welle-5b + M4-Welle-6b-C3 | **Active in M6-Welle-6** (Pfad B; per M6-Welle-0-C2-Triage) | `pyiec61850-ng` cp314-Wheel (Pfad A) ODER Multi-Python-Test-Stage (Pfad B) | [`009-iec61850-smoke-reactivation.md`](../open/009-iec61850-smoke-reactivation.md) |
| Base-Image-Bump fuer krb5-CVE-Drift (`make fullbuild`-Defer) | `Aufgeloest` | M3-Welle-7-`c61ab0d` pre-existing | **Aufgeloest in M6-Welle-1-C2 `b514170`** (Null-Code-Edit; Debian-13.5-Upstream-Drift + Trigger-015-`apt-get upgrade`-Pattern) | n/a (aufgeloest) | [`010-base-image-krb5-cve-bump.md`](../done/010-base-image-krb5-cve-bump.md) |

### 2.3 M3-Erbschaft (RL-Adapter)

Quelle: [`../done/M3-results.md §5`](../done/M3-results.md).

| Item | Typ | Quelle | Status | Aktivierungs-Bedingung | Trigger-Doc |
| ---- | --- | ------ | ------ | ---------------------- | ----------- |
| Reinforcement-Learning-Agent-Adapter (`RL-Adapter`) | `Trigger-Gated` | M3-Welle-7 Decision (C3) | In Trigger Watch | RL-Forschungs-Bedarf oder Stakeholder-Aktivierung | [`030-rl-adapter.md`](../open/030-rl-adapter.md) |

### 2.4 M2-Erbschaft (SOLLTE-Geraete + Netzbilanz, 9 Items)

Quelle: [`../done/M2-devices-results.md §5`](../done/M2-devices-results.md) +
[`../done/M3-results.md §5`](../done/M3-results.md) +
[`../done/M4-results.md §5`](../done/M4-results.md) (Re-Triage).

Alle 9 Items haben `Typ = Trigger-Gated`; Aktivierungs-
Bedingung pro Item: „wenn konkreter Bedarf — eigener Slice".

| Item | Lastenheft-ID | Status | Trigger-Doc |
| ---- | ------------- | ------ | ----------- |
| EV-Charger-Device | `GG-DEV-015` | In Trigger Watch | [`016-sollte-ev-charger-device.md`](../open/016-sollte-ev-charger-device.md) |
| Transformer-Device | `GG-DEV-016` | In Trigger Watch | [`017-sollte-transformer-device.md`](../open/017-sollte-transformer-device.md) |
| Wind-Device | `GG-DEV-017` | In Trigger Watch | [`018-sollte-wind-device.md`](../open/018-sollte-wind-device.md) |
| Diesel-Device | `GG-DEV-018` | In Trigger Watch | [`019-sollte-diesel-device.md`](../open/019-sollte-diesel-device.md) |
| Inselnetz-Bilanzmodell | `GG-GRID-005` | In Trigger Watch | [`020-sollte-island-grid.md`](../open/020-sollte-island-grid.md) |
| Transformatorgrenzen im Netzbilanzmodell | `GG-GRID-006` | In Trigger Watch | [`021-sollte-transformer-limits.md`](../open/021-sollte-transformer-limits.md) |
| Blindleistung im Netzbilanzmodell | `GG-GRID-007` | In Trigger Watch | [`022-sollte-reactive-power.md`](../open/022-sollte-reactive-power.md) |
| Battery-Temperatur-Telemetry | `GG-BESS-006` | In Trigger Watch | [`023-sollte-battery-temperature.md`](../open/023-sollte-battery-temperature.md) |
| Battery-Zellspannung-Telemetry | `GG-BESS-007` | In Trigger Watch | [`024-sollte-battery-cell-voltage.md`](../open/024-sollte-battery-cell-voltage.md) |

### 2.5 Tooling- / Build- / Type-System-Trigger (8 Items)

Quelle: [`../open/`](../open/). Alle Items haben `Typ =
Trigger-Gated`.

| Item | Status | Aktivierungs-Bedingung | Trigger-Doc |
| ---- | ------ | ---------------------- | ----------- |
| Canonical-Encoder-Alternative-ADR (orjson, msgspec) | In Trigger Watch | bei messbarem Perf-Druck am Telemetrie-Pfad | [`004-canonical-encoder-alternative-adr.md`](../open/004-canonical-encoder-alternative-adr.md) |
| Pyright-vs-mypy-Re-Eval | In Trigger Watch | sobald `ports/*` Generic-Protocols einfuehrt | [`005-pyright-vs-mypy-reeval.md`](../open/005-pyright-vs-mypy-reeval.md) |
| Pyright-als-Pre-Commit-Hook-ADR | In Trigger Watch | bei Editor-Parity-Druck | [`007-pyright-precommit-adr.md`](../open/007-pyright-precommit-adr.md) |
| `make sbom` scharfschalten (`GG-CICD-007`) | **Aufgeloest in M6-Welle-2-C2 `235395e`** (NEU `.github/workflows/release.yml` mit 3 Jobs + 6 publizierte Artefakte; Makefile sbom-Scan-Ziel auf Runtime-Image; ADR 0042 `Provisional`) | n/a (aufgeloest) | [`008-sbom-activation.md`](../done/008-sbom-activation.md) |
| `MLRandomPort` Sub-Seed-Wortbreite (ADR 0007 §5.2/§6) | In Trigger Watch | bei `> 10⁶` Sub-Ports / hochskalierter Multi-Agent-Welle | [`011-mlrandomport-subseed-width.md`](../open/011-mlrandomport-subseed-width.md) |
| CI-Pflicht-Gate fuer `make fullbuild` (M6-Welle-1-D-1-Vertagung) | **Aufgeloest in M6-Welle-3-C2 `ce13253`** (NEU `.github/workflows/fullbuild.yml` mit Hybrid Push/PR-Paths-Filter + workflow_dispatch; `make fullbuild` cache-frei gruen) | n/a (aufgeloest) | [`031-ci-make-fullbuild-gate.md`](../done/031-ci-make-fullbuild-gate.md) |
| Release-Workflow-Sensor-Run-Verifikation (M6-Welle-2-DoD-Reste) | In Trigger Watch | erster echter `v*.*.*`-Tag-Push ODER M6-Welle-3-Entscheidung ODER Compliance-Druck | [`032-release-workflow-sensor-run.md`](../open/032-release-workflow-sensor-run.md) |
| OTel-Collector Go-stdlib CVE-2026-42504-Bump (`make fullbuild`-Defer; M6-Welle-3-Post-Push-`ede21ad`-Aufdeckung) | **Temp-Deferral aktiv** seit M6-Welle-4a-C2 `8fbd17c` (NEU vulnignore-Pattern + ADR-0044; CI gruen via generierter `.trivyignore` mit `expires: 2026-06-20`); In Trigger Watch fuer echte Aufloesung | OTel-Collector-Release > 0.153.0 mit `go1.26.4+`-Build (erwartet 2026-06-09..06-12 per ~14-Tage-Kadenz) ODER Compliance-Druck ODER vulnignore-`expires`-Schwelle 2026-06-20 | [`033-otel-collector-go-stdlib-cve-bump.md`](../open/033-otel-collector-go-stdlib-cve-bump.md) |

### 2.6 Spike-Optional (1 Item)

| Item | Typ | Status | Aktivierungs-Bedingung | Trigger-Doc |
| ---- | --- | ------ | ---------------------- | ----------- |
| BESS-Simulation Reserve-Market-Spike | `Trigger-Gated` (optionaler Spike) | In Trigger Watch | bei Reserve-Market-Agent / BESS-SOC-Management / LER-Demo | [`026-bess-simulation-reserve-market-spike.md`](../open/026-bess-simulation-reserve-market-spike.md) |

### 2.7 Permanent (`Out-of-Scope`)

Quelle: [`../done/M5-results.md §8`](../done/M5-results.md) +
[`../done/M4-results.md §7`](../done/M4-results.md) +
[`../done/M3-results.md §7`](../done/M3-results.md). Diese
Items haben **keinen Aufloesungs-Plan** im Repo — entweder
strukturell ausgeschlossen (Lastenheft) oder bedingungs-
optional (z. B. „nur bei Stakeholder-Druck").

| Item | Typ | Quelle | Begruendung |
| ---- | --- | ------ | ----------- |
| Produktive Anlagensteuerung | `Out-of-Scope` | Lastenheft Z. 1161–1163 | Lastenheft fixiert: grid-gym ist Simulations-/Test-Werkzeug, **nicht** Steuerungs-Plattform. |
| Multi-User + Auth im UI-Layer | `Out-of-Scope` | M5-results §8 + Lastenheft Demo-Compose-Konfiguration | UI-Layer-Auth ist nicht von einer `GG-SAFE-*`-ID verlangt; IP-/Netz-Beschraenkung ist im Demo-Compose verankert (separate Auflagen-Schicht, kein einzelner Lastenheft-ID). `GG-SAFE-008` ist davon abzugrenzen — `GG-SAFE-008` verlangt **externe Eingabevalidierung an REST/WS/Adapter-Schnittstellen** und gehoert zur M6-Security-Welle (siehe `M6-welle-0.md §1.3`). |
| SvelteKit-SPA / React-SPA-Migration | `Out-of-Scope`-bedingt | M5-results §8 + ADR 0036 §2.5 | Nur bei Stakeholder-Druck (Architektur-Reinheit > UX-Glanz); kein Roadmap-Plan. |
| Plotly.js / ECharts als Charting-Library | `Out-of-Scope`-bedingt | M5-results §8 + ADR 0036 §2.5 + Welle-6b Decision 23 | Nur bei Chart.js-Limitationen (Re-Eval-Schwelle in Welle 3/4/6b unerreicht); kein Roadmap-Plan. |
| Inline-SVG-Anlagenschaltbild (≠ Inline-SVG-Geraete-Grafik §2.1) | `Out-of-Scope` | M5-results §8 + Welle-6b §1.3 | Voller Anlagen-Schaltplan ist M6+-Material; UI-Tabelle (Welle 6b) erfuellt `GG-UI-006`-Akzeptanz. |
| End-User-Tutorial / Onboarding-Doku | `Out-of-Scope` | M5-results §8 | `done/M5-results.md` ist Maintainer-Closure-Artefakt; `docs/user/gg-demo-008-abnahme.md` erfuellt `GG-DEMO-008`. End-User-Tutorial waere ein eigener Slice-Trigger (kein eingeplantes Ziel-M). |

**Konvention fuer `Out-of-Scope`-Eintraege:** bleiben
permanent im Index, wandern **nicht** in §3 Resolved.
Falls Stakeholder-Druck oder Lastenheft-Aenderung das
Item ploetzlich aktiv werden laesst, wandert es per
Lifecycle-Klausel (§4) in eine andere §2.x-Kategorie um
(z. B. `Trigger-Gated` mit neu erstelltem `open/`-
Trigger-Doc).

### 2.8 M6-Vorbelegung (Lastenheft-Pflicht-IDs)

Quelle: [`roadmap.md §4 M6`](roadmap.md). Diese sind keine
Carveouts im engeren Sinne (M6 ist der Hauptbestimmungs-Ort),
sondern Vorbelegungs-DoD-Items, die mit M6-Welle-0 in einen
formalen M6-Slice-Plan wandern.

| Lastenheft-Familie | Anzahl IDs | Lieferziel |
| ------------------ | ---------- | ---------- |
| `GG-RT-001..005` | 5 | Performance-Schranken (10k-Points/s-Benchmark) |
| `GG-SAFE-001..006` | 6 | Sicherheits-Audit |
| `GG-CICD-001..00X` | ≥7 | CI/CD-Vollausbau (4 Slice-025-ausgelagerte Items + Release-Workflow + SBOM + Test-Matrix) |
| `GG-DEPLOY-001..00X` | ≥X | Deploy-Hardening (Container-Smoke + Image-Audit + krb5-Bump-Erbschaft) |
| `GG-SBOM-001..00X` | ≥1 | SBOM-Generierung (Trigger 008) |

### 2.9 Quality-Pipeline-Audit-Luecken (M6-Welle-5a, 2 Items)

Quelle: [`../open/`](../open/) + [`../../../user/safe-001-004-quality-pipeline.md`](../../../user/safe-001-004-quality-pipeline.md).
Alle Items haben `Typ = Trigger-Gated`; aus M6-Welle-5a-Audit
hervorgegangen (Welle-5a-D-3 Hybrid-Strategie: substantielle
Substanz-Lücken werden als NEU `open/`-Trigger vertagt, nicht
inline gefixt). Eigene Cluster-Sektion statt §2.5-Verklumpung,
weil SAFE-IDs Lastenheft-Domain-Items sind, nicht Tooling-/
Build-Trigger.

| Item | Status | Aktivierungs-Bedingung | Trigger-Doc |
| ---- | ------ | ---------------------- | ----------- |
| `GG-SAFE-004` `max_age`-stale-Quality-Markierung (Lücke — `max_age`-Substanz fehlt komplett im Repo) | In Trigger Watch | Compliance-/Stakeholder-Druck auf konkrete `max_age`-Schwelle ODER M6-Welle-7-Closure-Sweep ODER Welle-X-Maintainer-Entscheidung | [`034-safe-004-max-age-stale-quality.md`](../open/034-safe-004-max-age-stale-quality.md) |
| `GG-SAFE-003` Adapter-Kommunikationsausfall → `MISSING`/`STALE` + Alarm (partial Lücke — SmartMeter-pre-attach teil-produktiv) | In Trigger Watch | Reale-Compose-Demo-Pfad mit Protocol-Adapter ODER M6-Welle-6-Deploy-Hardening (Trigger 009-Erbschaft) ODER Compliance-Druck ODER M6-Welle-7-Closure-Sweep | [`035-safe-003-comm-failure-missing-quality.md`](../open/035-safe-003-comm-failure-missing-quality.md) |

### 2.10 Multi-Node-Deployment-Familie (M6-Welle-6-Audit-Folge)

Quelle: [`../open/`](../open/) + Trigger
[`037`](../open/037-deploy-007-010-multi-node-deployment.md).
Alle Items haben `Typ = Trigger-Gated`; aus dem M6-Welle-6-
Deploy-Hardening-Audit hervorgegangen. `GG-DEPLOY-007..010`
bleiben Post-MVP/M7+-Material, bis ein konkreter Multi-Node-,
Skalierungs- oder Compliance-Anker vorliegt.

| Item | Status | Aktivierungs-Bedingung | Trigger-Doc |
| ---- | ------ | ---------------------- | ----------- |
| `GG-DEPLOY-007..010` Kubernetes-Manifeste, Rolling Updates, Zero-Downtime-Grenzen und Rollback-Strategie | In Trigger Watch | Stakeholder-Bedarf fuer Multi-Node-/K8s-Deployment ODER Skalierungs-/Compliance-Druck | [`037-deploy-007-010-multi-node-deployment.md`](../open/037-deploy-007-010-multi-node-deployment.md) |

---

## 3. Resolved Carveouts (Audit-Trail-Auswahl)

Geschlossen mit M-Closure oder Welle-Lieferung; Eintraege
bleiben hier eine kurze Weile fuer Audit-Trail (volle History
in `done/`).

| Item | Geloest mit | Resolution-Hash |
| ---- | ----------- | --------------- |
| `--strict-bytes`-Aktivierung (`[tool.mypy]`) | M4-Welle-6a-C3 | Trigger-Doc nach [`../done/006-mypy-strict-bytes.md`](../done/006-mypy-strict-bytes.md) |
| `GG-DEMO-008` Abnahmedoku (Welle-5-Anti-Scope-Erbschaft) | M5-Welle-6c-C2 | `0e604e4` — NEU [`../../../user/gg-demo-008-abnahme.md`](../../../user/gg-demo-008-abnahme.md) |
| `GG-DEMO-006` YAML-side Fault-Injection (Welle-5-Anti-Scope-Erbschaft) | M5-Welle-6a-C2 | `db3a0c2` |
| `GG-UI-006..008` Geraete-Grafik + Fault-Form + Sim-Zustand | M5-Welle-6a/6b-C2 | `db3a0c2` + `9fcb887` |

(Liste nicht erschoepfend; volle Resolution-Historie pro M
in `done/M{N}-results.md §5` + §8.)

---

## 4. Lifecycle + Pflege-Konvention

**Wann ergaenzt der Index?**

- Bei jeder Welle-Closure (`C3-Sync`): pro neu angelegtem
  Welle-Anti-Scope-Item pruefen, ob es als Trigger-Watch in
  `open/` formalisiert werden sollte → falls ja, Trigger-Doc
  anlegen UND Zeile hier ergaenzen.
- Bei jeder M-Closure (`Welle-7-C2 M-results.md`): die §5/§8-
  Eintraege gegen diesen Index abgleichen; redundante oder
  bereits abgedeckte Items mit Cross-Link versehen, neue als
  eigene Zeile aufnehmen.

**Wann reduziert der Index?**

- `Deferred` / `Trigger-Gated` / `Pattern-Forward`-Items
  werden durch eine Welle-Lieferung aufgeloest → Zeile in §3
  Resolved-Block fuer Audit-Trail; nach M-Closure (z. B.
  M+1-Welle-7) gehoert die §3-Zeile in das jeweilige
  `done/M{N}-results.md §5 Resolution` und kann hier raus.
- **`Out-of-Scope`-Items wandern nicht** — sie bleiben
  permanent im §2.7-Block als Audit-Trail. Falls Stakeholder-
  Druck oder Lastenheft-Aenderung sie ploetzlich aktiv werden
  laesst, **wandert der Typ** (z. B. `Out-of-Scope` →
  `Trigger-Gated`) und ein formaler `open/`-Trigger-Doc
  wird angelegt.

**Was lebt nicht hier?**

- Pro-Welle-Anti-Scope-Bloecke `§1.3` (zu granular; siehe
  Source-Slice-Doc).
- Welle-interne DoD-Checkboxen (`§9` der Slice-Doc).
- Lastenheft-IDs ohne Forward-Pointer (siehe `roadmap.md §3
  M{N}` DoD-Checkliste).

**Wann sollte das Dokument selbst gesplittet werden?**

- Wenn Tabelle ≥ 50 Eintraege wird (Cross-M-Sicht wird
  unuebersichtlich).
- Wenn Resolved-Block ≥ 30 Zeilen wird (Audit-Trail-
  Verschieberung nach `done/M-results.md` faellig).

---

## 5. References

- [`../done/M5-results.md §5 + §8`](../done/M5-results.md)
  — M5-Welle-7-Erbschaft + Nicht-vollzogen.
- [`../done/M4-results.md §5 + §7`](../done/M4-results.md)
  — M4-Welle-7-Erbschaft + Nicht-vollzogen.
- [`../done/M3-results.md §5 + §7`](../done/M3-results.md)
  — M3-Welle-7-Erbschaft + Nicht-vollzogen.
- [`../done/M2-devices-results.md`](../done/M2-devices-results.md)
  — M2-SOLLTE-Geraete-Quelle.
- [`../open/README.md`](../open/README.md) — Bestand-Tabelle
  der formal-akzeptierten Trigger-Watch-Eintraege.
- [`roadmap.md §4 M6`](roadmap.md) — M6-Vorbelegung mit DoD-
  Checkbox-Skizze.
- [`../README.md`](../README.md) — Planning-Verzeichnis-
  Lifecycle-Konvention.
