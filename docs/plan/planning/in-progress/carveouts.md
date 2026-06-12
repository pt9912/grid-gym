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
Vier Typen (siehe `Typ`-Spalte in §2.1):

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

**Hinweis:** die §2-Tabellen tragen seit der Neuordnung
2026-06-12 keine Status-Spalte mehr — alles in §2 ist per
Definition offen; Resolved-Eintraege leben in §3.

**Typ vs. Status:** `Out-of-Scope`-Eintraege bleiben
permanent auf `Open` (kein Resolve-Pfad); `Deferred` und
`Trigger-Gated` durchlaufen typischerweise `Open` → `In
Trigger Watch` → `Active in M{N}-Welle-X` → `Resolved`;
`Pattern-Forward` bleibt `Open` bis zur ersten Adoption.

---

## 2. Aktive Carveouts

**Lesefuehrung (Neuordnung 2026-06-12):** §2.1 ist **eine**
Tabelle aller aktivierbaren Carveouts — 7 `Deferred`/
`Pattern-Forward` (Aktivierung per Mandat, `D-n`) + 21
`Trigger-Gated` (`T-nnn` = `open/`-Trigger-Nummer; zusammen
deckungsgleich mit dem `open/`-Bestand). Begruendungen sind per
ID nach §2.2 ausgelagert; fuer `T-nnn` traegt das Trigger-Doc
Begruendung + erwartete Lieferung. **Keine Status-Spalte**:
alles in §2 ist per Definition offen (Aufgeloestes → §3, dort
auch die Nummern-Historie-Map). §2.7 (Permanent
`Out-of-Scope`) behaelt seine gepinnte Nummer — die
„§2.7-Auflage" ist repo-weit als normativer Anker zitiert;
daher die bewusste Nummern-Luecke §2.3..§2.6.

### 2.1 Aktivierbare Carveouts (7 per Mandat + 21 per Trigger)

