# M7 — MVP-Abschluss — Closure-Ergebnisse

**Status:** Done (2026-06-12). **Der MVP ist geliefert** —
MVP-Abschluss-Kriterium (M7-D-4, finalisiert als Welle-X-D-3):
`GG-MVP-002` + `GG-MVP-003` produktiv, `GG-SAFE-003/004`
geschlossen → **alle vier `GG-MVP-*`-Punkte (001/002/003/004)
UND alle vier `GG-SAFE-001..004`-MUSS-IDs produktiv**; Trigger
033/037/038/039/040 bleiben legitime Post-MVP-Trigger.
M7-Abschluss-Gate `make gates` cache-frei gruen (10 A-1-Gates,
ohne Override); `make test-integration` 139 passed / 4 skipped
(Rest nur IEC-Python-3.13); `make fullbuild` inkl.
`accept-pin-check` + `make docs-check` cache-frei gruen.
Fuenf M7-ADRs (0047/0048/0049/0052/0053) sind mit Welle-X-C1
auf `Accepted` promoted; [`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md)/0051 bleiben bewusst
`Proposed` (Welle-X-D-2).
**Bezug:** Slice-Plan
[`M7-mvp-completion.md`](../done-archive/M7-mvp-completion.md);
Welle-Slice-Begleit-Docs
[`M7-welle-0.md`](../done-archive/M7-welle-0.md),
[`M7-welle-1.md`](../done-archive/M7-welle-1.md) (Gruppenplan),
[`M7-welle-1a.md`](../done-archive/M7-welle-1a.md),
[`M7-welle-1b-a.md`](../done-archive/M7-welle-1b-a.md),
[`M7-welle-1b-b.md`](../done-archive/M7-welle-1b-b.md),
[`M7-welle-2.md`](../done-archive/M7-welle-2.md),
[`M7-welle-3.md`](../done-archive/M7-welle-3.md) (Gruppenplan),
[`M7-welle-3a.md`](../done-archive/M7-welle-3a.md),
[`M7-welle-3b.md`](../done-archive/M7-welle-3b.md),
[`M7-welle-X.md`](../done-archive/M7-welle-X.md);
Roadmap [`../in-progress/roadmap.md`](../in-progress/roadmap.md)
§M7.

---

## 1. Welle-Tabelle

| Welle | Datum | Lieferung | Stack |
| ----- | ----- | --------- | ----- |
| 0 | 2026-06-08 | Slice-Plan-Eroeffnung + Trigger-Triage (M7-D-1..D-4 vorbelegt; carveouts-Triage 034/035/036 → Active). NEU `M7-mvp-completion.md`. | `e27de7e..f96ba5a` (C1 `a25a6d9`; C2 `74a5108`) |
| 1a | 2026-06-08/09 | Zeitreihen-Persistenz (`GG-PERSIST-001`): NEU `TelemetrySinkPort` (Driven) + Postgres-/InMemory-Adapter + Alembic-`0002` + Core-`telemetry_sink`-Kwarg. NEU [`ADR 0047`](../../adr/0047-telemetry-sink-timeseries-persistence.md). | `933c9d5..4b9be80` (C1 ADR `3ebb197`; C2 `4d00327`; Review-Folge `5983853`) |
| 1b-a | 2026-06-09 | `ReplaySnapshotPort`-Rekonstruktion: liest 1a-`telemetry_points`, deterministischer `timestamp`-Vertrag. NEU [`ADR 0048`](../../adr/0048-replay-snapshot-port-reconstruction.md) + NEU Trigger 038 (volle GG-TERM-Matrix). | `58203f1..39ee142` (C1 ADR `fb965c6`; C2 `2b755d6`) |
| 1b-b | 2026-06-09 | Replay-Lifecycle-Closure: Core-`finalize()`-Naht + `replay_diff_status`-Gauge + `GG-TERM-002/003`-MVP-Preflight + Zwei-Lauf-E2E-Beleg. NEU [`ADR 0049`](../../adr/0049-replay-lifecycle-finalize-hook.md) + NEU Trigger 039 (API-Replay). **`GG-MVP-002` ✓ produktiv**; `GG-SAFE-006` ⚠ → ✓; Trigger 036 aufgeloest. **Welle 1 komplett.** | `c193788..e6a2126` (C1 ADR `021e8d7`; C2 `6476267`; Review-Folge `4c6f4d6`) |
| 2 | 2026-06-09/10 | Abnahme-CLI (`GG-MVP-003`): NEU `make accept` + `tools/accept.py` + `AbnahmeReport`-Schema + Shared `scenario_yaml` + `check_demo_scenario_pin`-Lint. NEU [`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md)/0051 (`Proposed`, Review-Folge-Material) + NEU Trigger 040 (finalize-Headless-Naht). **`GG-MVP-003` ✓ produktiv → alle vier `GG-MVP-*` produktiv.** | `27df91b..d8ab5d6` (C2 `33ac255`; Review-Folge `92d10f5`) |
| 3a | 2026-06-11 | `max_age`-`STALE`-Stage (`GG-SAFE-004`): NEU `TickLoop`-Kwarg `max_age_ms` + Core-Stage vor `TickResult`-Bau + `from_snapshot`-Resume-Symmetrie. NEU [`ADR 0052`](../../adr/0052-max-age-stale-quality-stage.md). **`GG-SAFE-004` ✓**; Trigger 034 aufgeloest. | `9e266d2..4b3d2f1` (C1 ADR `744e31e`; C2 `23c614a`; Review-Folge `5a9960a`) |
| 3b | 2026-06-11/12 | Comm-Failure-Wrapper (`GG-SAFE-003`): NEU `CommFailureGuardedDeviceProtocolPort` (read-Fehler → `MISSING`-Point + `adapter_communication_lost`-Alarm) + NEU `_protocol_wrap_common.py`. NEU [`ADR 0053`](../../adr/0053-comm-failure-wrapper-missing-quality-alarm.md). **`GG-SAFE-003` ✓ — alle vier `GG-SAFE-001..004` produktiv**; Trigger 035 aufgeloest. **Welle 3 komplett.** | `6324042..427f3c2` (C1 ADR `caae16e`; C2 `3f28be1`; Review-Folge `82704b1`) |
| X | 2026-06-12 | Closure: 5 M7-ADRs `Provisional → Accepted` (0050/0051 bleiben `Proposed`); `done/M7-results.md` (dieses Dokument); `roadmap.md` M7 → `Done` + Post-MVP-Trigger-Watch; Self-Close-Move `M7-mvp-completion.md` + `M7-welle-X.md`. | C0 `6746321` / C1 `cdef313` / C2 (dieses Doc) / C3 (Roadmap-DoD + Top-Level-Sync) / C4a/C4b (Self-Close-Move + Refs) |

