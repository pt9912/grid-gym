# Slice-Plan — M6 Performance + Security + CI/CD-Haertung — In Progress

**Status:** In Progress — eroeffnet 2026-06-04 mit M6-Welle-0-
C1 `e050035`. **M6-Welle-0** (Slice-Plan-Eroeffnung +
Trigger-Triage) **abgeschlossen 2026-06-04** mit Stack
`282a8cb..960f6ed` (siehe
[`../done/M6-welle-0.md`](../done/M6-welle-0.md)).
**M6-Welle-1** (Base-Image-Bump / krb5-CVE-Aufloesung,
Trigger 010 M4-Erbschaft) **abgeschlossen 2026-06-05** mit
Stack `4b1b3e9..4517614` (Trigger-010-Aufloesung ohne Code-
Edit durch Debian-13.5-Upstream-Drift + Trigger-015-Pattern;
NEU ADR 0043 `Provisional`; Welle-1-D-1 vertagt auf Welle 3
ueber NEU Trigger 031).
**M6-Welle-2** (SBOM-Aktivierung + Release-Workflow; Trigger
008 + `GG-CICD-007`) **abgeschlossen 2026-06-05** mit Stack
`0cc28f3..b41b7fc` (NEU `.github/workflows/release.yml` mit
3 Jobs + 6 publizierten Artefakten; NEU ADR 0042
`Provisional`; Trigger 008 nach `done/` gewandert; siehe
[`../done/M6-welle-2.md`](../done/M6-welle-2.md)).
**M6-Welle-3** (CI/CD-Vollausbau; `GG-CICD-002/003/005/
006` + Python-3.13/3.14-Matrix + Trigger 031-Aufloesung)
**abgeschlossen 2026-06-05** mit Stack `08a8034..c36f734`
(C0 + C2 `ce13253` + C3 dieser Commit; C1 entfaellt;
Self-Close-Move-Folge C4a/C4b ausstehend als Welle-4-Pre-
C0a/Pre-C0b): NEU 4 Workflows (`tests.yml`/`coverage.yml`/
`dep-audit.yml`/`fullbuild.yml`) mit Python-3.13/3.14-
Matrix in tests.yml; Trigger 031 aufgeloest. Plus
pip-PYSEC-2026-196-Drift im uv.lock behoben (`pip 26.1.1
→ 26.1.2`).
**M6-Welle-4a** (Generated-Trivyignore-Permit; ADR-0011-
Schaerfung an ADR-0043 §2.2 + vulnignore-Pattern-Import aus
m-trace; Welle-3-Post-Closure-Folge fuer Trigger 033 / OTel-
Collector-CVE-2026-42504-Temp-Deferral) **abgeschlossen
2026-06-06** mit Stack `9bb6a92..789ac50` (C0 + C1 `94dff9e`
ADR-0044 `Provisional` + C2 `8fbd17c` Pattern-Import + C3
`f19837f` Closure-Sync + Post-Push-CI-Fix `f46e789`
simulation-Healthcheck Always-Healthy + C4a `3bc58b8` Self-
Close-Move + C4b `789ac50` Cross-Doc-Refs-Sync).
`make fullbuild` cache-frei gruen lokal UND CI-Sensor (Lauf
27055273876) — erstmalig seit `fullbuild.yml`-Anlage in
M6-Welle-3-C2. Welle-4-Sub-Slicing-Beschluss (4a Vulnignore +
4b Performance-Bench) per Welle-4a-D-1.
**Aktive Welle: M6-Welle-5b** (Sim/Prod-Marker + Input-
Validation; `GG-SAFE-007/008` MUSS) **In Progress 2026-06-07**
mit C0 `0d3bb61` (Slice-Doc-Anlage; siehe
[`M6-welle-5b.md`](M6-welle-5b.md)); Welle-5b-Decisions D-1..D-6
final (Audit-Form Doku+Smokes / **drei Pflicht-Marker-Surfaces
UI + API-Doku + Adapterkonfiguration** plus arch_check / Hybrid-
Luecken-Adressierung / DriveSide+DrivenSide-Audit / Per-Endpoint-
Strict-Mode mit Request-Default / **NEU Schaerfungs-ADR 0045 mit
Bezug auf ADR 0037, ADR 0037 unveraendert `Accepted`**). **C1
ist Pflicht-Commit vor C2** (D-5 hat Default-Pydantic-Mode als
Lücke verbindlich gemacht); C2/C3 + Self-Close-Folge C4a/C4b
ausstehend. **M6-Welle-5a
abgeschlossen 2026-06-06** mit Stack `4b36185..52cb698`
(C0 `4b36185` Slice-Doc + C2 `4c1a693` Quality-Pipeline-
Audit-Substanz + C2-Review-Folge `52cb698` 6 Self-Review-
Findings adressiert); 4 Pflicht-Smokes + 2 Schwester + 2
Skip-mit-Trigger-Pointer = 7 NEU Integration-Tests; 2 NEU
`open/`-Triggers 034 (`GG-SAFE-004` `max_age`-Lücke) + 035
(`GG-SAFE-003` partial Lücke); `docs/user/safe-001-004-
quality-pipeline.md` Audit-Tabelle mit ehrlichem Status.
**Welle-4-Subdivision komplett abgeschlossen 2026-06-06**:
4a Vulnignore-Pattern (Stack `9bb6a92..789ac50`) + 4b-a
Bench-Foundation (`f2fbcc0..76a2f40`) + 4b-b GG-RT-005-
Telemetry-Bench (`beb5dee..c8625f7`) + 4b-c GG-RT-001-
Backpressure-Healthcheck (`c5543fd..7001989`).
**M6-Welle-4b-a abgeschlossen 2026-06-06** mit Stack `f2fbcc0..
76a2f40` + **M6-Welle-4b-b abgeschlossen 2026-06-06** mit
Stack `beb5dee..c8625f7` (plus Post-C3-Review-Folge `1b77665`:
7 Self-Review-Findings adressiert, F1 HIGH ADR-0041-§2.2-
Vertragsbruch betrifft auch Welle-4b-a-Baseline rueckwirkend);
NEU `tests/perf/test_telemetry_port_bench.py` + Baseline mit
ADR-konformer Konfig; `GG-RT-005`-Doppel-Akzeptanz produktiv
(Payload ≤ 256 Byte UND ~1.17M Publish-OPS lokal weit ueber
10 000-SOLLTE-Schwelle).

