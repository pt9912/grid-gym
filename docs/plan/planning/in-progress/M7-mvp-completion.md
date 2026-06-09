# Slice-Plan — M7 MVP-Abschluss — In Progress

**Status:** In Progress — eroeffnet 2026-06-08 mit M7-Welle-0-C1
(dieser Commit; NEU Slice-Plan). M7 ist der Container fuer die
nach M6 verbliebene MVP-Arbeit plus die offenen Safety-Trigger.
Eroeffnet als M6-Welle-7-Closure-Handoff (Entscheidung 2026-06-08,
M6-welle-7-Review-Befund 3 — M2..M6 waren vorbelegt, M7 ist NEU).
Welle 0 (Slice-Plan-Eroeffnung + Trigger-Triage) siehe
[`M7-welle-0.md`](../done/M7-welle-0.md).

---

## 1. Zweck + Architektur-Familie

M7 schliesst die letzten **MVP-Pflicht-IDs** ab, die M1..M6 offen
gelassen haben, und auditiert die verbliebenen Safety-Lücken:

| Sub-Bereich | ID / Trigger | Beleg-Familie |
| ----------- | ------------ | ------------- |
| **Replay-Spine-Closure** | `GG-MVP-002` / Trigger 036 (`GG-SAFE-006`) | NEU `ReplaySourcePort` + Per-Lauf-`replay_diff_status`-Metrik + Core-Spine-Lifecycle-Hook ueber den bestehenden `diff_replay()`-Algorithm. Plan [`M7-welle-1.md`](../done/M7-welle-1.md). |
| **Abnahme-Tooling** | `GG-MVP-003` | NEU `make accept` + `tools/accept.py` (Szenario-Validierung + deterministischer Replay + `/ready`-Healthcheck-Aggregat) + `AbnahmeReport`-JSON-Schema (Pydantic-strict). Plan [`../next/abnahme-cli.md`](../next/abnahme-cli.md). |
| **Safety-Closure** | Trigger 034 (`GG-SAFE-004`) + 035 (`GG-SAFE-003`) | `max_age`-`STALE`-Markierung + Adapter-Comm-Failure → `MISSING`/`STALE` + Alarm. |

**Architektur-Erbschaft:** Replay-Core (`hexagon/core/replay/
diff.py`) + `/ready`-Healthcheck (M6-Welle-6) + `TickLoop`-Spine
sind alle produktiv — M7 ergaenzt Lifecycle-Verkabelung + Tooling
ohne neue Driving-/Driven-Architektur-Familien.

**Sub-Slicing-Schwelle** (analog M4/M5/M6): > 300 Zeilen Slice-Doc
ODER > 5 Code-Commits ODER > 2 unabhaengige Sub-Bereiche →
Sub-Welle-Split; Welle-X-C0-Beschluss pro Welle.

---

## 2. Erfolgskriterien

**MUSS-IDs (MVP-Abschluss):**

- `GG-MVP-002` — `replay_diff_status`-Per-Lauf-Marker
  (Architektur §15 Z. 820 + 823) + `ReplaySourcePort`-Verkabelung
  mit `diff_replay()` (Lastenheft Z. 2292) produktiv; Trigger 036
  aufgeloest.
- `GG-MVP-003` — `make accept` liefert maschinenlesbaren
  Aggregat-Abnahme-Status (Szenario + Replay + Healthcheck) als
  `AbnahmeReport`-JSON.

**SOLLTE/Audit-IDs:**

- `GG-SAFE-004` (Trigger 034) — `max_age`-`STALE`-Markierung
  geschlossen oder als bewusste Carveout-Notiz verankert.
- `GG-SAFE-003` (Trigger 035) — Adapter-Comm-Failure-Quality-
  Pfad geschlossen oder verankert.

**DoD-Gates:** `make gates` cache-frei gruen ohne Override;
`make fullbuild` gruen; `make docs-check` gruen; pro Sub-Welle
Smoke-/Unit-Test-Coverage; M7-ADRs (falls noetig) auf `Accepted`
mit M7-Closure.

---

## 3. Liefer-Reihenfolge (Wellen)

### 3.1 Welle-Status-Tabelle

| # | Titel | Status | Slice-Doc | Scope / Trigger |
| - | ----- | ------ | --------- | --------------- |
| 0 | Slice-Plan-Eroeffnung + Trigger-Triage | **In Progress 2026-06-08** (C0..C2) | [`M7-welle-0.md`](../done/M7-welle-0.md) | Plan-Welle; carveouts-Triage 034/035/036 → Active |
| 1 | ReplaySource-Integration (`GG-MVP-002`) | **Done 2026-06-09** (1a + 1b-a + 1b-b) | [`M7-welle-1.md`](../done/M7-welle-1.md) | `ReplaySnapshotPort` + `replay_diff_status` + Core-`finalize()`-Hook + `GG-TERM`-Preflight; ADR 0047/0048/0049; Trigger 036 aufgeloest. `GG-MVP-002` ✓ produktiv |
| 2 | Abnahme-CLI (`GG-MVP-003`) | Pending | TBD | `make accept` + `tools/accept.py` + `AbnahmeReport`-Schema |
| 3 | Safety-Closure (`GG-SAFE-003/004`) | Pending | TBD | Trigger 034 (`max_age`) + 035 (Comm-Failure) |
| X | M7-Closure | Pending | TBD | `done/M7-results.md` + ADR-Accept + Roadmap-DoD-Sweep |

