# M6 — Performance + Security + CI/CD-Haertung — Closure-Ergebnisse

**Status:** Done (2026-06-08). M6-Abschluss-Gate `make gates`
cache-frei gruen **ohne** `CRITICAL_COV_TARGETS`-Override (10
A-1-Gates); `make fullbuild` cache-frei gruen (Trigger 010
krb5-CVE in Welle 1 aufgeloest; erstmals seit M3-Welle-7-Drift).
Alle sechs M6-ADRs (0041/0042/0043/0044/0045/0046) sind mit
Welle-7-C1 auf `Accepted` promoted.
**Bezug:** Slice-Plan
[`M6-perf-security-cicd.md`](../in-progress/M6-perf-security-cicd.md);
Welle-Slice-Begleit-Docs
[`M6-welle-0.md`](M6-welle-0.md),
[`M6-welle-1.md`](M6-welle-1.md),
[`M6-welle-2.md`](M6-welle-2.md),
[`M6-welle-3.md`](M6-welle-3.md),
[`M6-welle-4a.md`](M6-welle-4a.md),
[`M6-welle-4b-a.md`](M6-welle-4b-a.md),
[`M6-welle-4b-b.md`](M6-welle-4b-b.md),
[`M6-welle-4b-c.md`](M6-welle-4b-c.md),
[`M6-welle-5a.md`](M6-welle-5a.md),
[`M6-welle-5b.md`](M6-welle-5b.md),
[`M6-welle-5c.md`](M6-welle-5c.md),
[`M6-welle-6.md`](M6-welle-6.md),
[`M6-welle-7.md`](../in-progress/M6-welle-7.md);
Roadmap [`../in-progress/roadmap.md`](../in-progress/roadmap.md)
§M6.

---

## 1. Welle-Tabelle

