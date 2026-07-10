# 061 — GG-RT-006: Replay-Zeit-Multiplikatoren nicht implementiert (MUSS-Luecke)

**Status:** Open — MUSS-Luecke aus dem §27.2-Re-Sweep (Slice 060)
**Datum:** 2026-07-10
**Quelle:** Slice-060-Traceability-Audit gegen den Code-Stand M8/v0.3.1.

---

## Befund

[`GG-RT-006`](../../../../spec/lastenheft.md#gg-rt-006) (MUSS): „Replay-Modi
MUESSEN Zeitmultiplikatoren unterstuetzen" — Akzeptanz: Faktoren `0.5x`, `1x`,
`10x` und `unbounded` konfigurierbar. Der Tick-Loop laeuft heute ohne
Wall-Clock-Wait; die Frequenz ist Aufrufer-Sache
([`GG-SIM-007`](../../../../spec/lastenheft.md#gg-sim-007)). Es gibt **keine**
Multiplikator-Konfiguration im Run-/Replay-Pfad.

## Erwartete Lieferung

- Zeit-Multiplikator-Konfiguration (`0.5x/1x/10x/unbounded`) am Run-/Replay-Pfad
  — ADR fuer die Verortung (ClockPort-getriebenes Pacing vs. Driver-seitiges
  Sleep-Scaling).
- Determinismus-Vertrag: der Multiplikator aendert nur die Wall-Clock-Kadenz,
  nicht die deterministische Tick-Sequenz/Ausgabe.
- Tests: Pacing-Verifikation je Faktor + `unbounded` (so schnell wie moeglich).

## Aktivierungs-Kriterium

Naechster Slice am Run-/Replay-Pacing ODER wenn die MUSS-Abnahme formell
eingefordert wird.

## Wandert nach

`done/`, sobald die Multiplikatoren konfigurierbar sind und die zugehoerige
§27.2-Matrix-Zeile auf `✓` steht.
