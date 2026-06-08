# Welle 7 — M6 Closure (1/2 Tag)

**Status:** Done 2026-06-08 (M6-Closure-Welle) — Stack C0
`5415903` (Slice-Doc) + Sharpen `cff646c` (Review-Fixes B1-3) +
C1 `7a2aba8` (6 ADRs 0041..0046 `Provisional → Accepted`) +
C2 `0402b87` (NEU `done/M6-results.md`) + C3 `35c5fd0`
(Top-Level-Sync + M7-Eroeffnung) + C4a `1633ce1` (Self-Close-
Move rename-only) + C4b (Cross-Doc-Refs-Sync; dieser Commit).
Pattern
analog [`../done/M5-welle-7.md`](../done/M5-welle-7.md) +
[`../done/M4-welle-7.md`](../done/M4-welle-7.md).

**Pre-C0 (M6-Welle-6-Closure-Folge):** C4a `79ac725`
(`git mv M6-welle-6.md → done/`) + C4b `d8dd8d2` (Cross-Doc-
Refs-Sync) dienen gleichzeitig als M6-Welle-7-Pre-C0a/Pre-C0b.

---

## 1. Context

M6 (Performance + Security + CI/CD-Haertung) ist die siebte
Meilenstein-Spanne. Substanz-Wellen 0..6 sind `Done` (siehe
[`M6-perf-security-cicd.md §3.1`](M6-perf-security-cicd.md)):

- **Welle 0** Slice-Plan-Eroeffnung + Trigger-Triage.
- **Welle 1** Base-Image-Bump / krb5-CVE (Trigger 010) +
  ADR 0043.
- **Welle 2** SBOM + Release-Workflow (`GG-CICD-007`,
  Trigger 008) + ADR 0042.
- **Welle 3** CI/CD-Vollausbau (`GG-CICD-002/003/005/006` +
  3.13/3.14-Matrix, Trigger 031).
- **Welle 4a** Generated-Trivyignore-Permit + ADR 0044.
- **Welle 4b-a/b/c** Performance-Benches (`GG-RT-004/005/001`)
  + ADR 0041.
- **Welle 5a/5b/5c** Safety-Audit (`GG-SAFE-001..008`) +
  ADR 0045.
- **Welle 6** Deploy-Hardening + IEC-Smoke-Pfad-B
  (`GG-DEPLOY-001..011` + Trigger 009) + ADR 0046.

Welle 7 ist die **reine Closure-Welle** (Doku-only, kein Code):
M6-ADRs auf `Accepted`, Closure-Artefakt `done/M6-results.md`,
Roadmap-DoD-Sweep, Top-Level-Doku-Sync, Self-Close-Move des
M6-Slice-Plans nach `done/`.

---

## 2. Scope

Sechs Closure-Sektionen im NEU `done/M6-results.md` (Pattern
analog `done/M5-results.md`):

1. **Welle-Tabelle** — Quick-Glance aller M6-Wellen mit
   Liefer-Hash-Stack + Status.
2. **Abnahme-Belege** — Lastenheft-IDs, die M6 produktiv
   gemacht/auditiert hat (`GG-CICD-*`, `GG-RT-*`, `GG-SAFE-*`,
   `GG-DEPLOY-*`).
3. **Pro-Welle-Reviews** — Review-Folgen pro Substanz-Welle.
4. **S-1..S-6-Sweep** — M6-Welle-7-End-to-End-Verifikation.
5. **Welle-7-Erbschaft fuer M7+** — offene Trigger + Forward-
   Pointer.
6. **M6-Wandert-Nach** — was nach `done/` zieht.

Plus M6-ADR-Decision-Sweep (0041..0046) + Nicht-vollzogene
Items (bewusst).

---

## 3. Architektur-Entscheidungen (Welle-7)

### Welle-7-D-1 — Kein neuer ADR in Welle 7

Closure-Welle traegt keine NEU ADRs (Doku-only). Pattern
analog M4-/M5-Welle-7. ADR 0041..0046 werden in C1 von
`Provisional` auf `Accepted` gezogen — kein neuer Entscheidungs-
Text.

### Welle-7-D-2 — Gebuendelter ADR-Accept

