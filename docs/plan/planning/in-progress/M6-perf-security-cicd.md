# Slice-Plan — M6 Performance + Security + CI/CD-Haertung — In Progress

**Status:** In Progress — eroeffnet 2026-06-04 mit M6-Welle-0-
C1 (dieser Commit). Welle 0 (Slice-Plan-Eroeffnung + Trigger-
Triage) ist aktiv; Welle 1+-Substanz-Wellen folgen.

**Datum:** 2026-06-04 (in `in-progress/` direkt eroeffnet
ohne `next/`-Zwischenschritt; Welle-0-Doc-Hoheit fuer den
Hintergrund liegt in [`M6-welle-0.md`](M6-welle-0.md) §1).

**Bezug:**

- [`roadmap.md`](roadmap.md) §3 M6 (Lieferziel, DoD-
  Checkliste, Architekturartefakte).
- [`carveouts.md`](carveouts.md) (Cross-Meilenstein-
  Carveout-Index; M6-Welle-0-C2-Triage ist die primaere
  Pflege-Welle).
- M5-Closure-Notiz
  [`../done/M5-results.md`](../done/M5-results.md) §5
  „Welle-7-Erbschaft fuer M6+".
- [`M6-welle-0.md`](M6-welle-0.md) §3 Decision-Liste
  (7 offene Decisions fuer Welle 1+).
- [`../../adr/0030-device-protocol-port-surface.md`](../../adr/0030-device-protocol-port-surface.md)
  + M4-/M5-ADRs (0030..0040) — M6 baut auf der voll-
  ausgereiften Adapter- + Driving-Surface auf, ohne neuen
  Driving-Port einzuziehen.
- [`../../../../spec/lastenheft.md`](../../../../spec/lastenheft.md)
  §22 (`GG-RT-001..005`) + §23 (`GG-SAFE-001..008`) +
  CI/CD-Kapitel (`GG-CICD-001..007` inkl. `GG-CICD-007`
  Release-Workflow mit SBOM-Hook ueber Trigger 008;
  `GG-DEPLOY-*`). **Keine eigene `GG-SBOM-*`-Lastenheft-
  Familie** — SBOM ist ueber `GG-CICD-007` verankert.

---

## 1. Zweck

M6 liefert die **operative Haertung** der M1..M5-Foundation
in drei orthogonalen Querschnitts-Bereichen:

- **Performance** (`GG-RT-001..005`): 10 000-Points/s-
  Benchmark + Tick-Drift-Schranken + Performance-Methodologie
  (Bench-Framework, Mess-Protokoll, Regression-Gate).
- **Security** (`GG-SAFE-001..008`): Sicherheits-Audit-
  Familie inkl. **`GG-SAFE-008` externe Eingabevalidierung
  an REST/WebSocket/Adapter-Schnittstellen** + IP-/Netz-
  Beschraenkung im Demo-Compose (separate Auflagen-Schicht
  ohne einzelne `GG-SAFE-*`-ID).
- **CI/CD-Vollausbau** (`GG-CICD-001..007`): GitHub-Actions-
  Matrix Python 3.13+3.14, Tests/Coverage/Dep-Audit als CI-
  Jobs neben den vier Slice-025-Pflicht-Gates, Release-
  Workflow inkl. SBOM-Hook (`GG-CICD-007` + Trigger 008),
  Image-Audit (`GG-DEPLOY-*` + krb5-CVE-Bump-M4-Erbschaft
  ueber Trigger 010).

Plus eine **Deploy-Hardening-Schicht** (`GG-DEPLOY-*`):
Image-Audit + Container-Smoke + Healthcheck-Pollung +
krb5-Bump.

**Architektur-Familie:** M6 fuehrt **keinen neuen Driving-
Port** ein. Die M1..M5-Foundation (Tick-Loop, Devices,
Faults, Agents, Observability, Protokolladapter, UI, Demo)
ist Voraussetzung; M6 setzt nur Quer-Schicht-Aenderungen
(CI-Workflow, Image, Performance-Bench-Pfad,
Eingabevalidierungs-Hardening).