**Datum:** 2026-06-04 (in `in-progress/` direkt eroeffnet
ohne `next/`-Zwischenschritt; Welle-0-Doc-Hoheit fuer den
Hintergrund liegt in [`M6-welle-0.md`](../done/M6-welle-0.md) §1).

**Bezug:**

- [`roadmap.md`](roadmap.md) §3 M6 (Lieferziel, DoD-
  Checkliste, Architekturartefakte).
- [`carveouts.md`](carveouts.md) (Cross-Meilenstein-
  Carveout-Index; M6-Welle-0-C2-Triage ist die primaere
  Pflege-Welle).
- M5-Closure-Notiz
  [`../done/M5-results.md`](../done/M5-results.md) §5
  „Welle-7-Erbschaft fuer M6+".
- [`M6-welle-0.md`](../done/M6-welle-0.md) §3 Decision-Liste
  (7 offene Decisions fuer Welle 1+).
- [`../../adr/0030-device-protocol-port-surface.md`](../../adr/0030-device-protocol-port-surface.md)
  + M4-/M5-ADRs (0030..0040) — M6 baut auf der voll-
  ausgereiften Adapter- + Driving-Surface auf, ohne neuen
  Driving-Port einzuziehen.
- [`../../../../spec/lastenheft.md`](../../../../spec/lastenheft.md)
  Kap. 7 (`GG-RT-001..005`; `GG-RT-006` Replay-Zeit-
  multiplikator gehoert zu M3, nicht M6) + Kap. 20
  (`GG-SAFE-001..008`) + Kap. 22 (`GG-CICD-001..007` inkl.
  `GG-CICD-007` Release-Workflow mit SBOM-Hook ueber
  Trigger 008) + Kap. 23 (`GG-DEPLOY-001..011`). **Keine
  eigene `GG-SBOM-*`-Lastenheft-Familie** — SBOM ist ueber
  `GG-CICD-007` verankert.

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

