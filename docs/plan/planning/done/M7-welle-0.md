# Welle 0 — M7 Slice-Plan-Eroeffnung + Trigger-Triage

**Status:** Done 2026-06-08 — Stack C0 `e27de7e` (Slice-Doc) +
C1 `a25a6d9` (NEU `M7-mvp-completion.md` Slice-Plan) + C2
(Trigger-Triage + roadmap-Flip + Status-Flip) + C4a `3f7efe2`
(Self-Close-Move rename-only) + C4b (Cross-Doc-Refs-Sync; dieser
Commit). Vorabraeumung + Slice-Plan-Eroeffnung
fuer **M7
(MVP-Abschluss)** — die nach M6 verbliebene MVP-Arbeit
(`GG-MVP-002` ReplaySource-Integration + `GG-MVP-003`
Abnahme-CLI) plus die offenen Safety-/Deploy-Trigger
(034/035/036/037) und der CVE-Stable-Watch (033). Pattern analog
[`../done/M6-welle-0.md`](../done/M6-welle-0.md) +
[`../done/M5-welle-0.md`](../done/M5-welle-0.md).

**Pre-C0 — bereits erledigt** (M6-Closure-Stack): M6-Welle-7-
Closure-Stack `5415903` → `8c0af4f` (C0..C4b inkl. Sharpen +
Hash-Backfill); M6 ist `Done` (siehe
[`../done/M6-results.md`](../done/M6-results.md)); roadmap §M7-
Vorbelegung wurde in M6-Welle-7-C3 angelegt. Welle 0 startet
damit direkt mit C0.

**Spec-Reife:** Reines Doc-Arbeitspaket (kein Code-Pfad-Wechsel;
Pattern analog M6-Welle-0). Welle-0-Decision-Liste (§3) sammelt
offene Fragen, entscheidet sie aber nicht — Entscheidungen
wandern in M7-Welle 1+ und werden im jeweiligen M7-ADR (falls
noetig) konkretisiert.

---

## 1. Context

M6 ist seit 2026-06-08 mit Welle-7-Closure abgeschlossen
([`../done/M6-results.md`](../done/M6-results.md)). Per
[`roadmap.md §M7`](../in-progress/roadmap.md) ist M7 (MVP-Abschluss) der NEU
eroeffnete aktive Slice — der Container fuer die letzte MVP-
Arbeit plus die offenen Trigger.

### 1.1 M7-Eingangsbestand

| Item | Quelle | M7-Relevanz |
| ---- | ------ | ----------- |
| `GG-MVP-002` ReplaySource-Integration | [`M7-welle-1.md`](../done/M7-welle-1.md) | **Pflicht-Substanz** — `ReplaySourcePort`-Adapter + `replay_diff_status`-Metrik + Core-Spine-Lifecycle-Hook; aktiviert [Trigger 036](../done/036-safe-006-replay-diff-status-replay-source-integration.md). ~6-7 Tage. |
| `GG-MVP-003` Abnahme-CLI | [`next/abnahme-cli.md`](M7-welle-2.md) | **Pflicht-Substanz** — NEU `make accept` + `tools/accept.py` (Szenario-Validierung + deterministischer Replay + `/ready`-Healthcheck) + `AbnahmeReport`-Schema. ~1.5-2.5 Tage. |
| Trigger 034 (`GG-SAFE-004` max_age) | [`open/034-…`](034-safe-004-max-age-stale-quality.md) | Safety-Lücke (max_age-`STALE`-Markierung fehlt) — M7-Closure-Substanz. |
| Trigger 035 (`GG-SAFE-003` Comm-Failure) | [`open/035-…`](035-safe-003-comm-failure-missing-quality.md) | Safety-Partial-Lücke (Adapter-Comm-Failure → `MISSING`/`STALE` + Alarm) — M7-Closure-Substanz. |
| Trigger 036 (`GG-SAFE-006` replay_diff_status) | [`open/036-…`](../done/036-safe-006-replay-diff-status-replay-source-integration.md) | Wird durch `GG-MVP-002` aufgeloest (gekoppelt). |
| Trigger 037 (`GG-DEPLOY-007..010` Multi-Node) | [`open/037-…`](../open/037-deploy-007-010-multi-node-deployment.md) | **Bleibt Trigger-Gated** — Stakeholder-/Skalierungs-getrieben; kein MVP-Pflicht-Item. |
| Trigger 033 (OTel-Collector-CVE) | [`open/033-…`](../open/033-otel-collector-go-stdlib-cve-bump.md) | **Bleibt Stable-Watch** — Temp-Deferral via vulnignore (ADR 0044); loest sich bei Upstream-Stable-Release unabhaengig von M7-Wellen. |

### 1.2 Existierende Substanz im Repo

M6-Welle-7-Closure-Stand (siehe
[`../done/M6-results.md`](../done/M6-results.md)):

- `make gates` cache-frei gruen ohne Override (10 A-1-Gates);
  `make fullbuild` gruen.