| ID | Item | Cluster | Typ | Quelle | Aktivierungs-Bedingung | Trigger-Doc |
| -- | ---- | ------- | --- | ------ | ---------------------- | ----------- |
| D-1 | Snapshot-Envelope-v2-Body-Serialisierung (`GET /snapshot`) | M5-Erbschaft | `Deferred` | M5-Welle 1 (Stub) + ADR 0015 v2 | Replay-/Export-Konsument braucht den vollen Envelope-Body ueber HTTP | — |
| D-2 | CSV/JSONL-Export-Endpunkte | M5-Erbschaft | `Deferred` | M5-Welle 6c §1.3 + `GG-ACCEPT-003` | konkreter Abnahme-/Analyse-Bedarf an Datei-Export | — |
| D-3 | Inline-SVG-Geraete-Grafik | M5-Erbschaft | `Deferred` | M5-Welle 6b §1.3 + Decision 23 | UI-Polish-Mandat | — |
| D-4 | Dynamische Fault-Activation ueber `POST /faults` | M5-Erbschaft | `Deferred` | M5-Welle 6a Decision 19 | Bedarf an Laufzeit-Fault-Injection jenseits der Szenario-YAML | — |
| D-5 | URL-Versionierung `/api/v1`-Mount-Prefix | M5-Erbschaft | `Deferred` | M5-Welle 6b §10.1 URL-Realization-Note | vor der naechsten URL-Kollision / dem naechsten Endpoint-Schub | — |
| D-6 | WebSocket-Live-Stream `/devices` | M5-Erbschaft | `Deferred` | M5-Welle 6b §1.3 | UX-Beschwerde ueber 1s-Polling-Latenz oder Live-Demo-Mandat | — |
| D-7 | Welle-3-Pre-init-Defense-Pattern verallgemeinern | M5-Erbschaft | `Pattern-Forward` | M5-Welle 6b Review-Folge F2 (`cd7cfc6`) | naechster device-iterierender Driving-Adapter, der `device.snapshot()` konsumiert | — |
| T-016 | EV-Charger-Device (`GG-DEV-015`) | SOLLTE-Geraete/Netz | `Trigger-Gated` | M2-Erbschaft | konkreter Bedarf — eigener Slice | [`016`](../open/016-sollte-ev-charger-device.md) |
| T-017 | Transformer-Device (`GG-DEV-016`) | SOLLTE-Geraete/Netz | `Trigger-Gated` | M2-Erbschaft | konkreter Bedarf — eigener Slice | [`017`](../open/017-sollte-transformer-device.md) |
| T-018 | Wind-Device (`GG-DEV-017`) | SOLLTE-Geraete/Netz | `Trigger-Gated` | M2-Erbschaft | konkreter Bedarf — eigener Slice | [`018`](../open/018-sollte-wind-device.md) |
| T-019 | Diesel-Device (`GG-DEV-018`) | SOLLTE-Geraete/Netz | `Trigger-Gated` | M2-Erbschaft | konkreter Bedarf — eigener Slice | [`019`](../open/019-sollte-diesel-device.md) |
| T-020 | Inselnetz-Bilanzmodell (`GG-GRID-005`) | SOLLTE-Geraete/Netz | `Trigger-Gated` | M2-Erbschaft | konkreter Bedarf — eigener Slice | [`020`](../open/020-sollte-island-grid.md) |
| T-021 | Transformatorgrenzen im Netzbilanzmodell (`GG-GRID-006`) | SOLLTE-Geraete/Netz | `Trigger-Gated` | M2-Erbschaft | konkreter Bedarf — eigener Slice | [`021`](../open/021-sollte-transformer-limits.md) |
| T-022 | Blindleistung im Netzbilanzmodell (`GG-GRID-007`) | SOLLTE-Geraete/Netz | `Trigger-Gated` | M2-Erbschaft | konkreter Bedarf — eigener Slice | [`022`](../open/022-sollte-reactive-power.md) |
| T-023 | Battery-Temperatur-Telemetry (`GG-BESS-006`) | SOLLTE-Geraete/Netz | `Trigger-Gated` | M2-Erbschaft | konkreter Bedarf — eigener Slice | [`023`](../open/023-sollte-battery-temperature.md) |
| T-024 | Battery-Zellspannung-Telemetry (`GG-BESS-007`) | SOLLTE-Geraete/Netz | `Trigger-Gated` | M2-Erbschaft | konkreter Bedarf — eigener Slice | [`024`](../open/024-sollte-battery-cell-voltage.md) |
| T-004 | Canonical-Encoder-Alternative-ADR (orjson, msgspec) | Tooling/Build | `Trigger-Gated` | M1-Tooling | bei messbarem Perf-Druck am Telemetrie-Pfad | [`004`](../open/004-canonical-encoder-alternative-adr.md) |
| T-005 | Pyright-vs-mypy-Re-Eval | Tooling/Build | `Trigger-Gated` | M1-Tooling | sobald `ports/*` Generic-Protocols einfuehrt | [`005`](../open/005-pyright-vs-mypy-reeval.md) |
| T-007 | Pyright-als-Pre-Commit-Hook-ADR | Tooling/Build | `Trigger-Gated` | M1-Tooling | bei Editor-Parity-Druck | [`007`](../open/007-pyright-precommit-adr.md) |
| T-011 | `MLRandomPort` Sub-Seed-Wortbreite (ADR 0007 §5.2/§6) | Tooling/Build | `Trigger-Gated` | M2-Tooling | bei `> 10⁶` Sub-Ports / hochskalierter Multi-Agent-Welle | [`011`](../open/011-mlrandomport-subseed-width.md) |
| T-032 | Release-Workflow-Sensor-Run-Verifikation (erstes reales Release steht aus) | Tooling/Build | `Trigger-Gated` | M6-Welle-2-DoD-Rest | erster echter `v*.*.*`-Tag-Push ODER Compliance-Druck | [`032`](../open/032-release-workflow-sensor-run.md) |
| T-033 | OTel-Collector Go-stdlib CVE-2026-42504-Bump (Temp-Deferral via vulnignore aktiv, ADR 0044; `expires: 2026-06-20`) | Tooling/Build | `Trigger-Gated` | M6-Welle-3-Post-Push | OTel-Collector-Release > 0.153.0 mit `go1.26.4+` ODER Compliance-Druck ODER vulnignore-`expires` 2026-06-20 | [`033`](../open/033-otel-collector-go-stdlib-cve-bump.md) |
| T-030 | Reinforcement-Learning-Agent-Adapter (`RL-Adapter`) | Forschung/Spike | `Trigger-Gated` | M3-Welle-7 Decision (C3) | RL-Forschungs-Bedarf oder Stakeholder-Aktivierung | [`030`](../open/030-rl-adapter.md) |
| T-026 | BESS-Simulation Reserve-Market-Spike | Forschung/Spike | `Trigger-Gated` (optionaler Spike) | M4-Erbschaft | bei Reserve-Market-Agent / BESS-SOC-Management / LER-Demo | [`026`](../open/026-bess-simulation-reserve-market-spike.md) |
| T-037 | `GG-DEPLOY-007..010` Kubernetes-Manifeste, Rolling Updates, Zero-Downtime-Grenzen, Rollback-Strategie | Multi-Node | `Trigger-Gated` | M6-Welle-6-Audit | Stakeholder-Bedarf fuer Multi-Node-/K8s-Deployment ODER Skalierungs-/Compliance-Druck | [`037`](../open/037-deploy-007-010-multi-node-deployment.md) |
| T-038 | Volle `GG-TERM-002/003`-Equality-Matrix (M7 liefert MVP-Preflight ueber 5 `RunMetadata`-Felder) | M7-Erbschaft | `Trigger-Gated` | M7-Welle-1b-a-D-6 | Compliance-/Audit-Bedarf ODER Multi-Plattform-/Multi-Adapter-Replay | [`038`](../open/038-gg-term-002-003-full-equality-matrix.md) |
| T-039 | Oeffentliche API-Replay-Bedienung (`POST /runs` `replay_of` + Migration) | M7-Erbschaft | `Trigger-Gated` | M7-Welle-1b-b-D-7 | Stakeholder-Forderung nach API-Replay ODER Compliance-Bedarf persistente Referenz-Bindung | [`039`](../open/039-api-replay-trigger-surface.md) |
| T-040 | Core-Run-End-Naht fuer `TickLoop.finalize()` (`make accept` faehrt Replay-Step standalone) | M7-Erbschaft | `Trigger-Gated` | M7-W1b-b-Review F4 / Welle 2 | Headless-Replay-Validierung im Abnahme-Pfad ODER Auto-`completed`-Transition | [`040`](../open/040-replay-finalize-headless-run-end-seam.md) |

