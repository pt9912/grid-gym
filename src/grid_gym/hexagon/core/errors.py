"""Wurzel- und Domain-Fehlerklassen (AC-TYPED-ERRORS).

`GridGymError` ist die Wurzel aller Domain-/Application-Fehler
(ADR 0002 §A-1). Konkrete Domain-Fehler, die zu einer Daten-/
Snapshot-Konvention gehoeren, liegen hier — nicht in
`hexagon/core/domain/`, weil AC-DOMAIN-FROZEN dort nur
Daten-Klassen (Frozen-Dataclasses, `FrozenModel`-Vererbung,
`Enum`-Subklassen) zulaesst. Exception-Klassen sind keine
Datenklassen, also lebt ihre Definition eine Ebene hoeher.
"""

from __future__ import annotations


class GridGymError(Exception):
    """Wurzel aller Domain- und Application-Fehler in `grid_gym`.

    AC-TYPED-ERRORS (ADR 0002 A-1) verlangt, dass alle Domain-/
    Application-Fehler von dieser Klasse erben. Adapter-spezifische
    Boundary-Translation-Module duerfen `Exception` fangen und auf
    Subklassen von `GridGymError` abbilden.
    """


# ---------------------------------------------------------------------------
# Generischer Snapshot-/Format-Codec (M2 Welle 0a, Trigger 014)
# ---------------------------------------------------------------------------
#
# Wurzel-Basis fuer alle strukturellen Format-Fehler (Snapshot, Schema,
# Replay-Parse) im Repo. Die fuenf M1-Per-Subsystem-Roots
# (`RandomPortSnapshotFormatError`, `SchedulerSnapshotFormatError`,
# `TickLoopSnapshotFormatError`, `ScenarioSchemaError`,
# `ReplayParseError`) erben via Multi-Inheritance von `SnapshotFormatError`,
# damit Aufrufer typisiert auf der Generic-Ebene catchen koennen, ohne
# pro Subsystem isinstance-Listen pflegen zu muessen. Bestehende Leaf-
# Klassen behalten ihre Konstruktor-Signatur und Message-Form
# byte-identisch — `subsystem` wird in der jeweiligen Per-Subsystem-Root
# vorbelegt und in der Instanz als `e.subsystem`-Attribut nachgewiesen.
#
# Neue Subsysteme (M2-Geraete) erben direkt von den generischen Kategorien
# (`MissingKeysError`, `WrongTypeError`, ...) oder konstruieren sie
# direkt mit `subsystem=...`.


class SnapshotFormatError(GridGymError):
    """Generische Wurzel fuer Format-/Strukturfehler in Snapshots, Schemas
    und Parse-Pfaden.

    `subsystem` traegt den Identifier des Codecs (z. B. `"random_port"`,
    `"scheduler"`, `"tick_loop"`, `"scenario"`, `"replay"`, neue
    M2-Geraete-Subsysteme wie `"battery"`, `"grid_model"`). Aufrufer
    pruefen typisiert (`isinstance(e, SnapshotFormatError)`) oder
    feingranular ueber Kategorie (`MissingKeysError`, `WrongTypeError`,
    ...). Welle-Inhalt: M2 Welle 0a (Trigger 014).
    """

    subsystem: str
    """Identifier des Codecs/Subsystems, der den Fehler ausgeloest hat."""

    def __init__(self, subsystem: str, message: str) -> None:
        self.subsystem = subsystem
        super().__init__(message)


class MissingKeysError(SnapshotFormatError):
    """Pflicht-Keys fehlen in einem Mapping.

    Generic — neue Subsysteme nutzen das direkt. Bestehende M1-Subklassen
    (`RandomPortSnapshotMissingKeysError`, `SchedulerSnapshotMissingKeysError`,
    `TickLoopSnapshotMissingKeysError`, `ScenarioMissingKeysError`)
    bleiben als typisierte Aliasse mit pre-belegtem `subsystem` erhalten.
    """

    def __init__(self, subsystem: str, missing: list[str]) -> None:
        super().__init__(subsystem, f"missing snapshot keys: {sorted(missing)}")


class WrongTypeError(SnapshotFormatError):
    """Ein Key hat den falschen Typ.

    Generic — neue Subsysteme nutzen das direkt. Bestehende M1-Subklassen
    (`RandomPortSnapshotWrongTypeError`, `SchedulerSnapshotWrongTypeError`,
    `TickLoopSnapshotWrongTypeError`, `ScenarioWrongTypeError`) bleiben
    erhalten.
    """

    def __init__(self, subsystem: str, key: str, expected: str, actual: str) -> None:
        super().__init__(subsystem, f"snapshot key {key!r} must be {expected}, got {actual}")