- **Lastenheft-Coverage** (MUSS/SOLLTE/KANN gem.
  Lastenheft-Normativ-Sprache; M6-Lieferziel umfasst alle
  drei Klassen, nicht nur MUSS):
  - **MUSS-IDs** (20): `GG-RT-001/002/003` (3; `GG-RT-006`
    ist M3-Scope `GG-AR-COMP-REPLAY`),
    `GG-SAFE-001/002/003/004/007/008` (6),
    `GG-CICD-001/002/003/005/006` (5),
    `GG-DEPLOY-001/002/003/005/006/011` (6).
  - **SOLLTE-IDs** (10): `GG-RT-004/005` (2) inkl.
    10 000-Points/s-Benchmark (`GG-RT-005` ist `SOLLTE`,
    nicht `MUSS`), `GG-SAFE-005/006` (2), `GG-CICD-004/007`
    (2; CI-Coverage-Gate + SBOM-Release-Workflow),
    `GG-DEPLOY-004/007/008/010` (4).
  - **KANN-IDs** (1): `GG-DEPLOY-009`.
  - **Klassen-Quelle:** Lastenheft-Kap. 7/20/22/23. Welle-
    X-C0 prueft die exakte Klassen-Zuordnung pro Welle und
    setzt DoD analog (MUSS = harte DoD, SOLLTE = DoD mit
    Begruendung wenn nicht erfuellt, KANN = optionale
    Erweiterung).
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
  - **3 M6-ADRs vorbelegt** (M6-Welle-0-D-4: ADR 0041 Bench
    + ADR 0042 SBOM + ggf. ADR 0043 Image-Audit). Die
    empirische M3/M4/M5-Spannweite liegt mit 5-6 ADRs pro
    Meilenstein deutlich hoeher (M3 = 6 ADRs 0022..0027;
    M4 = 6 ADRs 0030..0035; M5 = 5 ADRs 0036..0040; Quelle:
    `done/M{3,4,5}-results.md`). Die M6-Vorbelegung von 3
    ist also bewusst konservativ; tatsaechliche Anzahl
    haengt vom Welle-X-C0-Schaerfen ab. **Kein normativer
    Soll-Wert** — ADR 0011 definiert das Schaerfung-ohne-
    Supersedes-Pattern, nicht eine ADR-Mengenschwelle.
  - Vorbelegung in [`M6-welle-0.md §3 M6-D-4`](../done/M6-welle-0.md):
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
[`M6-welle-0.md §3 M6-D-1`](../done/M6-welle-0.md) — pro Triggerebene
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
| 0 | Slice-Plan-Eroeffnung + Trigger-Triage | Done 2026-06-04 | [`M6-welle-0.md`](../done/M6-welle-0.md) | Plan-Welle (7 Decisions vorbelegt) | — (kein C1) |
| 1 | Base-Image-Bump (krb5-CVE-Aufloesung) | Done 2026-06-05 | [`M6-welle-1.md`](../done/M6-welle-1.md) | Trigger 010 + `make fullbuild`-Defer-Aufloesung (Null-Code-Edit; Upstream-Drift) | NEU ADR 0043 `Provisional` (Image-Audit-Strategie; Welle-1-C1 `c44e6d5`) |
| 2 | SBOM-Aktivierung + Release-Workflow | Done 2026-06-05 | [`M6-welle-2.md`](../done/M6-welle-2.md) | `GG-CICD-007` (5 Asset-Klassen + 1 GHCR-Push) + Trigger 008 | NEU ADR 0042 `Provisional` (SBOM-Tool + Release-Pattern; Welle-2-C1 `4b1062b`) |
| 3 | CI/CD-Vollausbau | Done 2026-06-05 | [`M6-welle-3.md`](../done/M6-welle-3.md) | `GG-CICD-002/003/005/006` + Python-3.13/3.14-Matrix + Trigger 031 (`make fullbuild`-CI-Gate; Welle-1-D-1-Vertagung) **aufgeloest** | — (C1 entfaellt; Pattern analog M5-Welle-2) |
| 4a | Generated-Trivyignore-Permit (vulnignore-Pattern + ADR-0044) | Done 2026-06-06 | [`M6-welle-4a.md`](../done/M6-welle-4a.md) | Trigger 033 Temp-Deferral (OTel-Collector CVE-2026-42504) **aktiv** seit C2 `8fbd17c`; ADR-0044 als ADR-0011-Schaerfung an ADR-0043 §2.2 | NEU ADR 0044 `Provisional` (Generated-Trivyignore-Permit; Welle-4a-C1 `94dff9e`) |
| 4b-a | Performance-Bench-Foundation (`GG-RT-004` + ADR-0041) | Done 2026-06-06 | [`M6-welle-4b-a.md`](../done/M6-welle-4b-a.md) | `GG-RT-004` SOLLTE (100 Geraete × 10 000 Ticks ohne verlorene Events UND ohne Replay-Diff) **produktiv**; plus `GG-RT-002` + `GG-RT-003` DoD-Bestaetigung; Bench-Pattern-Foundation (pytest-benchmark + `make perf` + Baseline-Pinning) | NEU ADR 0041 `Provisional` (Performance-Bench-Pattern; Welle-4b-a-C1 `43569d2`) |
| 4b-b | `GG-RT-005` Telemetry-Port-Bench | Done 2026-06-06 | [`M6-welle-4b-b.md`](../done/M6-welle-4b-b.md) | `GG-RT-005` SOLLTE **produktiv** (10 000 Points/s am Telemetry-Port mit Payloads ≤ 256 Byte; lokal ~788k Publish-OPS) | — (C1 entfaellt; Welle-4b-b-D-4 schliesst ADR-0041-Schaerfung negativ aus) |
| 4b-c | `GG-RT-001` Backpressure-Healthcheck | Done 2026-06-06 | [`M6-welle-4b-c.md`](../done/M6-welle-4b-c.md) | `GG-RT-001` MUSS **produktiv** (Tick-Dauer/p95-Jitter/missed-Ticks/Backpressure-Status-Healthcheck via NEU Adapter-Side `_tick_loop_healthcheck.py` + `GET /runs/{id}/healthcheck`-Endpoint) | — (C1 entfaellt; Welle-4b-c-D-6 schliesst ADR-Schaerfungs-Bedarf negativ aus) |
| 5a | Quality-Pipeline-Audit (`GG-SAFE-001..004` MUSS) | **Done 2026-06-06** (`4b36185..52cb698`) | [`M6-welle-5a.md`](../done/M6-welle-5a.md) | `GG-SAFE-001` (invalid-Erkennung ✓ produktiv) + `002` (NaN-Reject ✓ produktiv) + `003` (Kommunikationsausfall ⚠ partial Lücke → Trigger 035) + `004` (max_age ✗ Lücke → Trigger 034) — Audit + 7 Smokes + Doku-Tabelle | — (C1 entfaellt; Welle-5a-D-5 schliesst ADR-Bedarf negativ aus) |
| 5b | Sim/Prod-Marker + Input-Validation (`GG-SAFE-007/008` MUSS) | **In Progress 2026-06-07** (C0 `0d3bb61`) | [`M6-welle-5b.md`](M6-welle-5b.md) | `GG-SAFE-007` (Sim/Prod-Trennung an drei Pflicht-Surfaces UI + API-Doku + **Adapterkonfiguration**; Welle-5b-D-2 Option B: OpenAPI + README + UI-Dashboard + Scenario-YAML + Protocol-Adapter-Config-Module + arch_check) + `008` (REST/WS/Adapter-Input-Validation-Audit; Welle-5b-D-4 Option B DriveSide+DrivenSide; Welle-5b-D-5 Per-Endpoint-Strict-Mode mit Request-Body-Default) | **NEU ADR 0045** `Proposed` in C1 → `Provisional` in C3 (Schaerfungs-ADR mit Bezug auf ADR 0037 per ADR-0011-Pattern; ADR 0037 unveraendert `Accepted`; Welle-5b-D-6 Option C verbindlich) |
| 5c | SOLLTE-Items + IP/Netz (`GG-SAFE-005/006` + Demo-Compose) | Pending | TBD (entsteht in Welle-5c-C0) | `GG-SAFE-005` (Fallback-Zustaende) + `006` (Non-Determinism-Detection) + IP-/Netz-Beschraenkung Demo-Compose | TBD |
| 6 | Deploy-Hardening + IEC-Smoke-Pfad-B | Pending | TBD (entsteht in Welle-6-C0) | `GG-DEPLOY-001..011` (6 MUSS + 4 SOLLTE + 1 KANN) + Trigger 009 (IEC-Reaktivierung; M4-Erbschaft); ggf. eigener Sub-Slice 6a/6b | TBD |
| 7 | M6-Closure | Pending | TBD (entsteht in Welle-7-C0) | M6-Closure (`done/M6-results.md` + S-1..S-6) | alle M6-ADRs → `Accepted` |