| Welle | Datum | Lieferung | Stack |
| ----- | ----- | --------- | ----- |
| 0 | 2026-06-04 | Slice-Plan-Eroeffnung + Trigger-Triage (7 Decisions vorbelegt; 3 Trigger reklassifiziert: 008→W2, 009→W6, 010→W1). | `282a8cb..960f6ed` |
| 1 | 2026-06-05 | Base-Image-Bump / krb5-CVE (Trigger 010, M4-Erbschaft) — Null-Code-Edit durch Debian-13.5-Upstream-Drift + `apt-get upgrade`-Pattern. NEU ADR 0043 (Image-Audit-Strategie). | `4b1b3e9..4517614` (C1 ADR `c44e6d5`; C2 `b514170`) |
| 2 | 2026-06-05 | SBOM-Aktivierung + Release-Workflow (`GG-CICD-007`, Trigger 008): NEU `make sbom` (Syft) + `.github/workflows/release.yml` (6 Artefakte). NEU ADR 0042. | `0cc28f3..b41b7fc` (C2 `235395e`) |
| 3 | 2026-06-05 | CI/CD-Vollausbau (`GG-CICD-002/003/005/006`): 4 GitHub-Actions-Workflows + Python-3.13/3.14-Matrix; Trigger 031 (`make fullbuild`-CI-Gate) aufgeloest. C1 entfaellt. | `08a8034..c36f734` (C2 `ce13253`; Post-Push `0891f65`) |
| 4a | 2026-06-06 | Generated-Trivyignore-Permit (vulnignore-Pattern aus m-trace; Trigger-033-Temp-Deferral). NEU ADR 0044 (ADR-0011-Schaerfung an ADR-0043 §2.2). | `9bb6a92..789ac50` (C1 ADR `94dff9e`; C2 `8fbd17c`) |
| 4b-a | 2026-06-06 | Performance-Bench-Foundation (`GG-RT-004`): NEU `tests/perf/` + Dockerfile-`perf`-Stage + `make perf` + opt-in `[perf]`-Extra. NEU ADR 0041. | `f2fbcc0..76a2f40` (C1 ADR `43569d2`; C2 `5d8c497`) |
| 4b-b | 2026-06-06 | `GG-RT-005` Telemetry-Port-Throughput-Bench (10 000 Points/s ≤ 256 Byte). C1 entfaellt (ADR-0041-Schaerfung negativ). | `beb5dee..c8625f7` (C2 `a2feff7`) |
| 4b-c | 2026-06-06 | `GG-RT-001` Backpressure-Healthcheck: NEU `TickLoopHealthcheckAdapter` + `GET /runs/{id}/healthcheck`. C1 entfaellt. **Welle-4-Subdivision komplett.** | `c5543fd..7001989` (C2 `a98f967`) |
| 5a | 2026-06-06 | Quality-Pipeline-Audit (`GG-SAFE-001..004` MUSS): 7 Smokes + Audit-Doku. 001/002 ✓ produktiv; 003 ⚠ partial → Trigger 035; 004 ✗ → Trigger 034. C1 entfaellt. | `4b36185..52cb698` (C2 `4c1a693`) |
| 5b | 2026-06-07 | Sim/Prod-Marker + Input-Validation (`GG-SAFE-007/008` MUSS): NEU `_BaseRequest`-Strict-Mixin + 11 Smokes. NEU ADR 0045. | `0d3bb61..06a20c3` (C1 ADR `cee5aab`; C2 `b580840`) |
| 5c | 2026-06-07 | SOLLTE-Items + IP/Netz (`GG-SAFE-005/006` SOLLTE + Demo-Compose-`ports`-Hardening): 6 Smokes + 2 Audit-Doks. 005 ✓ produktiv; 006 ⚠ partial → Trigger 036. **Welle-5-Subdivision komplett.** C1 entfaellt. | `4b76ff7..` (C2 `f03c4c7`; C3 `b943099`; C4a `4db4715`) |
| 6 | 2026-06-08 | Deploy-Hardening + IEC-Smoke-Pfad-B (`GG-DEPLOY-001..011` + Trigger 009): NEU `GET /ready` Three-State (`GG-DEPLOY-006`) + `.devcontainer/` (`GG-DEPLOY-004`) + Dockerfile-Stage `iec61850-test` (Python 3.12) + 7 Smokes + Audit-Doku. NEU ADR 0046. Code-Review-BLOCKER-Fix (simulation-Healthcheck-Wiring) + 2 latente Slice-033-IEC-Bug-Fixes. | `fab6a8c..d8dd8d2` (C1 ADR `1d478e3`; C2 `f07e996`; C3 `79563c0`; C4a `79ac725`; C4b `d8dd8d2`) |
| 7 | 2026-06-08 | Closure: 6 M6-ADRs `Provisional → Accepted`; `done/M6-results.md` (dieses Dokument); `roadmap.md` M6 → `Done`; S-1..S-6-Sweep; Self-Close-Move `M6-perf-security-cicd.md` + `M6-welle-7.md`. | C0 (Slice-Doc) / C1 (6 ADRs → Accepted) / C2 (dieses Doc) / C3 (Roadmap-DoD + Top-Level-Sync) / C4a/C4b (Self-Close-Move + Refs) |

---

## 2. Abnahme-Belege

| Lastenheft-Kategorie | Stand nach M6 |
| -------------------- | ------------- |
| `GG-CICD-002/003/005/006/007` | ✓ produktiv (Welle 2+3): GitHub-Actions-Matrix-CI + SBOM + Release-Workflow + `make fullbuild`-CI-Gate. |
| `GG-QG-002` (Image-Audit) | ✓ produktiv (Welle 1): `make image-audit` (Trivy) als verankerter Pflicht-Gate-Vertrag (ADR 0043). |
| `GG-RT-001/004/005` | ✓ produktiv (Welle 4b): Backpressure-Healthcheck + Tick-Loop-Bench + Telemetry-Port-Bench (ADR 0041). |
| `GG-SAFE-001/002/005/007/008` | ✓ produktiv (Welle 5): Quality-Pipeline + Fallback + Sim/Prod-Marker + strikte Input-Validation (ADR 0045). |
| `GG-SAFE-003` | ⚠ partial Lücke → [Trigger 035](../open/035-safe-003-comm-failure-missing-quality.md). |
| `GG-SAFE-004` | ✗ Lücke → [Trigger 034](../open/034-safe-004-max-age-stale-quality.md). |
| `GG-SAFE-006` | ⚠ partial (`diff_replay` ✓; `replay_diff_status` + `ReplaySourcePort` fehlen) → [Trigger 036](../open/036-safe-006-replay-diff-status-replay-source-integration.md). |
| `GG-DEPLOY-001..006/011` | ✓ produktiv (Welle 1/5c/6): Compose + offline + Linux + DevContainer + `docker compose up`-Demo-`healthy` + `/ready`-Three-State-Healthcheck (ADR 0046). |
| `GG-DEPLOY-007..010` | ⏸ M7+ (verteiltes Deployment / Kubernetes / Rolling-Update / Rollback) → [Trigger 037](../open/037-deploy-007-010-multi-node-deployment.md). |