---

## 2. Abnahme-Belege

| Lastenheft-Kategorie | Stand nach M7 |
| -------------------- | ------------- |
| `GG-MVP-001..004` | ✓ produktiv komplett: 001/004 (M1..M6-Bestand) + **002** (Welle 1: ReplaySource-Integration, Zwei-Lauf-E2E-Beleg `docs/user/replay-determinism-e2e.md`) + **003** (Welle 2: `make accept`-Aggregat-Abnahme als `AbnahmeReport`-JSON). |
| `GG-PERSIST-001` | ✓ produktiv (Welle 1a): Zeitreihen-Persistenz mit allen Pflichtfeldern + deterministischer Sortier-Invariante ([`ADR 0047`](../../adr/0047-telemetry-sink-timeseries-persistence.md)). |
| `GG-SAFE-006` | ⚠ → ✓ (Welle 1b-b): `replay_diff_status`-Per-Lauf-Marker + Detail-Evidence via `log_port` ([`ADR 0049`](../../adr/0049-replay-lifecycle-finalize-hook.md)); Trigger 036 aufgeloest. |
| `GG-SAFE-004` | ✗ → ✓ (Welle 3a): `max_age`-`STALE`-Markierung im TickLoop-Spine ([`ADR 0052`](../../adr/0052-max-age-stale-quality-stage.md)); Trigger 034 aufgeloest. |
| `GG-SAFE-003` | ⚠ → ✓ (Welle 3b): Comm-Failure → `MISSING` + Alarm mit Ziel/Startzeit/Ursache ([`ADR 0053`](../../adr/0053-comm-failure-wrapper-missing-quality-alarm.md), §2.1-Scope-Lesart); Trigger 035 aufgeloest. **Alle vier `GG-SAFE-001..004` produktiv.** |
| `GG-TERM-002/003` | MVP-Preflight produktiv (Welle 1b-b; 5 `RunMetadata`-Felder); volle Equality-Matrix → [Trigger 038](../open/038-gg-term-002-003-full-equality-matrix.md). |