**Aktiver Slice:** M6-Welle-5 (Security-Audit +
Eingabevalidierung; `GG-SAFE-001..008` MUSS/SOLLTE) — Welle-
5-Slice-Doc entsteht in Welle-5-C0. **M6-Welle-4b-c
abgeschlossen 2026-06-06** mit Stack `c5543fd..7001989` (C0 + C0-
Review-Folge `aacc370` + C2 `a98f967` + C2-Review-Folge
`8785a6b`): NEU Driving-Adapter-Side
`TickLoopHealthcheckAdapter` + Driver-Hook (`time.perf_counter
()`-Mess via try/finally) + NEU `GET /runs/{id}/healthcheck`-
Endpoint + 14 Unit-Tests + 3 Integration-Smokes; `GG-RT-001`
MUSS-Akzeptanz produktiv (Tick-Dauer/p95-Jitter/missed-Ticks/
Backpressure-Status fuer 10ms-Modus). **Welle-4-Subdivision
komplett**: 4a + 4b-a/b/c alle abgeschlossen.
**M6-Welle-4b-a abgeschlossen 2026-06-06** mit Stack
`f2fbcc0..76a2f40` (C0 + C1 `43569d2` + Review-Folge `f4f4983`
+ C2 `5d8c497` + C3 dieser Commit): NEU ADR-0041 `Provisional`
(Performance-Bench-Pattern + Regression-Schwelle); NEU
pytest-benchmark als opt-in-Extra; NEU tests/perf/ Layer +
Dockerfile-perf-Stage + Makefile-Targets; `GG-RT-004`-Doppel-
Akzeptanz produktiv (Maintainer-Dev-Host-Baseline 519ms /
1.92 OPS).
**M6-Welle-4a abgeschlossen 2026-06-06** mit Stack
`9bb6a92..789ac50` (C0 + C1 `94dff9e` + C2 `8fbd17c` + C3
`f19837f` + Post-Push-CI-Fix `f46e789` + C4a `3bc58b8` +
C4b `789ac50`): NEU ADR-0044 `Provisional` (Generated-
Trivyignore-Permit; ADR-0011-Schaerfung an ADR-0043 §2.2);
NEU `tools/render_trivyignore.py` + `deploy/security/
vulnignore.yaml` mit CVE-2026-42504-Eintrag; Makefile-
Integration mit `render-trivyignore`-Target und `image-
audit`-`--ignorefile`-Erweiterung. `make fullbuild` cache-
frei gruen lokal UND CI-Sensor (Lauf 27055273876) —
erstmalig seit `fullbuild.yml`-Anlage in M6-Welle-3-C2.
Trigger 033 bleibt OFFEN als Stable-Watch (Temp-Deferral
via vulnignore-Pattern; echte Aufloesung weiter bei OTel-
Stable-Release 0.154.0+).
**M6-Welle-3 abgeschlossen 2026-06-05** mit Stack
`08a8034..c36f734` (C0 + C2 `ce13253` + C3 `c8ecbe4` +
C3-Review-Folge `affdff7` + C4a `3b6d9bf` + C4b `c36f734`;
C1
entfaellt analog M5-Welle-2; siehe
[`M6-welle-3.md`](../done/M6-welle-3.md); Self-Close-Move-Folge
C4a/C4b ausstehend als Welle-4-Pre-C0a/Pre-C0b): NEU 4
GitHub-Actions-Workflows (`tests.yml`/`coverage.yml`/`dep-
audit.yml`/`fullbuild.yml`); Python-3.13/3.14-Matrix in
`tests.yml` (test-unit-Job; test-integration Default per
Welle-3-D-2); Trigger 031 (`make fullbuild`-CI-Gate aus
Welle-1-D-1-Vertagung) aufgeloest. **M6-Welle-2 abgeschlossen
2026-06-05** mit Stack `0cc28f3..b41b7fc` (siehe
[`M6-welle-2.md`](../done/M6-welle-2.md); Self-Close-Move-Folge
Stack umfasst C0/2 Review-Folgen/C1/C2/C3/C3-Sensor-
Erweiterung + C4a `c51d905` Self-Close-Move + C4b `b41b7fc`
Cross-Doc-Refs-Sync):
**Trigger-008-Aufloesung** durch C2 `235395e` (NEU
`.github/workflows/release.yml` mit Tag-Push + workflow_
dispatch + 3 Jobs + 1 GHCR-Push + 5 Release-Asset-Files;
Makefile `make sbom`-Scan-Ziel von Source-Tree auf
Runtime-Image umgestellt; Dockerfile test-unit/coverage-
gate-Stages fuer JUnit-XML + HTML-Coverage geschaerft);
NEU ADR 0042 `Provisional` (SBOM-Tool + Release-Pattern;
Accept in M6-Welle-7-Closure-C1 gebuendelt mit ADR 0041 +
ADR 0043). M6-Welle-1 abgeschlossen 2026-06-05 mit Stack
`4b1b3e9..d51d6e7` (siehe
[`M6-welle-1.md`](../done/M6-welle-1.md); Stack umfasst
C0/C0-Review-Folgen/C1/C2/C3/C3-Review-Folge + C4a `1fbd0ac`
Self-Close-Move + C4b `d51d6e7` Cross-Doc-Refs-Sync): **Trigger-010-Aufloesung ohne Code-
Edit** durch Upstream-Patch-Drift (Debian-13.5 +
Trigger-015-Pattern). Welle-1-D-1 (CI-Pflicht-Gate fuer
`make fullbuild`) auf M6-Welle-3 vertagt ueber NEU
[`../done/031-ci-make-fullbuild-gate.md`](../done/031-ci-make-fullbuild-gate.md).
NEU ADR 0043 `Provisional` (Image-Audit-Strategie + Trivy-
Defer-Aufloesungs-Pattern); `Accepted` in M6-Welle-7-
Closure-C1 gebuendelt mit ADR 0041 + ADR 0042. M6-Welle-0
abgeschlossen 2026-06-04 mit Stack `282a8cb..960f6ed`
(siehe [`../done/M6-welle-0.md`](../done/M6-welle-0.md)).

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