Audit-Dokus unter `docs/user/`: `safe-001-004-quality-pipeline.md`,
`safe-005-006-fallback-determinism.md`,
`safe-007-008-sim-prod-input-validation.md`,
`demo-compose-hardening.md`, `deploy-hardening.md`.

---

## 3. Pro-Welle-Reviews

- **Welle 1** — Trigger-010-Closure ohne Code-Edit (Upstream-Drift-
  Verifikation); ADR 0043 §2.2-Defer-Form als Quality-Gate-Vertrag.
- **Welle 4a** — vulnignore-Pattern-Import aus m-trace; ADR 0044 als
  additive §2.2-Erweiterung (kein Supersedes).
- **Welle 4b-a/b/c** — je Self-Review-Folgen (4b-a 4 Findings inkl.
  ADR-0041-§2.2-Vertragsbruch rueckwirkend; 4b-b 7 Findings; 4b-c
  2× 7 Findings).
- **Welle 5a/5b/5c** — Audit-Wellen mit C0-/C2-Review-Folgen
  (5a 6 Findings; 5b 7 Findings; 5c 4 Findings); 3 NEU `open/`-
  Trigger (034/035/036).
- **Welle 6** — Code-Review (1 BLOCKER: produktiv-`/ready`-
  simulation-Healthcheck-Wiring fehlte → gefixt + getestet; 8
  Deviations bestaetigt; 2 LOW). Beim realen `make test-iec61850`
  zwei latente Slice-033-Bugs gefunden+gefixt (SPDX-`#`-Header
  bricht libiec61850-Parser; String-`source`-Assertions).

---

## 4. S-1..S-6 Verification (M6-Welle-7-End-to-End-Sweep)

- **S-1 M6-Trigger-Sweep:** in M6 eroeffnet/aufgeloest — Trigger 010
  (W1 ✓), 008 (W2 ✓), 031 (W3 ✓), 009 (W6 ✓) aufgeloest; Trigger
  033 (OTel-Collector-CVE, Temp-Deferral via vulnignore), 034/035
  (`GG-SAFE-003/004`), 036 (`GG-SAFE-006`), 037 (`GG-DEPLOY-007..
  010`) bleiben offen als M7+/Stable-Watch.
- **S-2 Sub-Slicing-Schwelle:** Welle 4 → 4a/4b(-a/b/c), Welle 5 →
  5a/5b/5c, Welle 6 monolithisch (User-Ask „Alles fixen", Welle-6-
  D-1) — Sub-Slicing-Beschluss je per Welle-N-D-1 dokumentiert.
- **S-3 Default-Gates:** `make gates` cache-frei gruen **ohne**
  `CRITICAL_COV_TARGETS`-Override am Closure-Hash (10 A-1-Gates).
- **S-4 Image-Audit:** `make image-audit` cache-frei gruen
  (`GG-DEPLOY-*`-Coverage; Trigger 010 W1 + CI-Gate W3 aufgeloest;
  Trigger 033 als ADR-0044-vulnignore-Temp-Deferral).
- **S-5 ADR-Erweiterungs-Pattern:** M6 = **6 ADRs** (0041..0046),
  innerhalb der empirischen M3/M4/M5-Spannweite (5-6 ADRs/
  Meilenstein); kein ADR-Sollwert (ADR 0011 = Schaerfung-ohne-
  Supersedes-Pattern, kein Zaehl-Vertrag).