Audit-Dokus unter `docs/user/`: `replay-determinism-e2e.md`,
`safe-001-004-quality-pipeline.md` (alle vier IDs ✓),
`safe-005-006-fallback-determinism.md`.

---

## 3. Pro-Welle-Reviews

- **Welle 1a** — C2-Review-Folge `5983853` (F1/F2/F3).
- **Welle 1b-a** — C2-Review ohne Folge-Commit (Smokes pinnen
  Zwei-Lauf-Determinismus + Divergenz-Gegenprobe direkt).
- **Welle 1b-b** — C2-Review-Folge `4c6f4d6` (F1..F5:
  `finalize()`-Robustheit + Mapping-Single-Source; F4 → NEU
  Trigger 040).
- **Welle 2** — C2-Review-Folge `92d10f5` (F1
  Exit-Code-Klassifikation + F2/F3 Diagnostik); [`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md)/0051
  als Review-Folge-Vorschlaege (`Proposed`).
- **Welle 3a** — C2-Review-Folge `5a9960a` (F1
  Resume-Symmetrie + F2 ADR-Bilanz-Note + F3 Shared-Fake; F4
  Severity-Override-Lift zurueckgestellt → 3b-D-7).
- **Welle 3b** — C2-Review-Folge `82704b1` (F1
  Alarm-Nebenkanal-Vorrang komplett Best-Effort + F2
  Ein-Zeitstempel pro Fehler + F3 Shared-`RecordingTracePort`-
  Fake + F4 geteiltes Catch-Tupel `_protocol_wrap_common.py`).

---

## 4. S-1..S-6 Verification (M7-Welle-X-End-to-End-Sweep)

- **S-1 M7-Trigger-Sweep:** aufgeloest — 036 (W1b-b), 034 (W3a),
  035 (W3b). NEU eroeffnet — 038 (volle GG-TERM-Matrix, W1b-a),
  039 (API-Replay-Bedienung, W1b-b), 040 (finalize-Headless-
  Naht, W1b-b-Review/W2). Offen bleiben 033 (OTel-CVE
  Stable-Watch) + 037 (Multi-Node) + 038/039/040
  (Bedarfs-getrieben) + Trigger-Gated-Bestand (`carveouts.md`).
  **Post-Closure-Nachtrag 2026-06-12:** Trigger 032
  (Release-Workflow-Sensor-Run) wurde noch am Closure-Tag durch
  das erste reale Release **v0.1.0** aufgeloest (Tag-Push,
  Run `27415174757`; GHCR-Image + 5 Assets +
  SBOM-Digest-Bindung verifiziert) —
  [`032-…`](../done-archive/032-release-workflow-sensor-run.md).
- **S-2 Sub-Slicing-Schwelle:** Welle 1 → 1a/1b → 1b-a/1b-b
  (zweistufig, D-4-Final B + 1b-a-D-1); Welle 3 → 3a/3b
  (Welle-3-D-1); Welle 2 monolithisch — je per
  Welle-N-D-Beschluss dokumentiert.
- **S-3 Default-Gates:** `make gates` cache-frei gruen ohne
  Override am Closure-Hash (10 A-1-Gates; Doku-only-Welle,
  Test-Counts unveraendert: 139 passed / 4 skipped Integration).
- **S-4 Abnahme-Pfad:** `make accept` ([`GG-MVP-003`](../../../../spec/lastenheft.md#gg-mvp-003)) produktiv;
  `accept-pin-check` als CI-Gate haelt die Demo-Pins
  (`make fullbuild` gruen 2026-06-12).
- **S-5 ADR-Erweiterungs-Pattern:** M7 = **7 NEU ADRs**
  (0047..0053) — 5 `Accepted` (Welle-X-C1) + 2 `Proposed`
  (0050/0051, zukunftsgerichtete Review-Folge-Vorschlaege mit
  eigenen Lifecycle-Bedingungen, Welle-X-D-2). Die 5
  produktiv-belegten liegen in der empirischen M3..M6-Spannweite
  (5-6 ADRs/Meilenstein).
- **S-6 Lastenheft-Coverage-Sweep:** MVP-Scope komplett
  (`GG-MVP-001..004` ✓); `GG-SAFE-001..008` produktiv oder
  bewusst verankert (005 ✓, 006 ✓, 007/008 ✓ seit M6);
  verbleibende Kategorien (`GG-DEPLOY-007..010`, GG-TERM-
  Vollmatrix, `GG-FUTURE-*`, SOLLTE-Geraete) sind ueber Trigger
  + `carveouts.md` verankert. Post-M7-Entscheidung siehe §6.

---

## 5. Welle-X-Erbschaft (Post-MVP)

- **Offene `open/`-Trigger:** 033 (OTel-Collector
  Go-stdlib-CVE, Stable-Watch), 037
  (`GG-DEPLOY-007..010` Multi-Node/K8s), 038 (volle
  `GG-TERM-002/003`-Equality-Matrix), 039 (oeffentliche
  API-Replay-Bedienung), 040 (Core-Run-End-Naht fuer
  `TickLoop.finalize()` ohne Driver).
- **Next-Plaene** (`planning/next/`; konkret geplant, nicht
  aktiv — KEINE Trigger-Bedingung, Aktivierung per Mandat):
  [`041-adapter-pure-ignore-imports-rueckbau.md`](../next/041-adapter-pure-ignore-imports-rueckbau.md)
  (Umsetzungsslice fuer [`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md)) +
  [`042-fault-engine-location-and-naming.md`](../next/042-fault-engine-location-and-naming.md)
  (Umsetzungsslice fuer [`ADR 0051`](../../adr/0051-fault-engine-location-and-naming.md)).
