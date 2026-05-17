# 002 — `tools/check_refs.py` als Querverweis-Linter

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-15
**Quelle:** [`ADR 0004`](../../adr/0004-identifier-based-cross-references.md)
§3 (Retrofit-Regel), §4 (Konsequenzen)

---

## Trigger

ADR 0004 fordert Kennungs-basierte Querverweise (`GG-*`, `GG-AR-*`,
`AC-*`, ADR-Nummer). Bestehende `§…`-Verweise werden bei der
naechsten Beruehrung umgestellt. Eine Tool-Unterstuetzung ist
ausdruecklich als Folgearbeit erwaehnt:

> Dokumentations-Tooling (z. B. ein moeglicher `tools/check_refs.py`
> als Folgearbeit) kann spaeter ueber die Kennungen einen Index
> erzeugen und nicht aufgeloeste Verweise melden.

## Erwartete Lieferung

- `tools/check_refs.py`: scannt `spec/**.md` und `docs/plan/**.md`,
  extrahiert alle `GG-*`/`GG-AR-*`/`AC-*`/`ADR-NNNN`-Kennungen und
  meldet nicht aufgeloeste Verweise (Kennungen, die im Text
  referenziert werden, aber keine Definitionsstelle haben).
- Optional: Erkennung verbleibender `§…`-Verweise auf
  ID-tragende Sektionen.
- Aufruf als Quality-Gate im Makefile (`make docs-check` o. ae.).

## Aktivierungs-Kriterium

Sobald nach Spike-0 zwei oder mehr Fundstellen mit stillem
Querverweis-Drift beobachtet werden, oder spaetestens vor der
naechsten Minor-Versions-Hebung von `lastenheft.md` /
`architecture.md`.

## Wandert nach

- `next/`, sobald Spec-/Tooling-Sketch steht,
- `in-progress/`, wenn aktiver Slice geplant ist.
