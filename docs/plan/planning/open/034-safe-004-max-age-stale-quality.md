# 034 — `GG-SAFE-004` max_age-basierte STALE-Quality-Markierung (Lücke)

**Status:** Open — Substanz-Lücke aus M6-Welle-5a-Audit
**Datum:** 2026-06-06
**Quelle:** M6-Welle-5a-C2 (Quality-Pipeline-Audit; siehe
`docs/user/safe-001-004-quality-pipeline.md`).

---

## Lastenheft-Akzeptanz

`GG-SAFE-004` MUSS (Lastenheft Z. 1373-1378):

> Veraltete Daten MUESSEN markiert werden.
>
> Akzeptanz: Werte, deren Simulationszeitstempel die
> konfigurierte `max_age` ueberschreiten, erhalten
> deterministisch den Qualitaetsstatus `stale`.

## Substanz-Stand (Welle-5a-Audit 2026-06-06)

- **`Quality.STALE`-Enum-Wert existiert** seit M5-Welle-6b
  (`hexagon/core/domain/quality.py:24`); semantisch verankert,
  emittierbar von Adapter-Code.
- **`STALE`-Emission im Quality-Pipeline-Code: NICHT vorhanden.**
  Weder TickLoop noch `hexagon/core/devices/**`-Code haben
  `max_age`-Substanz oder eine Logik die `Quality.STALE` basierend
  auf einem Sim-Zeitstempel-Vergleich emittiert. Grep ueber
  `src/grid_gym/` nach `max_age` liefert null Treffer.
- **`max_age`-Konfigurationsfeld in Domain-Typen: NICHT
  vorhanden.** Weder `ScenarioDevice` noch `TelemetryPoint`
  haben ein `max_age`-Feld. Es gibt keinen Pfad zum
  Konfigurieren der Schwelle.
- **Test-Coverage: keiner Test verifiziert `GG-SAFE-004`.**

Welle-5a-C2-Smoke-Test (`tests/integration/test_m6_welle_5a_
safe_001_004_smoke.py::test_safe_004_stale_data_quality_after_
max_age`) ist deshalb `pytest.skip` mit Pointer auf diesen
Trigger.

## Erwartete Lieferung

Eigener Slice (M6-Welle-5a-Folge oder spaeter):

1. **`max_age`-Konfigurationsfeld** in `ScenarioDevice.params`
   oder als separates `TickLoop`-Konstruktor-Argument (oder
   pro Geraet/pro Metric — Design-Decision-pflichtig).
2. **`STALE`-Emission-Logik**: pro Tick prueft eine NEU
   Quality-Pipeline-Stage (oder eine bestehende Stage erweitert
   per Schaerfung), ob ein TelemetryPoint-Sim-Zeitstempel
   `(current_sim_time - point.simulation_time_ms) > max_age`
   ist; wenn ja, wird das emittierte Quality-Feld auf `STALE`
   geschoben.
3. **Determinismus-Garantie**: die Schwelle wird nur ueber
   Sim-Zeit gemessen, nicht ueber Wall-Clock — `AC-NO-TIME`
   bleibt im Core gewahrt.
4. **NEU Smoke-Test**: `tests/integration/test_safe_004_*`
   verifiziert end-to-end (Run mit max_age + alter Datenpunkt
   → erwartet `Quality.STALE`).
5. **Doku-Update** in `docs/user/safe-001-004-quality-pipeline.
   md` (Status-Spalte fuer SAFE-004 von „Lücke" auf
   „produktiv").

## Aktivierung

Aktivierung erfolgt bei einer der folgenden Bedingungen:

1. **Compliance-/Stakeholder-Druck** auf eine konkrete
   `max_age`-Schwelle (z. B. Demo-Audit verlangt das).
2. **M6-Welle-7-Closure-Sweep**-Material falls bis dahin
   nicht aufgeloest.
3. **Welle-X-Maintainer-Entscheidung** ohne externen Trigger.

## Konsequenz wenn ungeloest

- `GG-SAFE-004`-Akzeptanz bleibt **nicht produktiv erfuellt**.
- M6-Welle-5a `tests/integration/test_safe_004_*` bleibt
  `pytest.skip`.
- `docs/user/safe-001-004-quality-pipeline.md` zeigt SAFE-004
  als „Lücke" mit Pointer auf diesen Trigger.
- M6-Closure-DoD (`make gates` + `make fullbuild`) bleibt
  unbeeinflusst (`pytest.skip` ist nicht-blockierend).
- Lastenheft-Akzeptanz-Tabelle in `docs/user/`-Bereich zeigt
  die Lücke explizit; kein versteckter Drift.

## Bezuege

- [`../in-progress/M6-welle-5a.md`](../in-progress/M6-welle-5a.md)
  §3 Welle-5a-D-3 (Hybrid-Strategie: substantielle Lücken →
  `open/`-Trigger).
- [`../../../user/safe-001-004-quality-pipeline.md`](../../../user/safe-001-004-quality-pipeline.md)
  Audit-Tabelle mit Status-Spalte „Lücke" fuer SAFE-004.
- [`../../../../spec/lastenheft.md §20 GG-SAFE-004`](../../../../spec/lastenheft.md)
  — Lastenheft-Akzeptanz-Quelle.
- [`../../adr/0014-battery-snapshot-schema.md`](../../adr/0014-battery-snapshot-schema.md)
  + ADR 0016/0017/0018 — Device-Quality-Emission-Pattern
  (Vorbild fuer max_age-Stage).