**Erbschaft aus M5** ([`../done/M5-results.md §5`](../done/M5-results.md)):
6 `Deferred`-Items (Snapshot-Envelope-v2-Body, CSV/JSONL-
Export, Inline-SVG-Geraete-Grafik, Dynamische Fault-
Activation, URL-Versionierung `/api/v1`, WebSocket-Live-
Stream `/devices`) + 1 `Pattern-Forward` (Welle-3-Pre-
init-Defense-Pattern) sind im Carveout-Index
[`carveouts.md §2.1`](carveouts.md). Welle-Zuordnung
erfolgt in Welle-1-C0 + ggf. Welle-Polish-C0.

---

## 2. Erfolgskriterien

- **MUSS-IDs erfuellt:**
  - `GG-RT-001..005` (5 Items): Echtzeit- und
    Performance-Schranken inkl. 10 000-Points/s-Benchmark
    (`GG-RT-005`).
  - `GG-SAFE-001..008` (8 Items): Sicherheits-Audit-
    Familie inkl. externe Eingabevalidierung.
  - `GG-CICD-001..007` (7 Items): CI-Pflicht-Gate-Familie
    inkl. Tests/Coverage/Dep-Audit-CI-Jobs + Release-
    Workflow.
  - `GG-DEPLOY-001..00X` (≥X Items): Container-Hardening +
    Image-Audit + Healthcheck-Pollung.
- **Trigger-Aufloesung:**
  - **Trigger 008** (SBOM-Aktivierung) in `GG-CICD-007`-
    Release-Workflow-Welle.
  - **Trigger 009** (IEC-Smoke-Reaktivierung Pfad-B) als
    separater Slice (Multi-Python-Test-Stage; Repo-Novum-
    Material; M4-Erbschaft).
  - **Trigger 010** (Base-Image-krb5-Bump) in M6-Welle-1
    (M4-Erbschaft; `make fullbuild` cache-frei gruen).
- **DoD-Gates:**
  - `make gates` cache-frei gruen ohne Override am M6-
    Closure-Hash (10 A-1-Gates; ggf. neue Gates pro Welle).
  - `make fullbuild` cache-frei gruen (Trigger 010 in
    Welle 1 aufgeloest).
  - `make docs-check` cache-frei gruen.
  - **NEU CI-Pflicht-Gates** (GitHub-Actions): test-unit +
    coverage + dep-audit + image-audit als CI-Jobs (heute
    nur 4 lokal in `make gates`, in CI nur 4).
  - **NEU Performance-Regression-Gate**: `make perf`-Target
    + `GG-RT-005`-Bench reproduzierbar; Regress-Schwelle
    pinned.
- **ADR-Lifecycle:**
  - 1-3 M6-ADRs erwartet (Soll-Wert per ADR 0011);
    Vorbelegung in [`M6-welle-0.md §3 M6-D-4`](M6-welle-0.md):
    NEU ADR 0041 (Performance-Bench-Pattern), NEU ADR 0042
    (SBOM-Tool + CI-Hook), ggf. NEU ADR 0043 (Image-Audit-
    Pflicht-Strategie).
  - M6-Welle-7-Closure zieht alle M6-ADRs auf `Accepted`.

---

## 3. Liefer-Reihenfolge (Wellen)

**Sub-Slicing-Schwelle** (analog M4/M5): wenn eine Welle
voraussichtlich > 300 Zeilen Slice-Doc ODER > 5 Code-Commits
ODER mehr als zwei unabhaengige Sub-Bereiche umfasst, wird
sie in W-a/W-b sub-geslict. Welle-Sub-Slicing wird in der
betreffenden Welle-C0-Slice-Doc beschlossen, nicht hier
vorab vorbelegt.

**Welle-Strategie**: Vorbelegung **Option B** aus
[`M6-welle-0.md §3 M6-D-1`](M6-welle-0.md) — pro Triggerebene
(klein → mittel → gross), damit krb5-Bump + SBOM als
Schnell-Wins vor den groesseren Performance-/Security-/CI-
Vollausbau-Wellen laufen. Final entschieden mit Welle-1-C0.

### 3.1 Welle-Status-Tabelle

Quick-Glance ueber alle 7+ M6-Wellen. Substanz-Detail
(Liefer-Hash-Stack, DoD-Checkboxen, C2-Realization-Notes,
Review-Findings, Test-Counts am Closure-Hash) lebt im
jeweiligen Welle-Slice-Doc unter `done/` bzw.
`in-progress/`.