class ListItemWrongTypeError(SnapshotFormatError):
    """Ein Element in einer Snapshot-Liste hat den falschen Typ.

    Generic; bestehende `RandomPortSnapshotListItemWrongTypeError` bleibt
    Alias.
    """

    def __init__(self, subsystem: str, key: str, index: int, expected: str, actual: str) -> None:
        super().__init__(
            subsystem,
            f"snapshot key {key!r}[{index}] must be {expected}, got {actual}",
        )


class VersionError(SnapshotFormatError):
    """Snapshot/Schema traegt eine unbekannte `version`.

    Generic; bestehende `RandomPortVersionError`, `SchedulerSnapshotVersionError`,
    `TickLoopSnapshotVersionError`, `ScenarioUnsupportedSchemaVersionError`
    sind heute Geschwister-Klassen unter ihren Subsystem-Roots — sie
    bleiben dort, weil ihre Konstruktor-Signaturen voneinander abweichen.
    Neue M2-Subsysteme nutzen diese Basis direkt.
    """

    def __init__(self, subsystem: str, expected: object, found: object) -> None:
        super().__init__(
            subsystem,
            f"unsupported {subsystem} snapshot version: expected {expected!r}, got {found!r}",
        )


# ---------------------------------------------------------------------------
# Snapshot-Envelope-Vertrag (`hexagon.core.domain.snapshot`)
# ---------------------------------------------------------------------------


class SnapshotEnvelopeError(GridGymError):
    """Wurzel der Snapshot-Envelope-Vertragsverletzungen."""


class MissingSubSnapshotVersionError(SnapshotEnvelopeError):
    """Ein Sub-Snapshot-Dokument hat keinen `version`-Schluessel.

    Welle 1 fixiert die Konvention `version: int` in jedem Sub-
    Snapshot; Welle 4 verlaesst sich darauf, damit Resume-Pfade
    Schema-Drift ohne zentralen Mapper erkennen.
    """

    def __init__(self, sub_snapshot_name: str) -> None:
        super().__init__(
            f"sub-snapshot {sub_snapshot_name!r} is missing required "
            "'version: int' key (M1 Welle 1 convention)"
        )


class NonIntegerSubSnapshotVersionError(SnapshotEnvelopeError):
    """Der `version`-Schluessel eines Sub-Snapshots ist nicht `int`.

    `bool` ist `int`-Subklasse, wird hier aber explizit ausgeschlossen
    — Snapshot-Schema-Versionen sind aufsteigende Ganzzahlen, nicht
    Wahrheitswerte.
    """

    def __init__(self, sub_snapshot_name: str, value_type: str) -> None:
        super().__init__(
            f"sub-snapshot {sub_snapshot_name!r} has non-int 'version' (got {value_type})"
        )


# ---------------------------------------------------------------------------
# RandomPort-Snapshot-Vertrag (`ADR 0007 §5.2`,
# `adapters/driven/random_mt`)
# ---------------------------------------------------------------------------


class RandomPortError(GridGymError):
    """Wurzel der `RandomPort`-Vertragsverletzungen (`ADR 0007`)."""


class RandomPortVersionError(RandomPortError):
    """Snapshot traegt eine unbekannte `version` (`ADR 0007 §5.2`).

    Erwartete und vorgefundene Version werden mitgeschickt, damit
    Resume-Pfade in Logs / Errors klar erkennen, welches Schema
    erwartet wurde.
    """

    def __init__(self, expected: int, found: object) -> None:
        super().__init__(
            f"unsupported RandomPort snapshot version: expected {expected}, got {found!r}"
        )


class RandomPortSnapshotFormatError(RandomPortError, SnapshotFormatError):
    """Snapshot-Bytes sind strukturell nicht parsebar oder Pflicht-
    Keys fehlen / haben falsche Typen.

    Wird vor `RandomPortVersionError` ausgeloest, wenn die Bytes
    schon nicht als JSON-Objekt durchgehen. Konkrete Auspraegungen
    folgen als Subklassen — Aufrufer pruefen typisiert, nicht ueber
    Message-String-Matching.

    Multi-Inheritance von `SnapshotFormatError` (M2 Welle 0a,
    Trigger 014): Aufrufer koennen typisiert auch auf der generischen
    Ebene catchen. `subsystem` ist auf `"random_port"` vorbelegt.
    """

    def __init__(self, message: str) -> None:
        SnapshotFormatError.__init__(self, "random_port", message)