- M1..M6 alle `Done`; 44 ADRs `Accepted`.
- `diff_replay()`-Core-Algorithm ✓ produktiv (M6-Welle-5c-Audit),
  aber ohne Per-Lauf-`replay_diff_status`-Marker +
  `ReplaySourcePort`-Verkabelung (→ `GG-MVP-002`).
- `/ready`-Three-State-Healthcheck + `GET /runs/{id}/healthcheck`
  produktiv (M6-Welle-6) — Baseline fuer die Abnahme-CLI-Probes
  (`GG-MVP-003`).

---

## 2. Scope

Welle 0 liefert **drei Closure-Items** ueber 3 Commits (Pattern
analog M6-Welle-0):

1. **C0 — NEU `M7-welle-0.md` Slice-Doc** (dieser Commit) mit
   §1..§9-Struktur, Welle-0-Decision-Liste (§3), DoD (§9).
2. **C1 — NEU `M7-mvp-completion.md`** als kanonischer M7-Slice-
   Plan (analog `M6-perf-security-cicd.md`): §1 Zweck, §2
   Erfolgskriterien, §3 Liefer-Reihenfolge (Welle-Status-Tabelle
   + Pending-Vorbelegung), §4 Out-of-Scope, §5 Risiken, §6
   Wandert-Nach, §7 Verifikationspfad.
3. **C2 — Trigger-Triage + Status-Flip:** carveouts-Triage
   (034/035/036 → `Active in M7-Welle-X`; 033/037 bleiben
   gated); `roadmap.md §M7` `Vorbelegung → In Progress`;
   `in-progress/README.md` Aktive-Welle auf M7-Welle-1.

---

## 3. Architektur-Entscheidungen (Welle-0-Decision-Liste)

Offen — gesammelt, in M7-Welle 1+ entschieden.

### M7-D-1 — Sub-Slicing-Strategie

**Frage:** Wie wird M7 in Wellen geschnitten?

Vorbelegung (Welle-1-C0 entscheidet final):
- **Welle 1** — `GG-MVP-002` ReplaySource-Integration (groesste
  Substanz; aktiviert Trigger 036). Ggf. Sub-Slicing falls
  `ReplaySourcePort` + `replay_diff_status` + Lifecycle-Hook die
  Schwelle reissen.
- **Welle 2** — `GG-MVP-003` Abnahme-CLI (`make accept`).
- **Welle 3** — Safety-Closure `GG-SAFE-003/004` (Trigger
  034 + 035).
- **Welle 4+** — Closure (`done/M7-results.md`).
- Trigger 037 (Multi-Node) + 033 (CVE-Watch) bleiben
  Trigger-Gated; kein M7-Pflicht-Lieferpunkt.

### M7-D-2 — Trigger-Triage (Active vs. Gated)

| Trigger / Plan | Empfehlung | Begruendung |
| -------------- | ---------- | ----------- |
| `GG-MVP-002` (Trigger 036) | **Active M7-Welle-1** | MVP-Pflicht; Core-Diff ✓, nur Per-Lauf-Marker + Port fehlen. |
| `GG-MVP-003` | **Active M7-Welle-2** | MVP-Pflicht; baut auf `/ready` (M6-Welle-6). |
| Trigger 034 (`GG-SAFE-004`) | **Active M7-Welle-3** | Safety-Lücke; M-Closure-Sweep-Kandidat. |
| Trigger 035 (`GG-SAFE-003`) | **Active M7-Welle-3** | Safety-Partial-Lücke. |
| Trigger 037 (`GG-DEPLOY-007..010`) | **Bleibt Gated** | Multi-Node/K8s; Stakeholder-getrieben, kein MVP-MUSS. |
| Trigger 033 (OTel-CVE) | **Bleibt Stable-Watch** | Upstream-Release-getrieben; vulnignore-Temp-Deferral aktiv. |

### M7-D-3 — ADR-Bedarf

**Frage:** Erfordert M7 NEU ADRs?