| # | Titel | Status | Slice-Doc | Lastenheft-Coverage / Trigger | ADRs |
| - | ----- | ------ | --------- | ----------------------------- | ---- |
| 0 | Slice-Plan-Eroeffnung + Trigger-Triage | In Progress 2026-06-04 | [`M6-welle-0.md`](M6-welle-0.md) | Plan-Welle (7 Decisions vorbelegt) | — (kein C1) |
| 1 | Base-Image-Bump (krb5-CVE-Aufloesung) | Pending | TBD (entsteht in Welle-1-C0) | Trigger 010 + `make fullbuild`-Defer-Aufloesung | TBD (ggf. ADR 0043 Image-Audit-Strategie) |
| 2 | SBOM-Aktivierung + Release-Workflow | Pending | TBD (entsteht in Welle-2-C0) | `GG-CICD-007` + Trigger 008 | TBD (ggf. ADR 0042 SBOM-Tool) |
| 3 | CI/CD-Vollausbau | Pending | TBD (entsteht in Welle-3-C0) | `GG-CICD-001..006` (Test/Coverage/Dep-Audit-CI-Jobs + Python-3.13/3.14-Matrix) | — (C1 entfaellt erwartet) |
| 4 | Performance-Benchmark | Pending | TBD (entsteht in Welle-4-C0) | `GG-RT-001..005` (10 000-Points/s-Bench + Tick-Drift-Schranken) | TBD (ggf. ADR 0041 Bench-Pattern) |
| 5 | Security-Audit + Eingabevalidierung | Pending | TBD (entsteht in Welle-5-C0) | `GG-SAFE-001..008` | TBD |
| 6 | Deploy-Hardening + IEC-Smoke-Pfad-B | Pending | TBD (entsteht in Welle-6-C0) | `GG-DEPLOY-*` + Trigger 009 (IEC-Reaktivierung; M4-Erbschaft); ggf. eigener Sub-Slice 6a/6b | TBD |
| 7 | M6-Closure | Pending | TBD (entsteht in Welle-7-C0) | M6-Closure (`done/M6-results.md` + S-1..S-6) | alle M6-ADRs → `Accepted` |

**Naechster aktiver Slice:** Welle 0 (Slice-Plan-Eroeffnung
+ Trigger-Triage) — siehe [`M6-welle-0.md`](M6-welle-0.md).
Welle-1+-Aktivierung erfolgt mit Welle-0-Closure (C2-
Sync).

### 3.2 Pending-Wellen-Plan-Items

Vorbelegung pro Welle (Welle-X-C0 schaerft + entscheidet
final):

**Welle 1 — Base-Image-Bump (krb5-CVE-Aufloesung):**

- `Trigger-Gated → Active` per [`carveouts.md §2.2`](carveouts.md):
  Trigger 010 (M4-Erbschaft).
- Lieferziel: Dockerfile `FROM`-Update auf neueste
  Debian-13-Variante mit krb5-Fix; `make fullbuild`
  cache-frei gruen.
- Optional: CI-Pflicht-Gate fuer `make fullbuild` (`GG-
  DEPLOY-*`-Anteil).
- ADR-Lifecycle: ggf. ADR 0043 (Image-Audit-Strategie)
  falls die Audit-Pflicht-Schwelle re-evaluiert werden
  muss.

**Welle 2 — SBOM-Aktivierung + Release-Workflow:**

- `Trigger-Gated → Active` per [`carveouts.md §2.5`](carveouts.md):
  Trigger 008.
- Lieferziel: `make sbom` scharfgeschaltet (`syft`/
  `cyclonedx` — siehe ADR 0042); CI-Hook im Release-Workflow
  (`GG-CICD-007`); Release-Pipeline-Sanity gegen Tag-Push.
- ADR-Lifecycle: NEU ADR 0042 (SBOM-Tool-Wahl) + CI-Hook-
  Pattern.

**Welle 3 — CI/CD-Vollausbau:**

- Lieferziel:
  - `make test-unit` + `make test-integration` als
    GitHub-Actions-Jobs (`GG-CICD-002`).
  - `make coverage-gate` + `make coverage-gate-critical`
    als CI-Jobs (`GG-CICD-003`).
  - `make dep-audit` als CI-Job (`GG-CICD-006`).
  - **NEU Python-3.13+3.14-Matrix** (Spike-0-Closure-D-8
    + ADR 0002 §6.1).
  - **NEU `GG-CICD-007` Release-Workflow** (verlinkt
    Welle-2-SBOM-Hook).
