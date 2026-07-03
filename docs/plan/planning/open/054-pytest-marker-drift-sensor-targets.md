# 054 — pytest-Marker-Drift: `test-determinism`/`test-fault`/`test-replay`-Sensoren sammeln (fast) keine Tests

**Status:** Open — Sensor-Drift-Befund aus Slice 038 C2
**Datum:** 2026-07-03
**Quelle:** Slice-038-C2-Verifikation
([`../in-progress/038-gg-term-002-003-full-equality-matrix.md`](../in-progress/038-gg-term-002-003-full-equality-matrix.md)):
`make test-replay` schlug mit pytest-Exit-Code 5 fehl (0 Tests
selektiert, 2522 deselektiert).

---

## Befund

[`pyproject.toml`](../../../../pyproject.toml) deklariert die drei
Marker `determinism`, `replay`, `fault`, und
[`harness/README.md`](../../../../harness/README.md) fuehrt
`make test-determinism` / `make test-replay` / `make test-fault`
als Sensor-Familien — aber **kein Testmodul traegt einen der drei
Marker** (Stand 2026-07-03; verifiziert per Grep ueber `tests/`).
Alle drei Make-Targets liefen damit ins Leere:

- `make test-replay` → pytest-Exit 5 (no tests collected) → Target rot.
- `make test-determinism` / `make test-fault` → identisch.

Die Determinismus-/Replay-/Fault-Suiten existieren real (z. B.
`test_tick_loop_replay_finalize.py`, Determinismus-Properties der
Geraete-Tests, Fault-Engine-Tests), laufen aber ausschliesslich
ueber `make test-unit`/`make gates`. Die Marker-Sensoren waren
damit **stille No-ops** — ein Verifier, der `make test-replay`
als Closure-Beleg zitiert haette, haette einen leeren Lauf zitiert.

**Teil-Fix in Slice 038 C2:** `test_tick_loop_replay_finalize.py`
traegt jetzt `pytestmark = pytest.mark.replay` — `make test-replay`
ist wieder gruen (erster Traeger). `determinism`/`fault` bleiben
ohne Traeger.

## Erwartete Lieferung

- Marker-Zuordnungs-Sweep: alle bestehenden Determinismus-,
  Replay- und Fault-Suiten unter `tests/unit/`/`tests/integration/`
  erhalten die passenden `pytestmark`-Zuordnungen (Kriterium:
  Modul-Zweck, nicht Datei-Name).
- Leerlauf-Schutz: die drei Make-Targets sollen bei 0 selektierten
  Tests weiterhin **rot** sein (pytest-Exit 5 nicht maskieren) —
  das ist der Drift-Detektor.
- Harness-Sync: [`harness/replay.md`](../../../../harness/replay.md)
  Sensor-Familien-Tabelle prueft, ob die Evidence-Spalte den
  realen Selektionsumfang nennt.
- Optional CI-Anker: Pruefung, ob die Marker-Targets in einer
  CI-Stage laufen sollen (heute laufen sie in keiner —
  deshalb blieb die Drift unbemerkt).

## Aktivierungs-Kriterium

Naechster Slice, der Determinismus-/Replay-/Fault-Substanz
anfasst, ODER der naechste Verifier-Lauf, der einen der drei
Marker-Sensoren als Closure-Beleg zitieren will.

## Wandert nach

- `next/`, sobald ein Slice die Zuordnungs-Sweep einplant,
- `done/`, wenn alle drei Sensoren nicht-leer gruen laufen.