- **S-6 Lastenheft-Coverage-Sweep:** M6-Kategorien `GG-CICD-*`/
  `GG-RT-*`/`GG-SAFE-*`/`GG-DEPLOY-*` auditiert (siehe §2); offene
  Lücken sind ueber Trigger 034/035/036/037 verankert. Projekt-
  Closure-/M7-Entscheidung siehe §6.

---

## 5. Welle-7-Erbschaft fuer M7+

- **Offene `open/`-Trigger:** 033 (OTel-Collector Go-stdlib-CVE,
  Stable-Watch), 034 (`GG-SAFE-004` max_age), 035 (`GG-SAFE-003`
  Comm-Failure), 036 (`GG-SAFE-006` replay_diff_status +
  ReplaySourcePort), 037 (`GG-DEPLOY-007..010` Multi-Node).
- **Next-Plaene** (`planning/next/`): `replay-source-integration.md`
  (`GG-MVP-002`, aktiviert Trigger 036), `abnahme-cli.md`
  (`GG-MVP-003` `make accept`).
- **IEC-61850 Pfad-A-Watch:** sobald `pyiec61850-ng` ein
  cp314-/ABI3-Wheel publiziert, faellt die `iec61850-test`-Compat-
  Stage weg (Skip-Marker-Entfernung + Stage-Removal als
  `chore(deps)`-Slice; ADR 0046 §7).

---

## 6. M6-Wandert-Nach

- `M6-perf-security-cicd.md` + `M6-welle-7.md` → `done/` (C4a).
- `M6-results.md` (dieses Doc) liegt in `done/`.
- Aktiver Slice wechselt nach M6-Closure auf **M7** bzw. — falls
  kein M7 vorgesehen — auf Projekt-Closure (S-6; Entscheidung in
  `roadmap.md` §M6-C3).

---

## 7. M6-ADR-Decision-Sweep

| ADR | Titel | Welle | Status |
| --- | ----- | ----- | ------ |
| 0041 | Performance-Bench-Pattern + Regression-Schwelle | 4b-a | Accepted (W7-C1) |
| 0042 | SBOM-Tool + Release-Workflow-Pattern | 2 | Accepted (W7-C1) |
| 0043 | Image-Audit-Strategie + Trivy-Defer-Pattern | 1 | Accepted (W7-C1) |
| 0044 | Generated-Trivyignore-Permit (ADR-0011-Schaerfung an 0043) | 4a | Accepted (W7-C1) |
| 0045 | HTTP-API-Request-Body-Strict-Validation (ADR-0011-Schaerfung an 0037) | 5b | Accepted (W7-C1) |
| 0046 | Multi-Python-Test-Stage-Pattern (ADR-0011-Schaerfung an 0002) | 6 | Accepted (W7-C1) |

Drei der sechs M6-ADRs sind ADR-0011-Schaerfungen bestehender
`Accepted`-ADRs (0044→0043, 0045→0037, 0046→0002) — kein
Supersedes; die geschaerften ADRs bleiben textlich unveraendert.

---

## 8. Nicht-vollzogene Items (bewusst)

- **`GG-SAFE-003/004/006`-Vollausbau** — partial/Lücke, ueber
  Trigger 034/035/036 in `open/` verankert (Compliance-/Reale-
  Compose-Demo-getrieben).
- **Verteiltes Deployment (`GG-DEPLOY-007..010`)** — Post-MVP,
  Trigger 037.
- **IEC-61850 Real-Library auf Python 3.14** — Compat-Stage auf
  3.12 (ADR 0046); Pfad A (cp314-Wheel) bleibt bevorzugte Endform.
- **OTel-Collector-CVE-2026-42504** — Temp-Deferral via vulnignore
  (ADR 0044); echte Aufloesung bei Stable-Release-Bump (Trigger
  033).
- **Container-Image-Signing / Multi-Arch / PyPI-Publishing** —
  M7+ (ADR 0042 Out-of-Scope).

---

## References

- [`M6-perf-security-cicd.md`](../in-progress/M6-perf-security-cicd.md) —
  M6-Meilenstein-Slice-Plan.
- [`M5-results.md`](M5-results.md) + [`M4-results.md`](M4-results.md)
  — Results-Doc-Vorbilder.
- ADR-Index [`../../adr/README.md`](../../adr/README.md).
