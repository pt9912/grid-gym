# 014 — Generischer Snapshot-/Format-Codec (M2)

**Status:** Done — geschlossen 2026-05-18 in M2 Welle 0a
(Commit `3322cb8`).
**Datum:** 2026-05-17 — geoeffnet aus Welle-5-Review (SC-3 und
SC-4). Erbt + erweitert die Punkte aus
[`012-snapshot-composition.md`](012-snapshot-composition.md)
§2 (generischer Snapshot-Codec) und §3 (Payload-Canonical-Free-
Function), die Welle 4 explizit als „spaeter" verschoben hatte.
**Quelle:** Welle-3-Review N1/N2/N4, Welle-4-Review (Trigger 012
Closure), Welle-5-Review SC-3/SC-4.
**Verlinkt:** `hexagon/core/errors.py` (Zeilen 87-143
`RandomPortSnapshotFormatError`, 198-238 `SchedulerSnapshot*`,
277-330 `TickLoopSnapshot*`, 351-385 `ScenarioSchema*`, 396-430
`ReplayParse*`), `hexagon/core/scheduler.py::_assert_payload_
canonical` (Welle-3-Review S2 — heute scheduler-lokal), Welle-5-
Slice-Plan §3 Welle 5 Closure-Block.

---

## Closure-Notiz (M2 Welle 0a, 2026-05-18)

**Lieferung im Repo:**

- `hexagon/core/errors.py` traegt jetzt die generische Wurzel
  `SnapshotFormatError(GridGymError)` mit `subsystem: str`-
  Attribut, plus die Kategorien `MissingKeysError`,
  `WrongTypeError`, `ListItemWrongTypeError`, `VersionError`.
- Die fuenf Per-Subsystem-Roots
  (`RandomPortSnapshotFormatError`, `SchedulerSnapshotFormatError`,
  `TickLoopSnapshotFormatError`, `ScenarioSchemaError`,
  `ReplayParseError`) erben via Multi-Inheritance von
  `SnapshotFormatError` und legen `subsystem` ein-fuer-allemal vor.
  Leaf-Klassen-Konstruktoren bleiben byte-identisch.
- `hexagon/core/serialization/snapshot_codec.py` (neu) liefert die
  Free-Functions `assert_required_keys`, `assert_int`,
  `assert_mapping`, `assert_payload_canonical_compatible`. Letztere
  uebernimmt das Walk-Pattern aus
  `scheduler._assert_payload_canonical`.
- `hexagon/core/scenario/validator.py` ruft
  `assert_payload_canonical_compatible` an drei Stellen auf
  (`devices[].params`, `events[].payload`, `faults[].payload`) —
  Float-/Bytes-Injection wirft jetzt typisiert
  `WrongTypeError(subsystem="scenario", ...)` statt
  `FloatNotAllowedError` aus dem Hash-Encoder.

**Bewusst NICHT umgesetzt:**

- Item 5 der „Erwartete Lieferung" unten
  (`SnapshotEnvelope.__post_init__` zusaetzlich Payload-Canonical
  pruefen) ist additiv und kein Welle-0a-Pflicht-Punkt. Wird in
  M2 Welle 6 (TickLoop-Integration / `SnapshotEnvelope`-v1→v2-
  Bump) mitgenommen.
- `Scheduler._assert_payload_canonical` bleibt als private
  Helfer-Funktion im Scheduler — die Free-Function ist additiv,
  Scheduler-Tests bleiben byte-identisch gruen. Migration der
  M1-Module auf die Free-Functions ist ein separater
  Refactor-Slice, kein Welle-0a-Pflichtweg.

**Abnahme-Belege:**

- 265 Unit-Tests gruen (243 M1 + 22 neue Welle-0a-Tests).
- `make gates` gruen mit M1-Override-Liste + `core/serialization`
  (lint, format-check, typecheck, arch-check, test-unit,
  coverage-gate, coverage-gate-critical, dep-audit).
- Keine breaking changes: alle bestehenden Tests gruen ohne
  Anpassung; M1-Leaf-Konstruktoren byte-identisch.

**Erbschaft fuer Folgewellen:**

- M2 Welle 1+ (DeviceModel-Protocol, Battery, ...) konsumieren
  die generische Basis direkt — `subsystem="battery"`,
  `subsystem="pv"`, etc.
