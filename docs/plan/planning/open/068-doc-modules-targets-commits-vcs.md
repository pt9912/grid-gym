# 068 — d-check `doc-*`-Module aktivieren: targets / commits / vcs

**Status:** Open — **C1 (`targets`) geliefert** 2026-07-11; C2 (`commits`) + C3 (`vcs`) offen
**Datum:** 2026-07-11
**Quelle:** Modul-Review gegen das d-check-Handbuch (v0.41.0) — `targets`/`commits`/`vcs`
sind separate `doc-*`-Gates (kein `modules:`-Eintrag), via `d-check.mk`-Include verfuegbar.

---

## Befund

Drei git-/hermetische d-check-Module sind noch nicht scharf, obwohl ueber den Include
(`make doc-targets`/`doc-commits`/`doc-immutable`) verfuegbar. Sie mechanisieren
bestehende Konventionen. **Wichtig:** `docs-check` laeuft nur lokal im Handoff-Stop-Hook
([`ADR 0071`](../../adr/0071-enforcement-layer-hooks.md)), **nicht** in GitHub-CI — hermetische
Gates werden ans lokale `docs-check` gehaengt, Range-Gates brauchen einen CI-Job.

## Tranchen

- **C1 — `targets` (Doku↔Makefile) — ERLEDIGT 2026-07-11.** `targets:`-Block in
  `.d-check.yml` (`makefiles`/`doc-tables`, **ohne** `authority`); nur Richtung 1
  (`gate-phantom`: dokumentierte `make X` existieren). `make docs-check` haengt jetzt
  `doc-targets` an `doc-check`. Grün.
- **C1b — `targets` Richtung 2 (`gate-undocumented`):** `authority: AGENTS.md` setzen
  findet **38** undokumentierte (meist Utility-)Makefile-Regeln (`clean`, `sbom`, …).
  Auflösung: die echten Gates in `AGENTS.md` dokumentieren + Utility-Targets in
  `targets.exempt-targets` aufnehmen, dann Richtung 2 aktivieren.
- **C2 — `commits` (Message-Traceability):** Vorwärts-Gate (prüft nur die Commit-**Range**,
  nicht die Historie) — passt zum slice-getriebenen Modell (jeder Commit nennt seine
  Slice/Trigger/ADR/`GG-`-ID). `commits:`-Block (`id-patterns` + minimaler
  `exempt-pattern: '^(Merge |Revert )'`) + CI-Job in `ci.yml` (`make doc-commits
  RANGE=<base>..<head>`; PR `base..head`, push `before..after`). Konsequenz: auch
  `chore(tooling)`-Commits nennen künftig ihren Slice/Trigger (leichte Autoren-Disziplin).
- **C3 — `vcs` (ADR-Immutabilität):** mechanisiert „Nach `Accepted` gilt das
  Änderungsverbot" ([`ADR 0001`](../../adr/0001-documentation-and-planning-structure.md) §4).
  `vcs:`-Block (`paths: docs/plan/adr/[0-9]*.md`, `immutable-when: '^\*\*Status:\*\* Accepted'`,
  `head-allow: Accepted|Superseded`) + Range-CI-Job (`make doc-immutable`).
  **C0-Owner-Entscheidung nötig:** Konflikt mit
  [`ADR 0028`](../../adr/0028-link-maintenance-accepted-adr-bezug.md) — Link-Pflege in
  Accepted-ADRs ist erlaubt, würde aber als `core-drift-vcs` flaggen. Optionen:
  (a) `exclude-sections` für link-tragende Abschnitte, (b) Link-Pflege-Marker,
  (c) Bezug-Abschnitt aus dem Core nehmen. → **eigener Slice** wegen des Amendments.

## Aktivierungs-Kriterium

C2/C3 beim nächsten Tooling-/Disziplin-Slice; C3 braucht die C0-Entscheidung zu
[`ADR 0028`](../../adr/0028-link-maintenance-accepted-adr-bezug.md).

## Wandert nach

`done/`, sobald `commits` (C2) und `vcs` (C3) scharf sind (bzw. bewusst verworfen);
C1 ist bereits geliefert.