Vorbelegung: `GG-MVP-002` braucht voraussichtlich **1 ADR**
(`ReplaySourcePort`-Surface + `replay_diff_status`-Vertrag;
siehe `next/replay-source-integration.md §5` D-5 „1-or-2-ADRs").
`GG-MVP-003` Abnahme-CLI braucht voraussichtlich **keinen** NEU
ADR (CLI-Tooling auf bestehender Surface). Safety-Closure
(034/035) ggf. ADR-0011-Schaerfungen. Welle-X-C1 entscheidet.

### M7-D-4 — MVP-Abschluss-Kriterium

**Frage:** Wann ist M7 (= der MVP) abgeschlossen?

Vorbelegung: wenn `GG-MVP-002` + `GG-MVP-003` produktiv und
`GG-SAFE-003/004` auditiert/geschlossen sind; Trigger 037/033
bleiben als legitime Post-MVP-Trigger offen. M7-Welle-X-Closure
(`done/M7-results.md`) pinnt das finale Kriterium.

---

## 4. Liefer-Reihenfolge (3 Commits)

### C0 — `docs(plan)`: M7-welle-0 Slice-Doc

**Dieser Commit.** NEU `M7-welle-0.md` (§1..§9) + Welle-0-
Decision-Liste + DoD (initial leer; C2 hakt ab) +
`in-progress/README.md` Bestand-Zeile.

### C1 — `docs(plan)`: NEU `M7-mvp-completion.md`

M7-Slice-Plan-Eroeffnung (analog `M6-perf-security-cicd.md`):
§1..§7 mit Welle-Status-Tabelle (Welle 0 = `In Progress`, Rest
`Pending`) + Pending-Vorbelegung. Plus `in-progress/README.md`
Slice-Plan-Eintrag.

### C2 — `docs(plan)`: Trigger-Triage + Status-Flip

- carveouts-Triage per M7-D-2 (034/035/036 → `Active in
  M7-Welle-X`; 037/033 bleiben).
- `roadmap.md §M7` `Vorbelegung → In Progress`.
- `in-progress/README.md` Aktive-Welle auf M7-Welle-1.
- DoD (§9) abhaken.

### C4a/C4b — `chore/docs(welle-0)`: Self-Close-Move

- **C4a** `git mv M7-welle-0.md → done/` (rename-only).
- **C4b** Cross-Doc-Refs-Sync. (`M7-mvp-completion.md` bleibt in
  `in-progress/` bis M7-Welle-X-Closure.)

---

## 5. Critical Files

**NEU (C0/C1):** `in-progress/M7-welle-0.md` (C0),
`in-progress/M7-mvp-completion.md` (C1).
**MODIFY (C0/C2):** `in-progress/README.md`,
`in-progress/roadmap.md` (§M7-Flip),
`in-progress/carveouts.md` (Triage).
**UNBERUEHRT:** Aller Code + Tests + `done/`-Slice-Docs + ADRs +
`README.md`/`README.de.md` (M7-Status-Sync ist Welle-X-Closure-
Material).

---

## 6. Verifikationspfad

- `make docs-check` cache-frei gruen ueber alle Welle-0-Commits.
- `make gates` unveraendert gruen (reine Doku-Welle; keine
  Code-/Test-Aenderung).
- Abnahme erfolgt pro Sub-Welle + final in M7-Welle-X-Closure
  (`done/M7-results.md`).

---

## 7. Risiken

- **R1 M7-Scope-Drift** — `GG-MVP-002` ist substanziell (~6-7
  Tage). Mitigation: Sub-Slicing-Schwelle pro Welle (Welle-X-C0-
  Beschluss).
- **R2 Trigger-Triage-Konflikt** — 037/033 koennten unerwartet
  aktiviert werden. Mitigation: carveouts-Triage-Tabelle als
  Single-Source; Welle-X-C0 re-evaluiert.
- **R3 next/-Plan-Drift** — `replay-source-integration.md` +
  `abnahme-cli.md` sind gesharpt aber pre-M7. Mitigation: Welle-
  X-C0 aktiviert (next/ → in-progress/) + re-sharpt gegen den
  M7-Stand.

---

## 8. Wandert nach

- **Self-Close-Move im eigenen Welle-Stack:** `git mv
  M7-welle-0.md → done/` (C4a) + Cross-Doc-Refs-Sync (C4b),
  Pattern analog M6-Welle-0-Self-Close.
- `M7-mvp-completion.md` (C1) bleibt in `in-progress/` bis
  M7-Welle-X-Closure (analog `M6-perf-security-cicd.md`).

---

## 9. DoD-Checkliste (mit C2 abzuhaken)

- [x] C0 — NEU `M7-welle-0.md` §1..§9 + Decision-Liste (`e27de7e`).
- [x] C1 — NEU `M7-mvp-completion.md` M7-Slice-Plan (`a25a6d9`).
- [x] C2 — carveouts-Triage (034/035 → `Active in M7-Welle-3`;
      036 GG-MVP-002-gekoppelt; 037/033 bleiben gated).
- [x] C2 — `roadmap.md §M7` `Vorbelegung → In Progress`.
- [x] C2 — `in-progress/README.md` Bestand-Eintraege
      (M7-mvp-completion + M7-welle-0); naechste Welle M7-Welle-1.
- [x] `make docs-check` cache-frei gruen.
- [x] `make gates` unveraendert gruen (reine Doku-Welle).

**Anti-Scope (Welle 0 NICHT):** kein Code-Diff; keine Tests;
keine NEU ADRs (Sub-Welle-Material); keine Welle-1+-Decisions
final.

---

## References

- [`../done/M6-results.md`](../done/M6-results.md) — M6-Closure +
  §5 Welle-7-Erbschaft fuer M7.
- [`../done/M6-welle-0.md`](../done/M6-welle-0.md) +
  [`../done/M5-welle-0.md`](../done/M5-welle-0.md) — Welle-0-
  Vorbild-Slice-Docs.
- [`M7-welle-1.md`](../done/M7-welle-1.md)
  (`GG-MVP-002`) +
  [`next/abnahme-cli.md`](M7-welle-2.md) (`GG-MVP-003`).
- [`roadmap.md §M7`](../in-progress/roadmap.md) — M7-Vorbelegung.
- [`carveouts.md`](../in-progress/carveouts.md) — Cross-M-Carveout-Index
  (M7-Welle-0-C2-Triage pflegt 034/035/036/037).