class RandomPortSnapshotInvalidBytesError(RandomPortSnapshotFormatError):
    """Snapshot-Bytes sind kein gueltiges UTF-8 oder kein JSON."""

    def __init__(self) -> None:
        super().__init__("snapshot bytes are not valid utf-8 JSON")


class RandomPortSnapshotNotAnObjectError(RandomPortSnapshotFormatError):
    """Snapshot-JSON ist kein Top-Level-Objekt (dict)."""

    def __init__(self, actual_type: str) -> None:
        super().__init__(f"snapshot must be a JSON object, got {actual_type}")


class RandomPortSnapshotMissingKeysError(RandomPortSnapshotFormatError):
    """Pflicht-Keys fehlen im Snapshot.

    Welle-0b-Review M-3: `sorted(missing)` ist defensiv — alle M1-
    Aufrufer geben bereits sortierte Listen, aber die Generic-
    Variante `MissingKeysError` sortiert ebenfalls; damit bleibt die
    Message-Form konsistent zwischen Leaf- und Generic-Variante,
    falls ein zukuenftiger Aufrufer die Sortier-Pflicht vergisst.
    """

    def __init__(self, missing: list[str]) -> None:
        super().__init__(f"missing snapshot keys: {sorted(missing)}")


class RandomPortSnapshotWrongTypeError(RandomPortSnapshotFormatError):
    """Ein Snapshot-Key hat den falschen Typ."""

    def __init__(self, key: str, expected: str, actual: str) -> None:
        super().__init__(f"snapshot key {key!r} must be {expected}, got {actual}")


class RandomPortSnapshotListItemWrongTypeError(RandomPortSnapshotFormatError):
    """Ein Element in einer Snapshot-Liste hat den falschen Typ."""

    def __init__(self, key: str, index: int, expected: str, actual: str) -> None:
        super().__init__(f"snapshot key {key!r}[{index}] must be {expected}, got {actual}")


class RandomPortSnapshotInvalidRngStateLengthError(RandomPortSnapshotFormatError):
    """`rng_state` hat nicht die fuer Mersenne-Twister erwartete Laenge.

    `random.Random.getstate()` liefert ein 625-Tupel (`ADR 0007 §5.2`):
    624 MT-Werte + 1 Index. Ein abweichend langer Snapshot wuerde
    `random.Random.setstate()` mit unkategorisiertem `ValueError`
    brechen — diese Pruefung faengt das frueh und typisiert.
    """

    def __init__(self, expected: int, actual: int) -> None:
        super().__init__(f"snapshot key 'rng_state' must have length {expected}, got {actual}")


class RandomPortRangeError(RandomPortError):
    """`next_int` mit ungueltigem Intervall (`low > high`).

    Konsistent zur `typed errors`-Linie (`AC-TYPED-ERRORS`): statt
    der `ValueError` aus `random.randint` faengt der Adapter den
    Programmierfehler typisiert ab. Untergrenze und Obergrenze
    werden mitgeschickt, damit Aufrufer in Logs sehen, woher die
    Vertauschung kam.
    """

    def __init__(self, low: int, high: int) -> None:
        super().__init__(f"next_int requires low <= high, got low={low}, high={high}")


class UnexpectedGaussNextError(RandomPortError):
    """`random.Random.getstate()` lieferte einen non-`None` `gauss_next`.

    `RandomPort.next_int`/`next_float` rufen niemals `gauss()` auf;
    ein non-`None`-Wert deutet auf externe Manipulation des
    Generators hin und wuerde den `canonical_json`-Pfad mit einem
    `float`-Wert brechen (`FloatNotAllowedError`).
    """

    def __init__(self, value_type: str) -> None:
        super().__init__(
            f"random.Random gauss_next must be None (got {value_type}); "
            "RandomPort API does not call gauss() — external manipulation?"
        )


# ---------------------------------------------------------------------------
# Scheduler-Vertrag (`hexagon.core.simulation.scheduler`, M1 Welle 3)
# ---------------------------------------------------------------------------


class SchedulerError(GridGymError):
    """Wurzel der `Scheduler`-Vertragsverletzungen (`GG-ARCH-006`)."""


