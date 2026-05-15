# 001 — `docs/user/code-review.md` + PR-Template

**Status:** Next — Scope skizziert, M1-blockierend
**Datum:** 2026-05-15 (geoeffnet); Move `open/` → `next/`: 2026-05-15
Post-Acceptance nach Drittem Review.
**Quelle:** [`ADR 0002`](../../adr/0002-language-and-build-stack.md)
A-1 „Code-Review-Auflage (Reststeuerung fuer TABU-003)";
`pyproject.toml`-Folge-ADR-Pflicht (Post-Acceptance, ADR 0006 §3);
[`done/spike-0-results.md`](../done/spike-0-results.md) §6 Drittes
Review „Operative Folge-Pflichten".

---

## Trigger

`AC-ADAPTER-PURE` + `AC-ADAPTER-LIGHTWEIGHT` decken nur Import- und
strukturelle Aspekte von `GG-AR-TABU-003`. Fachliche Entscheidungen
direkt im Adaptercode sind statisch nicht voll erkennbar. ADR 0002
verlangt deshalb:

- Jede Adapter-PR enthaelt ein Review-Checklisten-Item „keine
  fachlichen Entscheidungen im Adapter" mit konkreter Begruendung der
  gewaehlten Mapping-Funktionen.
- Diese Review-Anforderung ist in `docs/user/code-review.md` und im
  PR-Template verankert.

## Erwartete Lieferung

- `docs/user/code-review.md` mit Review-Checkliste fuer:
  - TABU-003-Reststeuerung (fachliche Entscheidung im Adapter),
  - `GG-CC-001` Methoden-/Funktionsgroesse (Restanteil nach ruff),
  - `GG-CC-005` Naming-Konsistenz (Restanteil nach `ruff N`),
  - `GG-PRINC-002..005` SOLID-Restanteil,
  - **`pyproject.toml`-Folge-ADR-Pflicht**: jede Aenderung an
    `[tool.ruff.lint]`-`select`/`per-file-ignores`,
    `[tool.mypy] enable_error_code`/`files`,
    `[tool.importlinter]`-Contracts oder `[tool.grid_gym.arch_check]`-
    Whitelists braucht einen Verweis auf eine Folge-ADR (per
    ADR 0006 §3 weil ADR 0002 / ADR 0005 `Accepted` sind).
- `.github/PULL_REQUEST_TEMPLATE.md` (oder Gitea-Aequivalent) mit
  verlinkter Checkliste, inkl. expliziter Frage „beruehrt diese PR
  eine ADR-konforme Konfiguration? (Trigger fuer Folge-ADR?)".

## Aktivierungs-Kriterium

**Erfuellt** seit 2026-05-15 (Post-Acceptance): Scope ist skizziert
(siehe oben), Slice-Plan kann jederzeit starten. Spaetestens vor der
ersten Adapter-PR im M1-Slice.

## Wandert nach

- `in-progress/`, sobald aktive Slice-Arbeit beginnt,
- `done/`, sobald `docs/user/code-review.md` und PR-Template
  geliefert sind,
- `archive/`, falls eine Folge-ADR die Reststeuerung ersetzt.