Alle sechs M6-ADRs flippen in **einem** C1-Commit auf
`Accepted` (Pattern analog M5-Welle-7-C1 `62f988d` fuer 5
ADRs). Keine ADR hat einen offenen Validierungs-Spike; alle
sind produktiv-belegt (Code-Merge + Gates gruen am jeweiligen
Welle-Hash).

---

## 4. Liefer-Reihenfolge

### C0 — `docs(plan)`: M6-welle-7 Slice-Doc

**Dieser Commit.** Slice-Doc + Liefer-Reihenfolge +
DoD-Checkliste (initial leer). Keine ADR-/Code-Aenderung.

### C1 — `docs(adr)`: 6 M6-ADRs Provisional → Accepted

Pro ADR (0041/0042/0043/0044/0045/0046):

- **Status-Header** auf `Accepted — gezogen 2026-06-08 mit
  M6-Welle-7-C1 (dieser Commit; M6-Closure-Welle)` mit
  Erhalt der Provisional-/Proposed-Historie.
- **`Status geaendert am`** um `Provisional → Accepted`-
  Eintrag ergaenzt.
- **Status-Pfad-Body-Block** (falls vorhanden) auf
  `Accepted (M6-Welle-7-Closure)` geschlossen.
- ADR-README-Index Status-Spalte 6 Zeilen `Provisional →
  Accepted`.

Ein Commit, nur Status — keine Decision-Text-Aenderung.

### C2 — `docs(plan)`: NEU `done/M6-results.md`

Closure-Artefakt mit den sechs Sektionen aus §2 + ADR-Sweep
+ Nicht-vollzogene-Items. Pattern analog `done/M5-results.md`.

### C3 — `docs(plan)`: M6-Closure-Top-Level-Sync

