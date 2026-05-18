# 013 — `diff_replay`-Tick-Mapping-Parameter (M2)

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-17
**Quelle:** Welle-5-Review SC-2 (Commit `b2e1517`).
**Verlinkt:** `src/grid_gym/hexagon/core/replay/diff.py`
(heute `tick = simulation_time // 1000`), `GG-REPLAY-007`
(Diff-Akzeptanz nennt „Tick" ohne Skalen-Festlegung), M1-Slice-
Plan §3 Welle 5.

---

## Trigger

`diff_replay` setzt heute `tick = sample.simulation_time // 1000`
— ein impliziter Tick-pro-Sekunde-Mapping. Das ist nur fuer
`tick_ms=1000` korrekt. Bei den anderen erlaubten Werten aus
`GG-SIM-002` (10, 100) ist der `tick`-Wert Faktor 10 oder 100
daneben.

Heute (Welle 5) ist das per Docstring als „Aufrufer-Sache"
markiert. Aber `diff_replay` nimmt `tick_ms` nicht entgegen —
der Aufrufer kann den Default nicht reparieren, ohne den Diff
selbst nachzubearbeiten.

## Erwartete Lieferung

`diff_replay(expected, actual, *, tick_ms=1000,
volatile_fields=None) -> tuple[ReplayDelta, ...]`:

- Neuer Pflicht-Kwarg `tick_ms` mit Welle-5-kompatiblem Default
  `1000` (keine Backward-Compat-Bruch).
- `tick = sample.simulation_time // tick_ms`.
- Test, der bei `tick_ms=100` und `simulation_time=500` `tick=5`
  liefert (heutige Semantik wuerde `tick=0` liefern).

Optional: Type-Validierung `tick_ms > 0` analog zum Mapper
(`ReplayInvalidTickMsError`).

## Aktivierungs-Kriterium

Mit dem ersten Slice, der Replay-Diffs gegen `tick_ms != 1000`
produzieren muss — typischerweise M2-Geraetemodelle mit
hochfrequenten Telemetry-Streams (`tick_ms=10`).

## Wandert nach

- `next/`, sobald ein konkreter Slice (M2-Geraet, fault-injection)
  einen Replay-Diff mit nicht-1000-tick_ms triggert,
- `in-progress/`, wenn die Anpassung aktiv geplant ist.