class SchedulerDuplicateEventIdError(SchedulerError):
    """`Scheduler.add` mit einem `event_id`, der bereits in der Queue ist.

    Tie-Breaking `(time, priority, source, sequence, event_id)`
    haengt davon ab, dass `event_id` eindeutig ist — sonst kollidieren
    Sort-Keys und Pop-Reihenfolge wird vom Heap-Implementation-Detail
    abhaengig.
    """

    def __init__(self, event_id: str) -> None:
        super().__init__(f"duplicate event_id in scheduler queue: {event_id!r}")


class SchedulerSnapshotFormatError(SchedulerError, SnapshotFormatError):
    """Wurzel der Snapshot-Format-Vertragsverletzungen am `Scheduler`.

    Auspraegungen als Subklassen — Aufrufer pruefen typisiert,
    nicht ueber Message-String-Matching. Spiegelt das Pattern aus
    `RandomPortSnapshotFormatError` (`ADR 0009`).

    Multi-Inheritance von `SnapshotFormatError` (M2 Welle 0a,
    Trigger 014); `subsystem` ist auf `"scheduler"` vorbelegt.
    """

    def __init__(self, message: str) -> None:
        SnapshotFormatError.__init__(self, "scheduler", message)


class SchedulerSnapshotMissingKeysError(SchedulerSnapshotFormatError):
    """Pflicht-Keys fehlen im Snapshot-Dict.

    Welle-0b-Review M-3: `sorted(missing)` defensiv (siehe
    `RandomPortSnapshotMissingKeysError`-Begruendung).
    """

    def __init__(self, missing: list[str]) -> None:
        super().__init__(f"missing scheduler snapshot keys: {sorted(missing)}")


class SchedulerSnapshotWrongTypeError(SchedulerSnapshotFormatError):
    """Ein Snapshot-Key hat den falschen Typ."""

    def __init__(self, key: str, expected: str, actual: str) -> None:
        super().__init__(f"scheduler snapshot key {key!r} must be {expected}, got {actual}")


class SchedulerSnapshotEventFieldError(SchedulerSnapshotFormatError):
    """Ein Event-Eintrag in `pending_events` hat ein fehlendes oder
    falsch typisiertes Feld."""

    def __init__(self, index: int, field: str, expected: str, actual: str) -> None:
        super().__init__(
            f"scheduler snapshot pending_events[{index}] field {field!r} "
            f"must be {expected}, got {actual}"
        )


class SchedulerSnapshotVersionError(SchedulerError):
    """Snapshot traegt eine unbekannte `version`."""

    def __init__(self, expected: int, found: object) -> None:
        super().__init__(
            f"unsupported scheduler snapshot version: expected {expected}, got {found!r}"
        )


# ---------------------------------------------------------------------------
# TickLoop-Vertrag (`hexagon.core.simulation.tick_loop`, M1 Welle 4)
# ---------------------------------------------------------------------------


class TickLoopError(GridGymError):
    """Wurzel der `TickLoop`-Vertragsverletzungen (`GG-SIM-001`)."""


class TickLoopInvalidTickMsError(TickLoopError):
    """`TickLoop.__init__` mit nicht-positivem `tick_ms`.

    `GG-SIM-002` erlaubt 10/100/1000 ms (Policy-Whitelist beim
    Scenario-Loader); der Konstruktor prueft minimal `tick_ms > 0`,
    damit `clock.advance(tick_ms)` nicht versehentlich
    rueckwaerts laeuft.
    """

    def __init__(self, value: int) -> None:
        super().__init__(f"tick_ms must be positive, got {value}")


class TickLoopSnapshotFormatError(TickLoopError, SnapshotFormatError):
    """Wurzel der TickLoop-Snapshot-Format-Vertragsverletzungen.

    Auspraegungen als Subklassen — Pattern-konsistent zu
    `SchedulerSnapshotFormatError` und
    `RandomPortSnapshotFormatError`. Generalisierung als Trigger 014
    in M2 Welle 0a abgeschlossen — Multi-Inheritance von
    `SnapshotFormatError`, `subsystem` ist auf `"tick_loop"` vorbelegt.
    """

    def __init__(self, message: str) -> None:
        SnapshotFormatError.__init__(self, "tick_loop", message)


class TickLoopSnapshotMissingKeysError(TickLoopSnapshotFormatError):
    """Pflicht-Keys fehlen im TickLoop-Snapshot-Dict.

    Welle-0b-Review M-3: `sorted(missing)` defensiv (siehe
    `RandomPortSnapshotMissingKeysError`-Begruendung).
    """

    def __init__(self, missing: list[str]) -> None:
        super().__init__(f"missing tick_loop snapshot keys: {sorted(missing)}")


