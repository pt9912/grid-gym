# 013 — `diff_replay`-Tick-Mapping-Parameter (M2)

**Status:** Done — geschlossen 2026-05-18 in M2 Welle 2
(Commit `48f0106`). `diff_replay` traegt jetzt einen
`tick_ms: int = 1000`-Kwarg; der Battery-Pflicht-Test
`test_replay_diff_tick_ms.py` verifiziert die mechanische
Closure mit `tick_ms=100` und einem byte-stabilen Battery-Trace.
**Datum:** 2026-05-17 (geoeffnet aus Welle-5-Review SC-2).
**Quelle:** Welle-5-Review SC-2 (Commit `b2e1517`).
**Verlinkt:** `src/grid_gym/hexagon/core/replay/diff.py`
(heute mit `tick_ms`-Kwarg, `tick = simulation_time // tick_ms`),
`GG-REPLAY-007` (Diff-Akzeptanz nennt „Tick" ohne Skalen-
Festlegung), M1-Slice-Plan §3 Welle 5, M2-Slice-Plan §3 Welle 2.

---

## Closure-Notiz (M2 Welle 2, 2026-05-18)

**Lieferung im Repo:**

- `diff_replay(expected, actual, *, tick_ms=1000,
  volatile_fields=None) -> tuple[ReplayDelta, ...]`: neuer
  Pflicht-Kwarg `tick_ms` mit Welle-5-kompatiblem Default
  `1000` (keine Backward-Compat-Aenderung).
- `tick = sample.simulation_time // tick_ms` ersetzt die alte
  fixe `// 1000`-Division an allen drei Stellen
  (`_compare_sample` + zwei Laengen-Mismatch-Schleifen).
- `tick_ms <= 0` wirft `ReplayInvalidTickMsError` (typed,
  spiegelt das Mapper-Verhalten aus M1 Welle 5).
- Welle-2-Pflicht-Test
  `tests/unit/hexagon/core/devices/battery/test_replay_diff_tick_ms.py`
  pinnt:
  - Default `tick_ms=1000` unveraendert
    (`simulation_time=5000 → tick=5`).
  - `tick_ms=100` ergibt `simulation_time=500 → tick=5` (Trigger-
    013-Kernaussage).
  - `tick_ms <= 0` wirft typisiert.
  - Battery-Trace mit `tick_ms=100` ueber 10 Ticks → leerer Diff
    (`expected == actual` byte-stabil).
  - Drift-Battery-Trace (unterschiedliche initial_soc_pct) →
    fachliche Klassifikation pro Delta.

**Abnahme-Belege:**

- 380 Unit-Tests gruen (vorher 372).
- `make gates` cache-frei gruen.

**Erbschaft fuer Folgewellen:**

- Welle 5 Netzbilanzmodell und Welle 6 TickLoop-Integration
  koennen `diff_replay(..., tick_ms=...)` direkt nutzen, ohne
  den Default selbst nachbearbeiten zu muessen.
- `tick_ms=10` (`GG-SIM-002`-niedrigster zulaessiger Wert) ist
  jetzt sauber abbildbar.

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
