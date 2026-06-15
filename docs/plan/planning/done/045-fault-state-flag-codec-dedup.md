# Slice 045 — `fault_state`-Flag-Reader-Dedup (snapshot_codec)

**Status:** Done (geschlossen 2026-06-14) — verhaltensneutraler Refactor
aus der M8-Welle-2-Review-Folge. Loest die in
[`M8-welle-2a.md`](M8-welle-2a.md) §5 + [`M8-welle-2b.md`](M8-welle-2b.md)
§5 dokumentierte Deferral auf.

**Container:** [`roadmap.md`](../in-progress/roadmap.md) §4 M8. Kein neuer ADR — nutzt die
bestehende `snapshot_codec`-Infrastruktur (deren Modul-Docstring genau
das Sammeln N-fach duplizierter struktureller Reader vorsieht); keine
Vertragsaenderung, kein Verhaltens-Delta.

---

## 1. Lieferziel

Der optionale `fault_state`-Bool-Flag-Reader
([`ADR 0025`](../../adr/0025-fault-recovery-pattern.md) §2.2-Konvention)
war **viermal** wortgleich kopiert — Battery (`cell_failure_active`),
GridConnection (`voltage_drop_active`), EV-Charger
(`connection_loss_active`), Transformer (`winding_fault_active`). Dieser
Slice extrahiert das Muster in **einen** geteilten Helper und migriert
die vier Devices darauf.

## 2. DoD (≤ 3 beobachtbare Kriterien)

- [x] NEU `assert_optional_fault_flag(state, fault_state_key, flag_key,
      subsystem) -> bool` in
      [`snapshot_codec.py`](../../../../src/grid_gym/hexagon/core/serialization/snapshot_codec.py)
      (missing-block → False, missing-flag → False, non-bool →
      `WrongTypeError`).
- [x] Vier Device-Snapshots migriert (Inline-Block bzw. privater Reader
      `_connection_loss_from_state`/`_winding_fault_from_state` entfernt);
      **verhaltensneutral** — die vier `test_fault_injection.py`-Suites
      (fault-Roundtrip, fehlender/leerer Block → False, falsch-typisiert
      → `WrongTypeError`) bleiben unveraendert gruen.
- [x] `make gates` + `make docs-check` gruen (Helper-Branches durch die
      bestehenden Device-Tests abgedeckt; keine neuen Tests noetig, da
      kein neues Verhalten).

## 3. Lerneintrag (Closure-Pflicht)

**Geschaerfte Regel (Triggerschwelle 1×→2×→3×):** Das Muster haette beim
**dritten** Vorkommen (EV-Charger, Welle 2a) extrahiert werden sollen —
die Review-Folge hat es in 2a und 2b je als Deferral notiert, statt es
zu ziehen, sodass es auf vier Kopien wuchs. Konsequenz fuer die
device-iterierenden Folge-Wellen (2c Wind / 2d Diesel): **neue Geraete-
Snapshots nutzen `assert_optional_fault_flag` von Anfang an** — kein
fuenfter hand-gerollter Reader. Die „8-Naht"-Checkliste aus
[`M8-welle-2a.md`](M8-welle-2a.md) §4 wird entsprechend gelesen:
Naht (3)/Snapshot nutzt den geteilten Codec-Helper, nicht eine Kopie.