**Welle 4 — Sub-Slicing 4a/4b** (Welle-4a-D-1 in
[`M6-welle-4a.md §3`](../done/M6-welle-4a.md)):

**Welle 4a — Generated-Trivyignore-Permit (Welle-3-Post-
Closure-Folge):**

- Trigger: Welle-3-Post-Closure-Substanz (`done/M6-welle-3.md
  §10`); Trigger 033 (OTel-Collector Go-stdlib CVE-2026-
  42504) macht `make fullbuild` in `main` rot.
- Lieferziel: NEU ADR-0044 (Generated-Trivyignore-Permit;
  ADR-0011-Schaerfung an ADR-0043 §2.2) + NEU
  `deploy/security/vulnignore.yaml` + NEU `tools/render-
  trivyignore.sh` (m-trace-Pattern-Import) +
  `Makefile`-Integration. `make fullbuild` cache-frei gruen
  ohne OTel-Stable-Release abwarten zu muessen.
- Anti-Scope: Kein OTel-Collector-Image-Bump (Trigger 033
  bleibt offen als Stable-Watch); keine permanente Defer-
  Form (`expires`-Pflicht; m-trace-Pattern-Vorbild).
- ADR-Lifecycle: NEU ADR-0044 `Provisional` in Welle-4a-C1;
  `Accepted` in M6-Welle-7-Closure-C1 gebuendelt mit ADR
  0041 + ADR 0042 + ADR 0043.