### 2.2 Begruendungen (per ID)

Nur `D-n`- und `P-n`-Eintraege — fuer `T-nnn` tragen die
`open/`-Trigger-Docs Begruendung + erwartete Lieferung.

| ID | Begruendung (warum vertagt / warum out-of-scope) |
| -- | ------------------------------------------------ |
| D-1 | `GET /snapshot` liefert den `schema_ref`-Pointer — das erfuellt die Akzeptanz; volle Body-Serialisierung ist ADR-0015-v2-Erbschaft ohne MUSS-ID-Anker (der Replay-Pfad liest seit M7-Welle-1b direkt aus `telemetry_points`, nicht ueber HTTP). |
| D-2 | WS-Streams sind die dokumentierte Export-Surface (Welle-6c-Abnahmedoku); Datei-Export ist `GG-ACCEPT-003`-SOLLTE-Material ohne aktuellen Abnahme-Bedarf. |
| D-3 | `GG-UI-006`-Akzeptanz ist durch die HTMX-Polling-Tabelle erfuellt (Welle 6b, Decision 23); SVG-Grafik ist reiner UI-Polish ohne ID-Anker. |
| D-4 | `POST /faults` ist bewusst Form-Validation-only (Decision 19); YAML-seitige Fault-Injection (`GG-DEMO-006`, M5-Welle-6a) deckt den Demo-/Abnahme-Bedarf. |
| D-5 | Reine Konventions-Konsolidierung („natuerliche-URL-UI + suffixed-URL-JSON"-Pattern, §10.1) ohne Verhaltens-Effekt; lohnt erst, bevor neue Endpoints den Mismatch reproduzieren. |
| D-6 | 1s-HTMX-Polling erfuellt die `GG-UI-*`-Akzeptanz; Live-Push ist UX-Optimierung ohne ID-Anker. |
| D-7 | Generalisierungs-Empfehlung aus einem Einzel-Befund (`_extract_state_subset`-silent-drop); ein Lift ohne zweiten Adopter waere Spekulation (Pattern: Lift erst bei Wiederholung, vgl. 3b-D-7). |
| P-1 | Lastenheft fixiert: grid-gym ist Simulations-/Test-Werkzeug, **nicht** Steuerungs-Plattform. |
| P-2 | UI-Layer-Auth ist nicht von einer `GG-SAFE-*`-ID verlangt; IP-/Netz-Beschraenkung ist im Demo-Compose verankert (separate Auflagen-Schicht, kein einzelner Lastenheft-ID). `GG-SAFE-008` ist davon abzugrenzen — verlangt **externe Eingabevalidierung an REST/WS/Adapter-Schnittstellen** (M6-Security-Welle, siehe `M6-welle-0.md §1.3`). |
| P-3 | Nur bei Stakeholder-Druck (Architektur-Reinheit > UX-Glanz); kein Roadmap-Plan. |
| P-4 | Nur bei Chart.js-Limitationen (Re-Eval-Schwelle in Welle 3/4/6b unerreicht); kein Roadmap-Plan. |
| P-5 | Voller Anlagen-Schaltplan ist Post-MVP-Material; UI-Tabelle (Welle 6b) erfuellt `GG-UI-006`-Akzeptanz. |
| P-6 | `done/M5-results.md` ist Maintainer-Closure-Artefakt; `docs/user/gg-demo-008-abnahme.md` erfuellt `GG-DEMO-008`. End-User-Tutorial waere ein eigener Slice-Trigger (kein eingeplantes Ziel-M). |

### 2.7 Permanent (`Out-of-Scope`)

Quelle: [`../done/M5-results.md §8`](../done/M5-results.md) +
[`../done/M4-results.md §7`](../done/M4-results.md) +
[`../done/M3-results.md §7`](../done/M3-results.md). Diese
Items haben **keinen Aufloesungs-Plan** im Repo — entweder
strukturell ausgeschlossen (Lastenheft) oder bedingungs-
optional (z. B. „nur bei Stakeholder-Druck"). Begruendung per
ID in §2.2.

| ID | Item | Typ | Quelle |
| -- | ---- | --- | ------ |
| P-1 | Produktive Anlagensteuerung | `Out-of-Scope` | Lastenheft Z. 1161–1163 |
| P-2 | Multi-User + Auth im UI-Layer | `Out-of-Scope` | M5-results §8 + Lastenheft Demo-Compose-Konfiguration |
| P-3 | SvelteKit-SPA / React-SPA-Migration | `Out-of-Scope`-bedingt | M5-results §8 + ADR 0036 §2.5 |
| P-4 | Plotly.js / ECharts als Charting-Library | `Out-of-Scope`-bedingt | M5-results §8 + ADR 0036 §2.5 + Welle-6b Decision 23 |
| P-5 | Inline-SVG-Anlagenschaltbild (≠ Inline-SVG-Geraete-Grafik D-3) | `Out-of-Scope` | M5-results §8 + Welle-6b §1.3 |
| P-6 | End-User-Tutorial / Onboarding-Doku | `Out-of-Scope` | M5-results §8 |

**Konvention fuer `Out-of-Scope`-Eintraege:** bleiben
permanent im Index, wandern **nicht** in §3 Resolved.
Falls Stakeholder-Druck oder Lastenheft-Aenderung das
Item ploetzlich aktiv werden laesst, wandert es per
Lifecycle-Klausel (§4) nach §2.1 um (Typ-Wechsel zu
`Trigger-Gated` mit neu erstelltem `open/`-Trigger-Doc).

---

## 3. Resolved Carveouts (Audit-Trail-Auswahl)

Geschlossen mit M-Closure oder Welle-Lieferung; Eintraege
bleiben hier eine kurze Weile fuer Audit-Trail (volle History
in `done/`).

**Nummern-Historie (Neuordnung 2026-06-12):** §2 wurde nach
Lebenszyklus monoton neu nummeriert; Alt-Referenzen in
`done/`-Wellen-Docs uebersetzen sich so:

| Alt | Inhalt | Neu |
| --- | ------ | --- |
| §2.1 M5-Erbschaft | `Deferred`/`Pattern-Forward` | §2.1-Tabelle, Zeilen D-1..D-7 |
| §2.2 M4-Erbschaft | IEC-Smoke + krb5-Bump (aufgeloest in M6) | → §3-Zeilen |
| §2.3 M3-Erbschaft (RL-Adapter) | Trigger 030 | §2.1-Tabelle, Zeile T-030 |
| §2.4 M2-Erbschaft (SOLLTE) | Trigger 016..024 | §2.1-Tabelle, Zeilen T-016..T-024 |
| §2.5 Tooling/Build | Trigger 004/005/007/011/032/033 (008/031 aufgeloest → §3) | §2.1-Tabelle, Zeilen T-004..T-033 |
| §2.6 Spike-Optional | Trigger 026 | §2.1-Tabelle, Zeile T-026 |
| §2.7 Permanent | `Out-of-Scope` („§2.7-Auflage") | §2.7 (unveraendert, bewusst gepinnt; Zeilen P-1..P-6, Begruendungen in §2.2) |
| §2.8 M6-Vorbelegung | aufgeloest mit M6-Closure | → §3-Zeile |
| §2.9 Quality-Pipeline-Audit | Trigger 034/035 (geschlossen in M7-Welle-3) | → §3-Zeilen |
| §2.10 Multi-Node-Familie | Trigger 037 | §2.1-Tabelle, Zeile T-037 |
| §2.11 M7-Erbschaft | Trigger 038/039/040 | §2.1-Tabelle, Zeilen T-038..T-040 |

| Item | Geloest mit | Resolution-Hash |
| ---- | ----------- | --------------- |
| `--strict-bytes`-Aktivierung (`[tool.mypy]`) | M4-Welle-6a-C3 | Trigger-Doc nach [`../done/006-mypy-strict-bytes.md`](../done/006-mypy-strict-bytes.md) |
| `GG-DEMO-008` Abnahmedoku (Welle-5-Anti-Scope-Erbschaft) | M5-Welle-6c-C2 | `0e604e4` — NEU [`../../../user/gg-demo-008-abnahme.md`](../../../user/gg-demo-008-abnahme.md) |
| `GG-DEMO-006` YAML-side Fault-Injection (Welle-5-Anti-Scope-Erbschaft) | M5-Welle-6a-C2 | `db3a0c2` |
| `GG-UI-006..008` Geraete-Grafik + Fault-Form + Sim-Zustand | M5-Welle-6a/6b-C2 | `db3a0c2` + `9fcb887` |
| alt-§2.8 M6-Vorbelegung (Lastenheft-Familien `GG-RT-001..005` / `GG-SAFE-001..006` / `GG-CICD-*` / `GG-DEPLOY-*` / SBOM) | M6-Welle-0 (formaler Slice-Plan) + M6-Wellen 1..6 (Lieferung); M6-Closure 2026-06-08 — Rest-Luecken via Trigger 034/035/036 in M7 aufgeloest | [`../done/M6-results.md §2`](../done/M6-results.md) (Sektion §2.8 erst beim Post-M7-Index-Sweep 2026-06-12 nach §3 ueberfuehrt) |
| alt-§2.2 IEC-61850-In-Process-Smoke Reaktivierung (M4-Erbschaft) | M6-Welle-6-C2 (Pfad B: Dockerfile-Stage `iec61850-test` Python 3.12 + `make test-iec61850`; ADR 0046; Pfad A cp314-Wheel bleibt bevorzugte Endform) | Trigger-Doc nach [`../done/009-iec61850-smoke-reactivation.md`](../done/009-iec61850-smoke-reactivation.md) |
| alt-§2.2 Base-Image-Bump fuer krb5-CVE-Drift (M4-Erbschaft, `make fullbuild`-Defer) | M6-Welle-1-C2 (Null-Code-Edit; Debian-13.5-Upstream-Drift) | `b514170` — Trigger-Doc nach [`../done/010-base-image-krb5-cve-bump.md`](../done/010-base-image-krb5-cve-bump.md) |
| alt-§2.5 `make sbom` scharfschalten (`GG-CICD-007`) | M6-Welle-2-C2 (NEU `.github/workflows/release.yml`, 6 Artefakte; ADR 0042) | `235395e` — Trigger-Doc nach [`../done/008-sbom-activation.md`](../done/008-sbom-activation.md) |
| alt-§2.5 CI-Pflicht-Gate fuer `make fullbuild` | M6-Welle-3-C2 (NEU `.github/workflows/fullbuild.yml`) | `ce13253` — Trigger-Doc nach [`../done/031-ci-make-fullbuild-gate.md`](../done/031-ci-make-fullbuild-gate.md) |
| alt-§2.9 `GG-SAFE-004` `max_age`-stale-Quality-Markierung | M7-Welle-3a (TickLoop-Kwarg `max_age_ms` + Core-`STALE`-Stage, ADR 0052; Rest-Grenzen ADR 0052 §7) | `23c614a` + Review-Folge `5a9960a` — Trigger-Doc nach [`../done/034-safe-004-max-age-stale-quality.md`](../done/034-safe-004-max-age-stale-quality.md) |
| alt-§2.9 `GG-SAFE-003` Adapter-Comm-Failure → `MISSING` + Alarm | M7-Welle-3b (`CommFailureGuardedDeviceProtocolPort` + `adapter_communication_lost`-Alarm, ADR 0053; Rest-Grenzen ADR 0053 §2.1/§7) | `3f28be1` + Review-Folge `82704b1` — Trigger-Doc nach [`../done/035-safe-003-comm-failure-missing-quality.md`](../done/035-safe-003-comm-failure-missing-quality.md) |

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
