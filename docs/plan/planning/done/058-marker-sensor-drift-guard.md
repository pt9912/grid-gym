# 058 — Sensor-Marker-Drift-Guard (Meta-Test)

**Status:** Done — 2026-07-10
**Datum:** 2026-07-10
**Quelle:** [`054`](054-pytest-marker-drift-sensor-targets.md) Closure
(§CI-Anker „bewusst deferred") — Follow-up-Variante C: Rekurrenz-Schutz
ohne CI-Doppellauf.

---

## Kontext

Slice [`054`](054-pytest-marker-drift-sensor-targets.md) hat die
pytest-Marker-Drift behoben (`determinism`/`fault` sammelten 0 Tests →
pytest-Exit 5), aber die Reparatur war **nicht selbst-schuetzend**:
Faellt der letzte Traeger einer Marker-Familie weg, kehrt die stille
Drift zurueck — und weil die `make test-<marker>`-Targets in **keiner**
CI-Stage laufen (in 054 bewusst deferred, da die markierten Suiten
bereits ueber `make test-unit`/`gates` in CI abgedeckt sind), bliebe die
Wiederkehr unbemerkt.

## Lieferung

Neuer Meta-Test `tests/unit/test_sensor_marker_coverage.py`:

- liest die deklarierten Marker aus
  [`pyproject.toml`](../../../../pyproject.toml)
  `[tool.pytest.ini_options].markers` (Single-Source),
- scannt `tests/**` per statischem AST nach `pytest.mark.<name>`-Traegern
  (Modul-`pytestmark`, Dekorator, parametrisiert),
- faellt, sobald ein deklarierter Marker **keinen** Traeger mehr hat.

Scope-unabhaengig (anders als ein Session-Collection-Hook, der nur die
aktuelle Selektion sieht) und ohne verschachteltes pytest. Laeuft unter
`make test-unit`/`make gates` — also in CI — ohne die Determinismus-/
Fault-Suiten ein zweites Mal auszufuehren (kein CI-Zeit-Overhead).

## Verification-Evidence

- **Positiv:** aktueller Baum — deklariert `{determinism, replay, fault}`,
  alle drei mit Traeger; Meta-Test gruen.
- **Negativ (Guard feuert):** ein fingierter deklarierter Marker ohne
  Traeger wird als Waise erkannt → Test wuerde rot (Host-AST-Sanity vor
  Commit gefahren).
- `make gates` gruen (lint/format-check/typecheck/test-unit/coverage
  akzeptieren die neue Datei).
- `make docs-check` gruen.

## DoD

- [x] Meta-Test deckt alle deklarierten Marker ab (Single-Source pyproject).
- [x] Drift (Marker ohne Traeger) macht den Test rot — negativ verifiziert.
- [x] Kein Doppellauf der markierten Suiten; laeuft in `test-unit`/`gates`/CI.
- [x] Kein Runtime-Delta → kein Release (Test-only).

## Bezug

- [`054`](054-pytest-marker-drift-sensor-targets.md) (Marker-Sweep, Ursprung).
- Sensor-Familien: [`harness/replay.md`](../../../../harness/replay.md).