**Welle 4b — Sub-Slicing 4b-a/4b-b/4b-c** (Welle-4b-a-D-1
in [`M6-welle-4b-a.md §3`](../done/M6-welle-4b-a.md); Pattern analog
M5-Welle-6 Sub-Slicing 6a/6b/6c):

**Welle 4b-a — Performance-Bench-Foundation + `GG-RT-004`:**

- Lieferziel: NEU ADR-0041 (Bench-Pattern + Mess-Protokoll +
  Regression-Schwelle) + NEU `pyproject.toml`-`[dependency-
  groups.perf]` mit pytest-benchmark + NEU Dockerfile-`perf`-
  Stage + NEU `tests/perf/` + NEU `Makefile`-`perf`-Target +
  NEU `tests/perf/baseline.json` (committed). `GG-RT-004`
  SOLLTE (100 Geraete × 10 000 Ticks ohne verlorene Events).
  Plus DoD-Bestaetigung `GG-RT-002` (M1-Determinismus) und
  `GG-RT-003` (M3-Stale-Markierung).
- Anti-Scope: Kein `GG-RT-005` (Welle-4b-b); kein `GG-RT-001`
  Backpressure-Healthcheck (Welle-4b-c); keine `make perf`-
  Integration in `make gates`/`make ci`; kein CI-`perf.yml`-
  Workflow.