- **[`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md)/0051 (`Proposed`):** [`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)-Bridge-
  Rueckbau + Fault-Engine-Standort/-Naming — `Provisional` erst
  mit dem jeweiligen Umsetzungsslice (next/041 bzw. next/042).
- **IEC-61850 Pfad-A-Watch (M6-Erbschaft):** cp314-Wheel von
  `pyiec61850-ng` loest die `iec61850-test`-Compat-Stage ab
  ([`ADR 0046`](../../adr/0046-multi-python-test-stage-pattern.md) §7); bis dahin 4 versions-bedingte Integration-Skips.
- **Comm-Failure-Wrapper-Anschluss:** etabliert ein kuenftiger
  Slice einen produktiven Adapter-`read()`-Pfad, ist
  `CommFailureGuardedDeviceProtocolPort` die fertige
  Comm-Failure-Schicht (eine Verdrahtungs-Zeile; [`ADR 0053`](../../adr/0053-comm-failure-wrapper-missing-quality-alarm.md) §2.1).
- **Trigger-Gated-Bestand:** SOLLTE-Geraete 016..024, RL-Adapter
  030, BESS-Reserve-Market 026, Tooling-Trigger — Index in
  [`../in-progress/carveouts.md`](../in-progress/carveouts.md).

---

## 6. M7-Wandert-Nach + Post-M7-Modus

- `M7-mvp-completion.md` + `M7-welle-X.md` → `done/` (C4a);
  `M7-results.md` (dieses Doc) liegt in `done/`.