- Plus opportunistisch: **URL-Versionierung `/api/v1`-
  Mount-Prefix** (`carveouts.md §2.1 Deferred`-Item)
  proaktiv, vor naechster URL-Kollision.
- ADR-Lifecycle: C1 entfaellt erwartet (Slice-025-
  Erweiterung; bestehende GitHub-Actions-Konfiguration
  geschaerft).

**Welle 4 — Performance-Benchmark:**

- Lieferziel: `make perf`-Target + `GG-RT-005`-Benchmark
  (10 000 Points/s) + Tick-Drift-Schranken (`GG-RT-001..004`).
- Bench-Framework: Vorbelegung pytest-benchmark per
  [`M6-welle-0.md §3 M6-D-7`](M6-welle-0.md); Welle-4-C1-
  ADR entscheidet final.
- Regression-Gate: Bench-Resultate gegen Baseline pinned;
  CI-Hook (oder lokaler Pflicht-Pfad) gegen Drift.
- Carveout-Aufloesung opportunistisch: **Snapshot-
  Envelope-v2-Body-Serialisierung** falls Performance-Bench
  die Stub-Surface ohnehin anfasst.
- ADR-Lifecycle: NEU ADR 0041 (Performance-Bench-Pattern).

**Welle 5 — Security-Audit + Eingabevalidierung:**

- Lieferziel:
  - `GG-SAFE-001..007`: Audit-Familie (Logging-Hygiene,
    Secret-Handling, Audit-Trail-Integritaet).
  - **`GG-SAFE-008`** externe Eingabevalidierung an
    REST/WebSocket/Adapter-Schnittstellen produktiv
    verankert (Pydantic-Strict-Mode oder explizite
    Validation-Layer; ADR-pflichtig).
  - IP-/Netz-Beschraenkung im Demo-Compose dokumentiert
    + ggf. Hardening (separate Auflagen-Schicht; kein
    einzelner `GG-SAFE-*`-ID).
- Carveout-Aufloesung opportunistisch: **Welle-3-Pre-init-
  Defense-Pattern verallgemeinern** (`carveouts.md §2.1
  Pattern-Forward`) — falls neue Adapter-Surfaces in M6
  hinzukommen.
- ADR-Lifecycle: ggf. ADR fuer Eingabe-Validation-Pattern.

**Welle 6 — Deploy-Hardening + IEC-Smoke-Pfad-B:**

- Lieferziel:
  - `GG-DEPLOY-*`-Vollausbau: Image-Audit (`make image-
    audit`) als CI-Pflicht-Gate; Container-Smoke-Test
    (`make runtime` pollt `/health`); Healthcheck-Pollung-
    Pattern.
  - **Trigger 009 IEC-Smoke-Reaktivierung Pfad-B** (M4-
    Erbschaft): Multi-Python-Test-Stage in Dockerfile;
    IEC-In-Process-Smoke unter Python 3.12 reaktiviert;
    Test-`pytest.mark.skip` aufgehoben. **Repo-Novum-
    Material** — ggf. eigener Sub-Slice 6a/6b je
    Komplexitaet.
- ADR-Lifecycle: ggf. ADR fuer Multi-Python-Test-Stage-
  Konvention.

**Welle 7 — Closure:**

- Alle M6-ADRs (0041/0042/0043 etc.) auf `Accepted`.
- NEU `done/M6-results.md` mit Detail-Welle-Tabelle +
  Abnahme-Belege + Pro-Welle-Reviews + S-1..S-6-Sweep +
  Wandert-Nach (Pattern analog
  [`../done/M5-results.md`](../done/M5-results.md) +
  [`../done/M4-results.md`](../done/M4-results.md)).
- `roadmap.md §3 M6` DoD-Checkboxen alle `[x]`; M6 auf
  `Done`; „Naechster aktiver Slice: M7" (oder
  „Projekt-Closure" falls kein M7 vorgesehen).
- Top-Level-Doku-Sync (`README.md` / `README.de.md` /
  `AGENTS.md` / Status-Header).