- ADR-Lifecycle: NEU ADR-0041 `Provisional` in Welle-4b-a-C1;
  `Accepted` in M6-Welle-7-Closure-C1 gebuendelt mit ADR 0042
  + ADR 0043 + ADR 0044.

**Welle 4b-b — `GG-RT-005` Telemetry-Port-Bench:**

- Lieferziel: 10 000 Points/s am Telemetry-Port mit Payloads
  ≤ 256 Byte (`GG-RT-005` SOLLTE-Akzeptanz). Mess-Methodik
  + Probe + ggf. Erweiterung des Welle-4b-a-Bench-Patterns.
- ADR-Lifecycle: ggf. ADR-0041-Schaerfung per ADR-0011-
  Pattern (falls Mess-Surface die Bench-Foundation
  substanziell erweitert).

**Welle 4b-c — `GG-RT-001` Backpressure-Healthcheck:**

- Lieferziel: Tick-Dauer/p95-Jitter/missed-Ticks-Telemetrie
  als NEU TickLoop-Healthcheck-Surface (`GG-RT-001` MUSS-
  Akzeptanz fuer 10ms-Modus); Probe-Run unter Last; ggf.
  NEU Telemetry-Port-Hook.
- ADR-Lifecycle: ggf. NEU ADR fuer Healthcheck-Surface (M3-
  Welle-5-Observability-Port-Trio-Erweiterung; Pattern
  analog ADR-0024-Schaerfung).

**Carveout-Aufloesung opportunistisch** (gemeinsam Welle 4b-
a/b/c): **Snapshot-Envelope-v2-Body-Serialisierung** falls
Bench-Surface die Stub-Surface ohnehin anfasst. Welle-4b-a-
Anti-Scope schliesst das aus; 4b-b/4b-c koennten das
aufgreifen.

**Welle 5 — Sub-Slicing 5a/5b/5c** (Welle-5a-D-1 in
[`M6-welle-5a.md §3`](../done/M6-welle-5a.md); Pattern analog M5-
Welle-6 Sub-Slicing 6a/6b/6c):

**Welle 5a — Quality-Pipeline-Audit (`GG-SAFE-001..004` MUSS):**

- Lieferziel: End-to-End-Verifikation der existierenden Quality-
  Pipeline-Substanz (invalid-/nan-/missing-/stale-Statuswerte;
  Alarm-Emission). NEU 4 Integration-Smoke-Tests + NEU Audit-
  Doku-Tabelle in `docs/user/`. Inline-Luecken-Fixes wenn
  minimal; substantielle Luecken als NEU `open/`-Trigger
  (Welle-5a-D-3 Hybrid).
- Anti-Scope: Keine `GG-SAFE-005..008`; keine neue Quality-
  Enum-Variante; keine NEU ADR (D-5).