- **Post-M7-Modus (Welle-X-D-4): Trigger-Watch, kein
  M8-Auto-Open.** Der MVP ist geliefert; es gibt kein offenes
  MUSS-Mandat. Die offenen Trigger (§5) tragen dokumentierte
  Aktivierungs-Bedingungen; ein neuer Meilenstein entsteht erst
  bei Trigger-Aktivierung oder Stakeholder-Mandat (bewusste
  Eroeffnungs-Entscheidung, Pattern M6-welle-7-Review-Befund 3).

---

## 7. M7-ADR-Decision-Sweep

| ADR | Titel | Welle | Status |
| --- | ----- | ----- | ------ |
| 0047 | TelemetrySinkPort Zeitreihen-Persistenz | 1a | Accepted (WX-C1) |
| 0048 | ReplaySnapshotPort Replay-Snapshot-Rekonstruktion | 1b-a | Accepted (WX-C1) |
| 0049 | Replay-Lifecycle: Terminal-Hook + `replay_diff_status` + GG-TERM-Preflight | 1b-b | Accepted (WX-C1) |
| 0050 | [`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) Bridge-Rueckbau (HTTP-Demo-Wiring) | 2 (Review-Folge) | **Proposed** (X-D-2: `Provisional` erst mit Umsetzungsslice `next/041`) |
| 0051 | Fault-Engine-Standort + Adapter-Begriffsklaerung | 2 (Review-Folge) | **Proposed** (X-D-2: `Provisional` erst mit Umsetzungsslice) |
| 0052 | `max_age`-basierte `STALE`-Quality-Stage | 3a | Accepted (WX-C1) |
| 0053 | Comm-Failure-Wrapper: Read-Fehler → `MISSING` + Alarm | 3b | Accepted (WX-C1) |

Vier der fuenf Accepted-ADRs sind [`ADR-0011`](../../adr/0011-schaerfung-ohne-abloesung.md)-Schaerfungen
bestehender Vertraege (0047→0039, 0049→0039/0024, 0052→0021,
0053→0030/0040) — kein Supersedes; die geschaerften ADRs bleiben
textlich unveraendert.

---

## 8. Nicht-vollzogene Items (bewusst)

- **Volle `GG-TERM-002/003`-Equality-Matrix** — MVP-Preflight
  deckt 5 `RunMetadata`-Felder; Vollausbau ueber Trigger 038
  (Compliance-/Multi-Plattform-getrieben).
- **Oeffentliche API-Replay-Bedienung** (`POST /runs`
  `replay_of`) — Runtime-/Test-/Demo-intern per 1b-b-D-7;
  Trigger 039.
- **Headless-Run-End-Naht fuer `finalize()`** — heute
  Driver-getriggert; Trigger 040.
- **Produktiver Adapter-`read()`-Pfad** — dokumentierte
  Bestand-Grenze ([`ADR 0053`](../../adr/0053-comm-failure-wrapper-missing-quality-alarm.md) §2.1; kein Requirement, kein Trigger).
- **[`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)-Bridge-Rueckbau + Fault-Engine-Naming** —
  [`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md)/0051 `Proposed`; Umsetzung Post-MVP.
- **Verteiltes Deployment (`GG-DEPLOY-007..010`)** — Post-MVP,
  Trigger 037.
- **OTel-Collector-CVE-2026-42504** — Temp-Deferral via
  vulnignore ([`ADR 0044`](../../adr/0044-generated-trivyignore-permit.md)); Aufloesung bei Stable-Release (Trigger
  033).

---

## References

- [`M7-mvp-completion.md`](../done-archive/M7-mvp-completion.md) —
  M7-Meilenstein-Slice-Plan.
- [`M7-welle-X.md`](../done-archive/M7-welle-X.md) — Closure-Welle
  (Decisions X-D-1..D-4).
- [`M6-results.md`](M6-results.md) + [`M5-results.md`](M5-results.md)
  — Results-Doc-Vorbilder.
- ADR-Index [`../../adr/README.md`](../../adr/README.md).
