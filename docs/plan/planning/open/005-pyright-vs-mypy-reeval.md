# 005 — Re-Eval mypy vs. pyright bei generischen Protocols

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-15
**Quelle:** [`ADR 0005`](../../adr/0005-type-check-gate.md) §6

---

## Trigger

ADR 0005 waehlt `mypy --strict` als CI-Gate. Begruendung u. a.:
„`K-PROTO` (P0) ist bei `pyright` etwas besser, aber `mypy` reicht
fuer unsere Port-Strukturen (Driving/Driven-Ports sind eindeutige
Protocols, keine Generics-Akrobatik geplant). Re-Evaluation triggert,
sobald `ports/` generische Protocols mit Variance-Annotationen
einfuehrt."

## Erwartete Lieferung

- Pruefung, ob die Generic-Protocols mit `mypy` ohne Variance-
  False-Negatives validierbar sind.
- Falls nicht: Folge-ADR, die das CI-Gate von `mypy --strict` auf
  `pyright --strict` umstellt (oder `mypy` mit gehobenen
  `enable_error_code` ergaenzt).
- Pruefung der `K-DEPS`-Auflage (Node.js-Toolchain in CI) bei
  pyright-Wechsel.

## Aktivierungs-Kriterium

Sobald in `src/grid_gym/ports/**` der erste generische Protocol mit
Variance-Annotation (`Generic[T_co]`/`Generic[T_contra]`) eingefuehrt
wird.

## Wandert nach

- `next/`, sobald Variance-Bedarf konkret ist,
- `in-progress/`, wenn ADR-Schreibarbeit beginnt.
