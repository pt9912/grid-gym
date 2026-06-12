# 009 — IEC-61850 In-Process-Smoke Reaktivierung

**Status:** Aufgeloest (M6-Welle-6-C2, 2026-06-08) — Pfad B
geliefert: NEU Dockerfile-Stage `iec61850-test` auf Python 3.12 +
`make test-iec61850` + versions-bedingter Skip-Marker
(`pytest.mark.skipif(sys.version_info >= (3, 13))`) statt
unconditional `skip`. Pattern verankert in ADR 0046
(Multi-Python-Test-Stage-Pattern). Pfad A (`pyiec61850-ng`
cp314-/ABI3-Wheel) bleibt die bevorzugte passive Endform — sobald
verfuegbar, faellt die Compat-Stage weg (Skip-Marker-Entfernung +
Stage-Removal als eigener `chore(deps)`-Slice).
**Datum:** 2026-06-01
**Quelle:** M4-Welle-5b-Closure (`ca96bca`) + Slice 033
([`../done/033-iec61850-adapter-review-folge.md`](033-iec61850-adapter-review-folge.md))
+ M4-Welle-6b-C3-Pfad-A-Probe-Run-Befund (Slice
[`../done/M4-welle-6b.md`](M4-welle-6b.md)).

---

## Trigger

`tests/integration/test_iec61850_in_process_smoke.py` ist seit
Welle 5b ueber `pytestmark = pytest.mark.skip(...)` deaktiviert
(2c-Mock-only-Fallback). Welle-6b-C3 hat dem Pfad-A
(Library-Upgrade) folgenden Probe-Run gemacht:

- PyPI-Stand 2026-06-01: `pyiec61850-ng==1.6.1.2` ist Latest
  (selbe Version wie Welle-5b-Closure-Pin).
- Wheel-Manifest fuer 1.6.1.2:
  ```
  pyiec61850_ng-1.6.1.2-cp310-cp310-win_amd64.whl
  pyiec61850_ng-1.6.1.2-cp311-cp311-win_amd64.whl
  pyiec61850_ng-1.6.1.2-cp312-cp312-win_amd64.whl
  pyiec61850_ng-1.6.1.2-cp313-cp313-win_amd64.whl
  pyiec61850_ng-1.6.1.2-cp314-cp314-win_amd64.whl
  pyiec61850_ng-1.6.1.2-cp39-cp39-win_amd64.whl
  pyiec61850_ng-1.6.1.2-py3-none-manylinux1_x86_64.whl
  ```
- **Befund:** Linux-Wheel ist ausschliesslich
  `py3-none-manylinux1_x86_64` (kein cp-Tag) — der Wheel
  enthaelt SWIG-Bindings, die intern an eine spezifische
  Python-ABI gebunden sind, ohne dass das Wheel-Manifest
  das markiert. **Konsequenz:** `pip install pyiec61850-ng`
  auf Python 3.14 zieht den vermeintlich Python-Version-
  agnostischen Wheel und segfaultet beim ersten SWIG-Call,
  weil die internen Bindings nicht passen.
- Pfad A (Library-Upgrade) ist **tot** mit dem aktuellen
  Library-Distribution-Stand.

Pfad B (Dockerfile-Python-3.12-Test-Stage) waere moeglich,
aber repo-novum (zweite Python-Version im Build-Layer,
separates uv-Lockfile-Handling). Welle-6b-C3-Entscheidung:
Pfad-B als eigenstaendiger Slice (eigener Trigger; eigener
ADR ob noetig), nicht im Welle-6b-Scope.

Pfad C (Mock-only-Defer) ist aktiv mit explizitem Trigger
(diese Datei).

## Reaktivierungs-Pfade

**Pfad A (passiv, bevorzugt) — Library publishet cp314-Wheel:**

- pyiec61850-ng publiziert eine Version >= 1.6.2 (oder 2.0.x)
  mit einem expliziten `cp314-cp314-manylinux*.whl` oder mit
  einem cp-getaggten ABI3-Wheel (`cp310-abi3-manylinux*`),
  das auf Python 3.14 stabil laeuft.
- Bestaetigung: `pip download pyiec61850-ng --python-version
  3.14 --platform manylinux2014_x86_64 --no-deps` liefert
  einen Wheel ohne `py3-none`-Tag.
- Dann: `pyproject.toml`-Pin von `>=1.6,<2.0` auf die neue
  Version aktualisieren (ggf. Pin-Range erweitern), Probe-
  Run gegen `pytest tests/integration/test_iec61850_*.py`
  in Python-3.14-Dockerfile-Stage. Bei Erfolg:
  `pytest.mark.skip` aufheben.

**Pfad B (aktiv, eigener Slice) — Dockerfile-Multi-Python:**

- Neuer Dockerfile-Stage `iec61850-integration-test` auf
  Python-3.12-Basis (statt Default-3.14).
- Separates uv-Lockfile fuer diesen Stage (oder Konstraint
  `--python 3.12` im uv-sync-Call) — Repo-Novum.
- `tests/integration/test_iec61850_*.py` laeuft nur in
  diesem Stage; der Default-`make test-integration` muss
  beide Stages koordinieren.
- Eventueller ADR 0036 wenn das Pattern repo-weit als
  „Library-Compat-Test-Stage"-Pattern wiederverwendet
  wird (z. B. fuer andere Library-Inkompats spaeter).
- Geschaetzter Aufwand: ~60 min Probe + 1-2 Tage Sauber-
  Slice.

**Pfad C (aktuell aktiv) — Mock-only-Fallback:**

- `tests/integration/test_iec61850_in_process_smoke.py`
  bleibt via `pytest.mark.skip(reason=...)` deaktiviert
  (Welle-6b-C3-Skip-Message ist die kanonische Form).
- 18 Mock-Client-Unit-Tests in
  `tests/unit/adapters/driven/protocol_iec61850/test_iec61850_protocol_port.py`
  decken Lifecycle + Read-Pfad + Error-Translation ab.
- Defer bis Pfad A oder Pfad B getriggert wird.

## Erwartete Lieferung bei Trigger

- Bei Pfad A: ein einzelner `chore(deps)`-PR mit Pin-Update
  + Skip-Marker-Entfernung + Smoke-Run-Beleg.
- Bei Pfad B: ein eigener Slice
  `036-iec61850-multi-python-test-stage.md` mit ADR-
  Material falls noetig + Dockerfile-Multi-Python-Setup.

## Konsequenz wenn ungelöst

- IEC-61850-Adapter laeuft seit Welle 5b nur via Mock-Smoke.
  Real-Library-Roundtrip ist via Probe-Run auf Python 3.12
  (manuell) bewiesen, aber nicht in CI.
- Wenn `pyiec61850-ng` einen API-Bruch zwischen 1.6.x und
  einer zukuenftigen Version macht, faellt der Adapter
  potenziell still auf Mock-Smoke zurueck ohne dass das
  Integration-Test-Gate es faengt.

## Bezuege

- M4-Welle-5b-Slice-Doc:
  [`../done/M4-welle-5b.md`](M4-welle-5b.md) §6
  Verifikationspfad.
- Slice 033 (IEC-61850-Review-Folge):
  [`../done/033-iec61850-adapter-review-folge.md`](033-iec61850-adapter-review-folge.md).
- M4-Welle-6b-Slice-Doc:
  [`../done/M4-welle-6b.md`](M4-welle-6b.md)
  §2 Scope-Item 4 (IedServer-Smoke-Reaktivierungs-Probe)
  + Risk-Section.
- ADR 0035 §2.5 (Mock-only-Fallback-Begruendung).