- `roadmap.md`: M6-Section-Header `In Progress → Done`;
  **alle Live-`Aktiver Slice: M6`-Anker sweepen** — Top-Status
  (Z. ~3), Aktiver-Slice-Bullets (Z. ~149 + ~609),
  M6-Section-Active-Welle (Z. ~933). **Historischen
  M5-Closure-Beleg (Z. ~267 „… + 'Aktiver Slice: M6' (C3)")
  NICHT anfassen** — dokumentiert M5-welle-7-C3-Substanz.
  Entscheidung 2026-06-08: **M7 eroeffnen** — NEU `roadmap §M7`-
  Vorbelegungs-Block (GG-MVP-002 + GG-MVP-003 + offene Trigger
  033..037); aktiver Slice → **M7** (M7-Slice-Plan entsteht in
  M7-Welle-0, Pattern analog M6-Welle-0).
- `README.md` + `README.de.md`: **gesamten M6-Block neu
  schreiben**, nicht nur das Status-Token — die Bullets tragen
  Stale-Multi-Zeilen-Details (`active wave M6-Welle-5b`, `ADRs
  in flight 4 Provisional/1 Proposed`), die in einem `Done`-
  Meilenstein nicht stehenbleiben duerfen. M1..M5 → M1..M6;
  ADR-Count 38 → 44; M7-Eroeffnung notieren.
- `M6-welle-7.md` Status-Header `In Progress → Done`; §9-DoD-
  Checkboxen `[x]`.
- `M6-results.md` §5/§6 Handoff auf M7 praezisieren.
- `AGENTS.md` traegt bewusst keine Wellen/Slices/Commit-Hashes
  (§2.x) — **kein Edit**.

### C4a/C4b — `chore/docs(welle-7)`: Self-Close-Move

- **C4a** `git mv in-progress/M6-perf-security-cicd.md →
  done/` UND `in-progress/M6-welle-7.md → done/` (rename-
  only).
- **C4b** Cross-Doc-Refs-Sync nach Move.

---

## 5. Critical Files

**Welle-7-NEU (C0/C2):**

- `docs/plan/planning/in-progress/M6-welle-7.md` (C0).
- `docs/plan/planning/done/M6-results.md` (C2).

**Welle-7-MODIFY (C1 + C3):**

- `docs/plan/adr/0041..0046-*.md` — Status auf Accepted (C1).
- `docs/plan/adr/README.md` — Status-Spalte 6 Zeilen (C1).
- `docs/plan/planning/in-progress/roadmap.md` (C3).
- `docs/plan/planning/in-progress/README.md` (C3).
- `README.md` + `README.de.md` (C3).

**Welle-7-RENAME (C4a):**

- `M6-perf-security-cicd.md` + `M6-welle-7.md` nach `done/`.

**Welle-7-UNBERUEHRT:**

- Aller Code (`src/`, `tests/`) + `docs/user/*.md` +
  bestehende `done/M6-welle-*.md`.

---

## 6. Verifikationspfad

- `make gates` cache-frei gruen ohne `CRITICAL_COV_TARGETS`-
  Override am Closure-Hash (Test-Counts unveraendert — Welle 7
  ist Doku-only).
- `make docs-check` cache-frei gruen (Markdown-Link-Validator;
  faengt Move-Fan-out).

---

## 7. Risiken

- **R1 Move-Fan-out** — `M6-perf-security-cicd.md` ist breit
  referenziert; C4b muss alle Inbound-Links auf `../done/`
  umbiegen. Mitigation: `make docs-check` nach C4b.
- **R2 ADR-Index-Drift** — 6 Status-Spalten-Updates; Mitigation:
  ADR 0028 Link-Pflege + docs-check.
- **R3 roadmap-Multi-Anker-Sweep** — `roadmap.md` traegt den
  `Aktiver Slice: M6`-Marker an mehreren Live-Stellen (Top-Status
  + 2 Aktiver-Slice-Bullets + M6-Section-Active-Welle); ein naives
  Find/Replace riskiert (a) Teil-Sweep (Anker uebersehen) und
  (b) Korruption der historischen M5-Closure-Beleg-Zeile (Z. ~267
  „… 'Aktiver Slice: M6' (C3)"), die M5-welle-7-C3-Substanz
  dokumentiert und NICHT geaendert werden darf. Mitigation:
  explizite Zeilen-Sichtung statt Blind-Replace; `docs-check`
  nach C3. (Befund aus M6-welle-7-Review 2026-06-08.)

---

## 8. Wandert nach

Nach C4a/C4b liegen `M6-perf-security-cicd.md` + `M6-welle-7.md`
+ `M6-results.md` in `done/`. M6 ist abgeschlossen; aktiver
Slice wechselt auf **M7** (Entscheidung 2026-06-08, M6-welle-7-
Review-Befund 3): M7 ist der Container fuer die restliche
MVP-Arbeit (`GG-MVP-002` replay-source-integration +
`GG-MVP-003` abnahme-cli) plus die offenen Trigger
033/034/035/036/037. Der M7-Slice-Plan entsteht in M7-Welle-0
(Pattern analog M6-Welle-0); die roadmap-§M7-Vorbelegung wird in
C3 angelegt.

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [x] C1: ADR 0041..0046 `Accepted` + README-Index-Status.
- [x] C2: `done/M6-results.md` mit 6 Sektionen + ADR-Sweep.
- [x] C3: `roadmap.md` M6 `Done` + alle Live-`Aktiver Slice:
      M6`-Anker gesweept (Top + 2 Bullets + M6-Active-Welle;
      Z. ~267 historisch unberuehrt) + NEU §M7-Vorbelegung +
      aktiver Slice → M7.
- [x] C3: `README.md`/`README.de.md` gesamter M6-Block neu
      (Stale-Details raus; M1..M6; ADR 38→44; M7 eroeffnet).
- [x] C3: `M6-results.md` §5/§6 Handoff auf M7 praezisiert.
- [x] C4a: `M6-perf-security-cicd.md` + `M6-welle-7.md` →
      `done/` (rename-only `1633ce1`).
- [x] C4b: Cross-Doc-Refs-Sync (dieser Commit); `make docs-check`
      cache-frei gruen.
- [x] `make gates` cache-frei gruen am Closure-Hash (Verifikation).

---

## References

- [`M6-perf-security-cicd.md`](M6-perf-security-cicd.md) —
  M6-Meilenstein-Slice-Plan.
- [`../done/M5-welle-7.md`](../done/M5-welle-7.md) +
  [`../done/M4-welle-7.md`](../done/M4-welle-7.md) — Closure-
  Welle-Vorbilder.
- [`../done/M5-results.md`](../done/M5-results.md) — Results-
  Doc-Vorbild.