- Self-Close-Move `M6-perf-security-cicd.md → done/`
  (rename-only).
- Bezug-Linkpflege an M6-ADRs (ADR 0028).
- **M6-Welle-7-End-to-End-Sweep S-1..S-6:**
  - **S-1** M6-Vorabraeumungs-Item: Welle-0-Trigger-Triage
    + Welle-7-Sweep der in M6 dazu-gekommenen Trigger.
  - **S-2** Sub-Slicing-Schwelle eingehalten ueber Welle
    1..6; Beleg-Tabelle.
  - **S-3** Default-`make gates` ohne `CRITICAL_COV_TARGETS`-
    Override cache-frei gruen am Welle-7-Closure-Hash.
  - **S-4** `make image-audit` cache-frei gruen
    (`GG-DEPLOY-*`-Pflicht; Trigger 010 in Welle 1 +
    Welle-6-Image-Audit-CI-Gate aufgeloest).
  - **S-5** ADR-Erweiterungs-Pattern fortgefuehrt
    (geplante ADR-Anzahl in M6: 1-3 ohne Supersedes per
    ADR 0011).
  - **S-6** Lastenheft-Coverage-Sweep nach M6-Closure
    (Projekt-Closure-Trigger erstellen, falls kein M7).

---

## 4. Out-of-Scope (bleibt fuer M7+ oder permanent)

Aus [`carveouts.md §2.7`](carveouts.md) (Permanent
`Out-of-Scope`):

- **Produktive Anlagensteuerung** (Lastenheft Z. 1161–1163)
  — strukturell ausgeschlossen.
- **Multi-User + Auth im UI-Layer** — IP-/Netz-Beschraenkung
  im Demo-Compose ist die einzige verlangte Schicht
  (separate Auflage; kein `GG-SAFE-*`-ID).
- **SvelteKit-SPA / React-SPA-Migration** — ADR 0036 §2.5
  Migrations-Pfad nur bei Stakeholder-Druck.
- **Plotly.js / ECharts** — ADR 0036 §2.5 + Welle-6b
  Decision 23 nur bei Chart.js-Limitationen.
- **Inline-SVG-Anlagenschaltbild** — voller Schaltplan
  ist M7+/Welle-Polish-Material.
- **End-User-Tutorial / Onboarding-Doku** — separater
  Slice-Trigger; kein M6-Lieferpunkt.

Aus M5-Welle-7-Erbschaft, **bedingt** in M7+ oder offen:

- **Inline-SVG-Geraete-Grafik** — ist M6-Welle-X moeglich,
  aber falls UI-Polish-Druck fehlt → M7+.
- **WebSocket-Live-Stream `/devices`** — gleiches Argument;
  M6 falls UI-Druck, sonst M7+.
- **Dynamische Fault-Activation ueber `POST /faults`** — M6
  falls Fault-Pipeline-Erweiterung in M6 substantiell
  wird, sonst M7+.
- **CSV/JSONL-Export** — `GG-ACCEPT-003`-Material; M6 oder
  M7+ je nach Stakeholder-Bedarf.

**Trigger-Gated weiter offen** (4 Tooling + 9 SOLLTE-
Geraete + 1 RL + 1 BESS-Spike = 15 Items; siehe
[`carveouts.md §2.3..§2.6`](carveouts.md)): warten auf
externen Anlass; **nicht M6-Scope** ohne explizite
Aktivierung.

---

## 5. Risiken und Fallback

- **Performance-Bench-Methodologie unklar** — `GG-RT-005`
  ist eine harte Lastenheft-Schranke ohne dokumentierte
  Methodologie. **Mitigation:** Welle-4-C1-ADR 0041
  fixiert Bench-Framework + Mess-Pattern; ggf. Pre-C0c-
  Smoke-Probe analog M5-Welle-1 `9c20dad`.

- **CI-Erweiterung-Komplexitaet** — 4 neue CI-Jobs +
  Python-3.13/3.14-Matrix beruehren Slice-025-Konfiguration.
  Risiko: GitHub-Actions-Workflow-Drift. **Mitigation:**
  Welle-3-C2 macht alle Jobs in einem Commit (analog
  Slice 025); Local-CI-Parity-Test als Validierung.