class TickLoopSnapshotWrongTypeError(TickLoopSnapshotFormatError):
    """Ein TickLoop-Snapshot-Key hat den falschen Typ."""

    def __init__(self, key: str, expected: str, actual: str) -> None:
        super().__init__(f"tick_loop snapshot key {key!r} must be {expected}, got {actual}")


class TickLoopSnapshotVersionError(TickLoopError):
    """Snapshot traegt eine unbekannte `version`."""

    def __init__(self, expected: int, found: object) -> None:
        super().__init__(
            f"unsupported tick_loop snapshot version: expected {expected}, got {found!r}"
        )


class TickLoopSnapshotClockMismatchError(TickLoopError):
    """Beim Resume zeigt die injizierte `clock` nicht auf
    `state['simulation_time']`.

    Aufrufer-Pflicht: clock vor `from_snapshot` so vorbereiten,
    dass `clock.now() == state['simulation_time']`. Ein
    Mismatch faellt typisiert auf und vermeidet stille
    Determinismus-Drift.
    """

    def __init__(self, expected: int, actual: int) -> None:
        super().__init__(
            f"clock state mismatch on resume: expected clock.now() == {expected}, got {actual}"
        )


class TickLoopSnapshotRandomMismatchError(TickLoopError):
    """Beim Resume liefert die injizierte `random` nicht den
    persistierten Sub-Snapshot.

    Aufrufer-Pflicht: `random` so injizieren, dass
    `random.snapshot_as_mapping() == state['sub_snapshots']
    ['random_root']`. Mismatch faellt typisiert auf, damit
    Resume-Inkonsistenz nicht zu stiller Drift wird.
    """

    def __init__(self) -> None:
        super().__init__(
            "random state mismatch on resume: injected RandomPort does "
            "not match the persisted snapshot"
        )


# ---------------------------------------------------------------------------
# Scenario-Vertrag (`hexagon.core.scenario`, M1 Welle 5)
# ---------------------------------------------------------------------------


class ScenarioError(GridGymError):
    """Wurzel der `Scenario`-Validierungs-Vertragsverletzungen
    (`GG-SCN-008`)."""


class ScenarioSchemaError(ScenarioError, SnapshotFormatError):
    """Wurzel der Schema-Format-Verstoesse beim Loader-Eingang.

    Subklassen tragen den konkreten Verstoss; Aufrufer pruefen
    typisiert, nicht ueber Message-String-Matching.

    Multi-Inheritance von `SnapshotFormatError` (M2 Welle 0a,
    Trigger 014); `subsystem` ist auf `"scenario"` vorbelegt.
    """

    def __init__(self, message: str) -> None:
        SnapshotFormatError.__init__(self, "scenario", message)


class ScenarioMissingKeysError(ScenarioSchemaError):
    """Pflicht-Keys fehlen im Szenario-Mapping.

    Welle-0b-Review M-3: `sorted(missing)` defensiv (siehe
    `RandomPortSnapshotMissingKeysError`-Begruendung).
    """

    def __init__(self, path: str, missing: list[str]) -> None:
        super().__init__(f"scenario {path!r}: missing keys {sorted(missing)}")


class ScenarioWrongTypeError(ScenarioSchemaError):
    """Ein Szenario-Key hat den falschen Typ."""

    def __init__(self, path: str, expected: str, actual: str) -> None:
        super().__init__(f"scenario {path!r} must be {expected}, got {actual}")


class ScenarioUnsupportedSchemaVersionError(ScenarioError):
    """`schema_version` ist nicht `grid-gym.scenario.v1` (Welle-5-
    Stand)."""

    def __init__(self, expected: str, actual: str) -> None:
        super().__init__(
            f"unsupported scenario schema_version: expected {expected!r}, got {actual!r}"
        )


class ScenarioDuplicateDeviceIdError(ScenarioError):
    """`devices`-Liste enthaelt eine doppelte `id` (`GG-SCN-008`).

    Geraete-IDs sind Pflicht-eindeutig, weil Tie-Breaking und
    Telemetry darauf fussen.
    """

    def __init__(self, device_id: str) -> None:
        super().__init__(f"duplicate device id in scenario: {device_id!r}")


class ScenarioUnknownEventTargetError(ScenarioError):
    """Ein Event referenziert eine Geraete-ID, die nicht in
    `devices` definiert ist (`GG-SCN-008`)."""

    def __init__(self, target: str) -> None:
        super().__init__(f"scenario event targets unknown device: {target!r}")