**Aktiver Slice:** M7-Welle-1 **Done 2026-06-09** (`GG-MVP-002`
✓ produktiv, Self-Close → `done/`). Naechster Slice: **M7-Welle-2**
(`GG-MVP-003` Abnahme-CLI) — noch nicht eroeffnet.

### 3.2 Pending-Wellen-Vorbelegung

- **Welle 1** — `GG-MVP-002`: Plan
  [`M7-welle-1.md`](../done/M7-welle-1.md)
  (~6-7 Tage; ggf. Sub-Slicing). NEU `ReplaySourcePort`-Driven-
  Slot + `replay_diff_status`-Metrik + TickLoop-/Run-Lifecycle-
  Hook. Loest Trigger 036.
- **Welle 2** — `GG-MVP-003`: Plan
  [`../next/abnahme-cli.md`](../next/abnahme-cli.md) (~1.5-2.5
  Tage). NEU `make accept` + `tools/accept.py` (Headless-TickLoop-
  Runner-Helper) + drei Sub-Steps + `AbnahmeReport`-Schema.
- **Welle 3** — Safety-Closure: Trigger 034
  ([`../open/034-safe-004-max-age-stale-quality.md`](../open/034-safe-004-max-age-stale-quality.md))
  + 035
  ([`../open/035-safe-003-comm-failure-missing-quality.md`](../open/035-safe-003-comm-failure-missing-quality.md)).

---

## 4. Out-of-Scope (M7+ / permanent)

- **`GG-DEPLOY-007..010` Multi-Node/K8s** (Trigger 037) — bleibt
  Trigger-Gated; Stakeholder-/Skalierungs-getrieben, kein
  MVP-MUSS.
- **OTel-Collector-CVE-2026-42504** (Trigger 033) — Stable-Watch;
  loest sich bei Upstream-Release (vulnignore-Temp-Deferral
  aktiv, ADR 0044).
- **Produktive Anlagensteuerung** (Lastenheft Z. 1161-1163) —
  permanent ausgeschlossen (`carveouts.md §2.7`).
- Weitere `Trigger-Gated`-Carveouts (SOLLTE-Geraete 016..024,
  RL-Adapter 030, BESS-Reserve-Market 026, Tooling-Trigger
  004/005/007/011) — bleiben offen ohne M7-Lieferpunkt.

---

## 5. Risiken + Fallback

- **R1 `GG-MVP-002`-Scope** (~6-7 Tage) — groesste M7-Substanz;
  ggf. Sub-Slicing (Welle 1a/1b). Mitigation: Welle-1-C0-
  Sub-Slicing-Beschluss.
- **R2 next/-Plan-Drift** — `replay-source-integration.md` +
  `abnahme-cli.md` sind pre-M7 gesharpt (teils gegen M6-Welle-6-
  Annahmen). Mitigation: Welle-X-C0 aktiviert + re-sharpt gegen
  den realen M7-Stand.
- **R3 MVP-Abschluss-Definition** — was „MVP fertig" heisst, ist
  bis zur M7-Closure offen (Trigger 037/033 bleiben legitim
  offen). Mitigation: M7-D-4 + M7-Closure-Kriterium in
  `done/M7-results.md`.

---

## 6. Wandert nach

`M7-mvp-completion.md` bleibt in `in-progress/` bis zur
M7-Welle-X-Closure (analog `M6-perf-security-cicd.md` in
M6-Welle-7-C4a); dann `git mv → done/` + `done/M7-results.md`.

---

## 7. Verifikationspfad

- Pro Sub-Welle: `make gates` + Smoke-/Unit-Coverage am
  Welle-Closure-Hash.
- `make fullbuild` cache-frei gruen am M7-Closure-Hash.
- `make docs-check` cache-frei gruen ueber alle M7-Commits.

---

## References

- [`M7-welle-0.md`](../done/M7-welle-0.md) — Welle-0-Begleitdoc +
  Decision-Liste + Trigger-Triage.
- [`../done/M6-results.md`](../done/M6-results.md) — M6-Closure +
  §5 Welle-7-Erbschaft fuer M7.
- [`M7-welle-1.md`](../done/M7-welle-1.md)
  (`GG-MVP-002`) +
  [`../next/abnahme-cli.md`](../next/abnahme-cli.md)
  (`GG-MVP-003`).
- [`roadmap.md §M7`](roadmap.md) — M7-Vorbelegung.
- [`../../../../spec/lastenheft.md`](../../../../spec/lastenheft.md)
  (`GG-MVP-002/003`, `GG-SAFE-003/004/006`, `GG-REPLAY-004..006`).
