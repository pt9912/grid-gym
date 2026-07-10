# 054 — pytest-Marker-Drift: `test-determinism`/`test-fault`/`test-replay`-Sensoren sammeln (fast) keine Tests

**Status:** Done — 2026-07-10 (Marker-Sweep geliefert; alle drei Sensoren nicht-leer gruen)
**Datum:** 2026-07-03
**Quelle:** Slice-038-C2-Verifikation
([`038-gg-term-002-003-full-equality-matrix.md`](038-gg-term-002-003-full-equality-matrix.md)):
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

---

## Closure 2026-07-10

Direkt aktiviert (Aktivierungs-Kriterium „Verifier-Lauf, der einen
Marker-Sensor als Closure-Beleg zitieren will" erfuellt). Rollen:
Implementation (Marker-Sweep) → Verifier (Sensoren + Gates).

**Geliefert — Marker-Zuordnungs-Sweep nach Modul-Zweck (17 Traeger):**

- `determinism` (5): `battery/test_determinism.py`,
  `simulation/test_scheduler.py`, `simulation/test_scenario_permutation.py`,
  `serialization/test_canonical.py`, `random_mt/test_mersenne_twister.py`.
- `fault` (12): `core/faults/test_{battery,grid,scenario}_fault_engine.py`,
  `core/faults/test_protocol.py`, `core/faults/test_recovery_window_property.py`,
  `devices/{battery,diesel_generator,ev_charger,grid_connection,transformer}/test_fault_injection.py`,
  `ports/driven/test_fault.py`,
  `http_api/test_fault_port_composition.py`.
- `replay` (unveraendert, 2 Traeger seit Slice 038 C2 / Slice 055):
  `simulation/test_tick_loop_replay_finalize.py`,
  `integration/test_slice_055_profile_preflight_e2e.py`.

**Verification-Evidence:**

- Sensoren nicht-leer gruen: `make test-determinism` = 117 passed
  (vorher pytest-Exit 5), `make test-replay` = 26 passed,
  `make test-fault` = 125 passed (vorher pytest-Exit 5).
- `make gates` gruen (alle 10 Pflicht-Gates inkl. `format-check`/`lint`).
- Marker sind **rein additiv**: `test-unit`/`coverage-gate` laufen
  `pytest tests/unit/` ohne Marker-Filter — kein Test verlaesst die
  Coverage-Erfassung durch die Marker.
- **Leerlauf-Schutz intakt:** die Dockerfile-Stages fahren
  `pytest -m <marker> tests/ -v`; bei 0 selektierten Tests bleibt
  pytest-Exit 5 → Stage rot → Target rot (Drift-Detektor unmaskiert).

**Harness-Sync:** [`harness/replay.md`](../../../../harness/replay.md)
Sensor-Familien-Tabelle nennt jetzt in der Evidence-Spalte den realen
Selektions-Scope je Marker (statt nur den Target-Namen).

**CI-Anker (Original-Body „Optional CI-Anker"): bewusst deferred.**
Die drei Marker-Targets laufen weiterhin in keiner CI-Stage — aber die
markierten Suiten laufen vollstaendig unter `make test-unit` (ohne
Marker-Filter), das Teil von `make gates`/`make ci`/CI ist. Die
Coverage-/Regressions-Absicherung ist damit in CI intakt; die
Marker-Targets sind diagnostische Sensoren, kein zusaetzlicher
CI-Coverage-Pfad. Eine dedizierte CI-Stage bleibt eine separate,
optionale Folgeentscheidung ohne akutes Drift-Risiko.

**Nicht im Scope:** breitere Marker-Vergabe an sekundaere Suiten
(Protocol-Codec-Roundtrips, Snapshot-Codec) — der Sweep markiert die
Suiten mit primaerem Determinismus-/Fault-Zweck; Grenzfaelle bleiben
`test-unit`-only.