class ScenarioUnsupportedReplayFormatError(ScenarioError):
    """`scenario.replay.format` ist kein unterstuetzter Wert.

    `GG-REPLAY-001`-Akzeptanz nennt `csv` und `jsonl` als MVP-
    Formate. Welle 5 prueft strukturell auf `str`; diese
    Pruefung schaerft das semantisch.
    """

    def __init__(self, expected: tuple[str, ...], actual: str) -> None:
        super().__init__(f"scenario replay.format must be one of {expected}, got {actual!r}")


class ScenarioUnsupportedTimeMappingError(ScenarioError):
    """`scenario.replay.time_mapping` ist kein unterstuetzter Wert.

    `hexagon/core/replay/mapper.py` liefert die Strategien
    `monotonic` (ISO-8601-Deltas → ms) und `index` (`n * tick_ms`).
    Weitere Strategien brauchen einen Mapper-Erweiterung.
    """

    def __init__(self, expected: tuple[str, ...], actual: str) -> None:
        super().__init__(f"scenario replay.time_mapping must be one of {expected}, got {actual!r}")


# ---------------------------------------------------------------------------
# Replay-Vertrag (`hexagon.core.replay`, M1 Welle 5)
# ---------------------------------------------------------------------------


class ReplayError(GridGymError):
    """Wurzel der `Replay`-Vertragsverletzungen (`GG-REPLAY-001..007`)."""


class ReplayParseError(ReplayError, SnapshotFormatError):
    """Wurzel der Replay-Format-Verstoesse beim Mapper-Eingang.

    Multi-Inheritance von `SnapshotFormatError` (M2 Welle 0a,
    Trigger 014); `subsystem` ist auf `"replay"` vorbelegt.
    """

    def __init__(self, message: str) -> None:
        SnapshotFormatError.__init__(self, "replay", message)


class ReplayMissingFieldError(ReplayParseError):
    """Ein Replay-Sample-Eintrag hat ein fehlendes Pflichtfeld
    (`GG-REPLAY-001`)."""

    def __init__(self, line_index: int, field: str) -> None:
        super().__init__(f"replay sample at line {line_index}: missing required field {field!r}")


class ReplayInvalidValueError(ReplayParseError):
    """Ein Replay-Sample-Feld hat einen ungueltigen Wert."""

    def __init__(self, line_index: int, field: str, detail: str) -> None:
        super().__init__(f"replay sample at line {line_index}: field {field!r} invalid ({detail})")


class ReplayInvalidTickMsError(ReplayError):
    """`parse_csv`/`parse_jsonl` mit nicht-positivem `tick_ms`.

    Pattern-Parallel zu `TickLoopInvalidTickMsError`
    (`hexagon/core/simulation/tick_loop.py`): `tick_ms <= 0`
    wuerde bei `time_mapping="index"` alle Samples auf
    `simulation_time=0` setzen (stiller Tie-Breaking-Stress)
    und bei negativen Werten den Scheduler-Vertrag spaeter
    brechen. Welle-5-Review-MF-1.
    """

    def __init__(self, value: int) -> None:
        super().__init__(f"replay tick_ms must be positive, got {value}")


# ---------------------------------------------------------------------------
# RunRepository-Vertrag (`hexagon.ports.driven.run_repository`,
# M1 Welle 6b)
# ---------------------------------------------------------------------------


class RunRepositoryError(GridGymError):
    """Wurzel der `RunRepositoryPort`-Vertragsverletzungen
    (`GG-PERSIST-003`/`009`)."""


class RunNotFoundError(RunRepositoryError):
    """`RunRepositoryPort.get_by_id` mit unbekanntem `run_id`."""

    def __init__(self, run_id: str) -> None:
        super().__init__(f"run not found: {run_id!r}")


class RunAlreadyExistsError(RunRepositoryError):
    """`RunRepositoryPort.save` mit einer `run_id`, die bereits
    persistiert ist.

    Doppel-Inserts sind ein Programmierfehler — `run_id` ist als
    UUID4 generiert und kollidiert in der Praxis nicht. Diese
    Pruefung faengt versehentliche Re-Saves typisiert ab, bevor
    eine Postgres-`UNIQUE`-Constraint sie erst spaeter sichtbar
    macht.
    """

    def __init__(self, run_id: str) -> None:
        super().__init__(f"run already exists: {run_id!r}")