- `SnapshotEnvelope`-Versionsschritt v1 → v2 (M2 Welle 6,
  geplant in Slice-Plan) baut auf dem typisierten
  `VersionError` auf.

---

## Trigger

Fuenf Subsysteme mit nahezu wortgleichen `*FormatError`-Hierarchien:

| Subsystem      | Modul                                              | Errors                                                                                                          |
| -------------- | -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| RandomPort     | `adapters/driven/random_mt/`                       | `RandomPortSnapshotFormatError` + 6 Subklassen                                                                  |
| Scheduler      | `hexagon/core/simulation/scheduler.py`             | `SchedulerSnapshotFormatError` + 3 Subklassen + `SchedulerSnapshotVersionError`                                 |
| TickLoop       | `hexagon/core/simulation/tick_loop.py`             | `TickLoopSnapshotFormatError` + 2 Subklassen + `Version`/`ClockMismatch`/`RandomMismatch`                       |
| Scenario       | `hexagon/core/scenario/validator.py`               | `ScenarioSchemaError` + 4 Subklassen (`UnsupportedSchemaVersion`/`DuplicateDeviceId`/`UnknownEventTarget`)        |
| Replay         | `hexagon/core/replay/mapper.py`                    | `ReplayParseError` + 2 Subklassen + `InvalidTickMs`                                                              |

Plus: `Scheduler._assert_payload_canonical` (Welle-3-Review S2)
ist heute nur scheduler-lokal — Scenario-Loader (Welle 5)
duplicaiert das Risiko implizit (Float-Payload bricht erst beim
Hash-`canonical_json`), siehe Welle-5-Review MF-3.

## Erwartete Lieferung

In einem neuen Sub-Modul (z. B. `hexagon/core/serialization/
snapshot_codec.py` — neben dem bestehenden `canonical.py`):

1. **Generische Fehler-Hierarchie**: `SnapshotFormatError(GridGymError,
   subsystem: str)` plus Subklassen `MissingKeysError`,
   `WrongTypeError`, `ListItemWrongTypeError`,
   `VersionError` mit `subsystem`-Tag.
2. **Bestehende `*SnapshotFormatError`-Subklassen** bleiben als
   Backward-Compat-Aliase erhalten (z. B.
   `class RandomPortSnapshotMissingKeysError(MissingKeysError):
   def __init__(self, missing): super().__init__("random_port",
   missing)`). Test-Code, der heute `pytest.raises(
   RandomPortSnapshotMissingKeysError)` schreibt, bleibt
   funktional.
3. **Free-Functions**: `assert_required_keys(state, required,
   subsystem)`, `assert_int(value, key, subsystem)`,
   `assert_mapping(value, key, subsystem)`, etc. — heute pro
   Modul dupliziert.
4. **`assert_payload_canonical_compatible(payload, subsystem,
   path)`** als Free-Function, ausgelagert aus
   `Scheduler._assert_payload_canonical`. Wird im Scenario-Loader
   nach dem strukturellen Validator zusaetzlich aufgerufen, damit
   Float-Payloads typisiert (`ScenarioPayloadNotCanonicalError`
   o. ae.) statt aus dem Hash-Encoder kommen.
5. **`SnapshotEnvelope`-Schaerfung** (`done/012` §4): Welle-1-
   `SnapshotEnvelope.__post_init__` prueft zusaetzlich Payload-
   Canonical, nicht nur `version: int`-Anwesenheit.

Migration: alte Klassen-Namen via Alias erhalten, Welle-5-Tests
bleiben gruen. Neue Subsysteme (M2-Geraete) konsumieren nur die
generische Basis.

## Aktivierungs-Kriterium

Mit dem ersten M2-Geraetemodell, das einen eigenen
`*SnapshotFormatError` brauchen wuerde (Battery, PV, Smart Meter
etc.). Spaetestens, wenn ein sechster `*FormatError`-Block in
`errors.py` ansteht.

## Wandert nach

- `next/`, sobald M2 die Generalisierung als Slice aktiviert,
- `in-progress/`, wenn der Codec-Refactor begonnen wird,
- `done/`, sobald die Generalisierung samt Aliasen
  zurueckkommt und alle bestehenden Tests gruen sind.
