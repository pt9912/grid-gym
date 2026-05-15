# 001 — `docs/user/code-review.md` + PR-Template

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-15
**Quelle:** [`ADR 0002`](../../adr/0002-language-and-build-stack.md)
A-1 „Code-Review-Auflage (Reststeuerung fuer TABU-003)"

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
  - `GG-PRINC-002..005` SOLID-Restanteil.
- `.github/PULL_REQUEST_TEMPLATE.md` (oder Gitea-Aequivalent) mit
  verlinkter Checkliste.

## Aktivierungs-Kriterium

Spaetestens vor der ersten Adapter-PR im Slice-M1.

## Wandert nach

- `next/`, sobald Scope-Skizze steht,
- `in-progress/`, wenn aktiver Slice geplant ist,
- `archive/`, falls eine Folge-ADR die Reststeuerung ersetzt.