- ADR-Lifecycle: C1 entfaellt; Pattern analog M5-Welle-2.

**Welle 5b — Sim/Prod-Marker + Input-Validation (`GG-SAFE-007/008`
MUSS):**

- Lieferziel: `GG-SAFE-007` Sim/Prod-Trennung in UI/API-Doku
  + OpenAPI-Tags; `GG-SAFE-008` Adapter-Input-Validation-Audit
  + Pydantic-Strict-Mode-Schaerfung wo noetig.
- ADR-Lifecycle: ggf. ADR fuer Input-Validation-Pattern wenn
  substantielle Schaerfung am Adapter-Vertrag noetig.

**Welle 5c — SOLLTE-Items + IP/Netz (`GG-SAFE-005/006` +
Demo-Compose):**

- Lieferziel: `GG-SAFE-005` Fallback-Zustaende dokumentieren
  + ggf. erweitern; `GG-SAFE-006` Non-Determinism-Detection
  (Replay-Diff existiert in M3; dokumentieren + ggf. erweitern);
  IP-/Netz-Beschraenkung im Demo-Compose verankern.
- Carveout-Aufloesung opportunistisch: **Welle-3-Pre-init-
  Defense-Pattern verallgemeinern** (`carveouts.md §2.1
  Pattern-Forward`) — falls neue Adapter-Surfaces in M6
  hinzukommen.
- ADR-Lifecycle: ggf. ADR fuer Fallback-Pattern oder Demo-
  Compose-Hardening.

**Welle 6 — Deploy-Hardening + IEC-Smoke-Pfad-B:**

- Lieferziel:
  - `GG-DEPLOY-001..011`-Vollausbau (6 MUSS + 4 SOLLTE +
    1 KANN): Image-Audit (`make image-audit`) als CI-
    Pflicht-Gate; Container-Smoke-Test (`make runtime`
    pollt `/health`); Healthcheck-Pollung-Pattern.
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
    (`GG-DEPLOY-001..011`-Coverage; Trigger 010 in Welle 1
    + Welle-6-Image-Audit-CI-Gate aufgeloest).
  - **S-5** ADR-Erweiterungs-Pattern fortgefuehrt (M6-ADR-
    Anzahl gegen empirische M3/M4/M5-Spannweite 5-6 ADRs
    pro Meilenstein abgleichen; kein ADR-Sollwert per ADR
    0011; ADR 0011 = Schaerfung-ohne-Supersedes-Pattern).
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

- **ADR-Anzahl-Unter-Vorbelegung** — M6-Vorbelegung sind 3
  ADRs (Bench + SBOM + Image-Audit); empirische M3/M4/M5-
  Spannweite liegt bei 5-6 ADRs pro Meilenstein (M3 = 6,
  M4 = 6, M5 = 5). Risiko: zusaetzliche ADR-Pflicht in
  Welle 5+/6 (z.B. Validation-Strategie, Multi-Python-Stage)
  ueber die 3 vorbelegten hinaus, ohne dass die M6-D-4-
  Vorbelegung dies abgedeckt haette. **Mitigation:** ADR-
  Buendelung wo moeglich; ADR 0011 Schaerfung-ohne-
  Supersedes-Pattern fuer Inkremente ueber bestehende ADRs;
  ADR 0028 Link-Maintenance fuer Bezug-Refs; Welle-X-C0
  schaerft die ADR-Liste pro Welle.

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

- `GG-RT-001..005` (5 IDs; 3 MUSS + 2 SOLLTE) ✓ in
  M6-Welle-4 (`GG-RT-006` ist M3-Scope).
- `GG-SAFE-001..008` (8 IDs; 6 MUSS + 2 SOLLTE) ✓ in
  M6-Welle-5.
- `GG-CICD-001..007` (7 IDs; 5 MUSS + 2 SOLLTE) ✓ in
  M6-Welle-3 + Welle-2 (Release-Workflow + SBOM).
- `GG-DEPLOY-001..011` (11 IDs; 6 MUSS + 4 SOLLTE + 1 KANN)
  ✓ in M6-Welle-6 + Welle-1 (Image-Audit + krb5-Bump).

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