- **IEC-Smoke-Pfad-B-Scope** — Multi-Python-Test-Stage
  ist Repo-Novum (Dockerfile + Test-Matrix). Risiko:
  Welle-6-Komplexitaet > Schwelle. **Mitigation:** ggf.
  Sub-Slicing 6a (Multi-Python-Stage) + 6b (IEC-Smoke-
  Aktivierung); Welle-6-C0-Sub-Slicing-Beschluss.

- **krb5-Bump-Side-Effects** — Base-Image-Bump in Welle 1
  kann ungeplante Library-Drifts ausloesen (Debian-13-
  Bibliotheks-Versionen). Risiko: alte Tests brechen.
  **Mitigation:** Welle-1-C2 macht `make gates` cache-
  frei gruen vor Push; ggf. Pinning auf konkrete
  Debian-Punktversion.

- **`GG-SAFE-008`-Pydantic-Strict-Mode-Schaerfung** — kann
  bestehende Welle-1-Schemas brechen, falls dort
  implizite Coercion verlangt war. Risiko: API-Surface-
  Drift. **Mitigation:** Welle-5-Pre-C0c-Smoke-Probe gegen
  alle 9 HTTP-/WS-Endpunkte + Welle-5-C1-ADR fuer
  Validation-Strategie.

- **ADR-Anzahl-Drift** — Soll-Wert 1-3 ADRs (per ADR 0011);
  bei 3 ADRs (Bench + SBOM + Image-Audit) ist die Schwelle
  erreicht. Risiko: zusaetzliche ADR-Pflicht in Welle 5+/6.
  **Mitigation:** ADR-Buendelung wo moeglich; ADR-0028-
  Schaerfung-ohne-Supersede pflegen.

---

## 6. Wandert nach

- Bei M6-Welle-7-Closure: `M6-perf-security-cicd.md`
  Self-Close-Move nach `done/` (Pattern analog
  `M5-ui-demo.md` in M5-Welle-7-C4a `667be09`).
- `done/M6-results.md` entsteht in M6-Welle-7-C2 als
  Closure-Artefakt (Pattern analog `done/M5-results.md`
  + `done/M4-results.md`).
- Aktive Welle wechselt nach M6-Closure auf **M7** (falls
  vorgesehen) oder auf **Projekt-Closure-Slice**.

---

## 7. Verifikationspfad

**Welle-7-Gate:**

- `make gates` cache-frei gruen ohne Override am M6-
  Welle-7-Closure-Hash (alle A-1-Gates inkl. ggf. neuer
  Welle-X-Gates).
- `make fullbuild` cache-frei gruen (Trigger 010 in Welle
  1 aufgeloest; **Erbschafts-Loesung** des M3-Welle-7-
  pre-existing-Drifts).
- `make docs-check` cache-frei gruen.
- **NEU CI-Pflicht-Gates** (Welle 3): test-unit +
  coverage + dep-audit + image-audit als CI-Jobs.
- **NEU Performance-Regression-Gate** (Welle 4): `make
  perf` reproduzierbar; Bench-Resultate gegen Baseline
  pinned.

**Abnahme-Verifikation (Lastenheft):**

- `GG-RT-001..005` (5 IDs) ✓ in M6-Welle-4.
- `GG-SAFE-001..008` (8 IDs) ✓ in M6-Welle-5.
- `GG-CICD-001..007` (7 IDs) ✓ in M6-Welle-3 + Welle-2
  (Release-Workflow + SBOM).
- `GG-DEPLOY-001..00X` (≥X IDs) ✓ in M6-Welle-6 +
  Welle-1 (Image-Audit + krb5-Bump).

**Test-Bilanz-Erwartung** (Welle-7-Closure-Snapshot):

- Unit-Tests: 1722 → ~1750 (kleine Bench/Security-Test-
  Erweiterungen; Welle 3 fuegt CI-Job-Skripte hinzu, keine
  neuen Unit-Tests; Welle 4 ggf. NEU `tests/perf/`).
- Integration-Tests: 80 → ~85 (Welle 2 SBOM-Smoke +
  Welle 4 Perf-Smoke + Welle 6 IEC-Reaktivierung +4
  skipped → 0 skipped).
- Welle-Closure-Hash-Snapshot wird pro Welle in
  `done/M6-welle-*.md §10` und in `done/M6-results.md §1
  Welle-Tabelle` festgehalten.
