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
# DeviceModel-Lifecycle (M2 Welle 1, ADR 0013 §2.6)
# ---------------------------------------------------------------------------


class DeviceLifecycleError(GridGymError):
    """Wurzel der `DeviceModel`-Lifecycle-Vertragsverletzungen.

    Aufrufer pruefen typisiert ueber `DeviceNotInitializedError`
    bzw. `DeviceAlreadyInitializedError`.
    """


class DeviceNotInitializedError(DeviceLifecycleError):
    """`tick(...)`/`apply_command(...)`/`device_id` ohne vorheriges
    `initialize(...)` aufgerufen.

    Welle-1-Review C-2: Devices implementieren das Lifecycle-Gate;
    TickLoop ruft `initialize(scenario_device, random)` einmal vor
    dem ersten Tick. Pre-init-Aufrufe der State-mutierenden
    Methoden sind ein Programmier-Fehler und werfen typed, statt
    still no-op zu sein.
    """

    def __init__(self, method_name: str) -> None:
        super().__init__(
            f"DeviceModel.{method_name}() called before initialize(); "
            "TickLoop must initialize the device before tick/apply_command/"
            "device_id access"
        )


class DeviceAlreadyInitializedError(DeviceLifecycleError):
    """`initialize(...)` ein zweites Mal aufgerufen.

    Devices sind nicht resettable per Protocol-Vertrag (ADR 0013
    §2.6). Reset-Workflow geht ueber Snapshot/Restore
    (`from_snapshot`-Classmethod), nicht ueber Doppel-`initialize`.
    """

    def __init__(self) -> None:
        super().__init__(
            "DeviceModel.initialize() called twice; devices are not "
            "resettable per ADR 0013 §2.6 — use from_snapshot() for resume"
        )


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

    Welle-0b-Review L-12: `super().__init__` folgt der C3-MRO
    (`RandomPortError` → `SnapshotFormatError` → `GridGymError`).
    `RandomPortError` definiert kein eigenes `__init__`, also greift
    `SnapshotFormatError.__init__(subsystem, message)` direkt — und
    ein zukuenftiger Init-Add an `RandomPortError` wuerde hier laut
    `TypeError` brechen, statt still uebersprungen zu werden.
    """

    def __init__(self, message: str) -> None:
        super().__init__("random_port", message)


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
    `super().__init__` folgt der C3-MRO — siehe Welle-0b-Review L-12
    in `RandomPortSnapshotFormatError`.
    """

    def __init__(self, message: str) -> None:
        super().__init__("scheduler", message)


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


class TickLoopStoppedError(TickLoopError):
    """`TickLoop.tick()` mit `_control_state` in `stopped`/`completed`
    (M5 Welle 4a, ADR 0039 Decision 13).

    Wirft auf, wenn der externe Tick-Driver-Task einen Tick auf
    einem bereits terminierten Run aufruft. Der HTTP-Adapter (M5
    Welle 4a) faengt das normalerweise NICHT (kein 4xx-Mapping
    noetig) — es ist Driver-Logik-Fehler; der Driver-Task soll
    den Loop verlassen, sobald `tick_loop.control_state` auf
    `stopped`/`completed` flippt.
    """

    def __init__(self, run_id: str, control_state: str) -> None:
        super().__init__(
            f"tick() called on terminated run {run_id!r} "
            f"(control_state={control_state!r}); "
            "driver task should exit the loop before calling tick()."
        )


class TickLoopInvalidTransitionError(TickLoopError):
    """`TickLoop.request_*` mit unerlaubtem State-Uebergang
    (M5 Welle 4a, ADR 0039 Decision 13).

    Transitions-Matrix: pause aus `pending`/`running` ok; resume aus
    `paused`/`pending` ok; stop aus jedem aktiven State ok;
    idempotente Wiederholungen auf demselben State sind no-op (kein
    Throw). Terminal-States `stopped`/`completed` lassen nur einen
    erneuten `stop`-Idempotenz-No-op zu.

    Der HTTP-Adapter (`_runs_action_router.py:post_run_control`)
    mapped diese Exception auf 409 Conflict mit `GG-API-004`-
    `ErrorResponse(code="invalid_transition")`.
    """

    def __init__(self, run_id: str, current_state: str, target_state: str) -> None:
        super().__init__(
            f"invalid run-control transition for {run_id!r}: {current_state!r} -> {target_state!r}"
        )
        self.run_id = run_id
        self.current_state = current_state
        self.target_state = target_state


class TickLoopUnknownDeviceTypeError(TickLoopError):
    """Welle-6a-Review M-6: TickLoop kennt keinen `device_type` fuer
    den uebergebenen `DeviceModel`-Klassen-Namen. Schreib-Pfad-
    Exception (im `snapshot()`-Pfad); semantisch getrennt von
    `TickLoopSnapshotWrongTypeError` (Lese-Pfad-Format-Verletzung)."""

    def __init__(self, class_name: str, known: tuple[str, ...]) -> None:
        super().__init__(
            f"TickLoop kennt keinen device_type fuer Klasse {class_name!r}. "
            f"Welle-7+/M3-Geraete muessen sich in _DEVICE_TYPE_BY_CLASS_NAME "
            f"registrieren. Bekannt: {sorted(known)}."
        )


class TickLoopSnapshotFormatError(TickLoopError, SnapshotFormatError):
    """Wurzel der TickLoop-Snapshot-Format-Vertragsverletzungen.

    Auspraegungen als Subklassen — Pattern-konsistent zu
    `SchedulerSnapshotFormatError` und
    `RandomPortSnapshotFormatError`. Generalisierung als Trigger 014
    in M2 Welle 0a abgeschlossen — Multi-Inheritance von
    `SnapshotFormatError`, `subsystem` ist auf `"tick_loop"` vorbelegt.
    `super().__init__` folgt der C3-MRO (siehe Welle-0b-Review L-12).
    """

    def __init__(self, message: str) -> None:
        super().__init__("tick_loop", message)


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
    """Snapshot traegt eine unbekannte `version`.

    ADR 0015 §2.4 Pflicht-Text fuer M2-Welle-6a-Reject: die Message
    nennt die gefundene und erwartete Version PLUS einen Verweis
    auf den M6-`GG-PERSIST-*`-Migrations-Slice, damit der Operator
    den Migrations-Pfad ohne ADR-Lesen findet.
    """

    def __init__(self, expected: int, found: object) -> None:
        super().__init__(
            f"TickLoop snapshot version={found!r} wird in M2-Welle-6a "
            f"nicht mehr gelesen (erwartet: {expected}). "
            f"Quellen: Lauf in M1 abgeschlossen oder Snapshot-"
            f"Migrations-Slice abwarten (M6, GG-PERSIST-*)."
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
    `super().__init__` folgt der C3-MRO (siehe Welle-0b-Review L-12).
    """

    def __init__(self, message: str) -> None:
        super().__init__("scenario", message)


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


class ScenarioUnknownDeviceTypeError(ScenarioError):
    """Welle-6b (ADR 0021 §2.2): `ScenarioDevice.type` ist in der
    Device-Factory-Map nicht registriert. Welle-7+/M3-Geraete
    muessen sich in `scenario.loader._DEVICE_FACTORIES` eintragen
    oder per `device_type`-Protocol-Property dispatchen."""

    def __init__(self, device_type: str, known: tuple[str, ...]) -> None:
        super().__init__(
            f"scenario references unknown device type {device_type!r}. "
            f"Welle-6b-Factory-Map kennt: {sorted(known)}."
        )


class ScenarioMissingSourceDeviceError(ScenarioError):
    """Welle-6b (ADR 0021 §2.2): SmartMeter's `aggregate_device_ids`
    referenziert eine Geraete-ID, die im Scenario nicht definiert
    ist. Fail-fast vor dem ersten Tick (statt
    `SmartMeterSourceMissingError` zur Laufzeit, ADR 0018 §2.4)."""

    def __init__(self, smart_meter_id: str, missing_source_id: str) -> None:
        super().__init__(
            f"SmartMeter {smart_meter_id!r} referenziert "
            f"aggregate_device_id {missing_source_id!r}, "
            f"das im Scenario nicht definiert ist."
        )


class ScenarioUnknownEventTargetError(ScenarioError):
    """Ein Event referenziert eine Geraete-ID, die nicht in
    `devices` definiert ist (`GG-SCN-008`)."""

    def __init__(self, target: str) -> None:
        super().__init__(f"scenario event targets unknown device: {target!r}")


class ScenarioUnknownFaultTargetError(ScenarioError):
    """Ein Fault referenziert eine Geraete-ID, die nicht in
    `devices` definiert ist (M3-Welle-1, ADR 0022 §2.3).

    Spiegelt das Pattern aus `ScenarioUnknownEventTargetError`:
    Fail-fast im Scenario-Validator (`_assert_fault_list`),
    bevor der TickLoop einen Fault auf ein nicht-existierendes
    Device anwenden koennte.
    """

    def __init__(self, target: str) -> None:
        super().__init__(f"scenario fault targets unknown device: {target!r}")


class ScenarioInvalidLoadTargetError(ScenarioError):
    """Welle-6b-Review M-6 (ADR 0021 §2.5 + §2.7):
    `LoadEvent.target_device_id` bzw. `LoadProfile.target_device_id`
    muss auf ein `LoadDevice` oder `GridConnectionDevice` zeigen
    (die einzigen legitimen Overlay-Ziele). Andere Geraete-Typen
    (PV/Battery/SmartMeter) sind unzulaessig — Fail-fast im
    Builder, statt zur Laufzeit `apply_command(set_power_kw)` an
    den falschen Typ zu liefern."""

    def __init__(self, source: str, target_id: str, target_type: str) -> None:
        super().__init__(
            f"{source} target_device_id={target_id!r} verweist auf "
            f"Geraete-Typ {target_type!r}; erlaubt sind nur "
            "LoadDevice und GridConnectionDevice "
            "(Welle-6b-Review M-6, ADR 0021 §2.5/§2.7)."
        )


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
    `super().__init__` folgt der C3-MRO (siehe Welle-0b-Review L-12).
    """

    def __init__(self, message: str) -> None:
        super().__init__("replay", message)


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


# ---------------------------------------------------------------------------
# Fault-Injection (M3 Welle 2, ADR 0022 §2.4 / ADR 0025 §2.1)
# ---------------------------------------------------------------------------


class FaultPortError(GridGymError):
    """Wurzel der `FaultPort`-Vertragsverletzungen
    (`GG-FAULT-001..010`).

    ADR 0022 §2.4 Exception-Propagation-Vertrag: Adapter-Fehler
    propagieren ungewrappt aus `TickLoop.tick()` heraus. Welle-2-
    Adapter werfen typisierte Subklassen, damit Aufrufer auf der
    Hexagon-Boundary differenzieren koennen.
    """


class FaultUnsupportedTypeError(FaultPortError):
    """Ein Adapter erhaelt `fault_type`, den er nicht versteht.

    Welle-2-Pattern: Battery-Adapter unterstuetzt `cell_failure`;
    Grid-Adapter unterstuetzt `voltage_drop`. Andere Typen werfen
    typisiert ab, ohne den Tick zu beschaedigen (Aufrufer
    entscheidet Fail-Fast vs. Alarm).
    """

    def __init__(self, adapter: str, fault_type: str) -> None:
        super().__init__(f"fault adapter {adapter!r} does not support fault_type {fault_type!r}")


class FaultInvalidPayloadError(FaultPortError):
    """Ein Adapter erhaelt Payload, dessen Struktur nicht zum
    `fault_type` passt (z. B. `cell_failure` ohne
    `affected_cell_index` oder mit Falsch-Typ-Wert).

    ADR 0025 §2.1 (`manual-via-command`-Pfad) verlangt typisiertes
    Fail-Fast bei Payload-Schema-Verletzungen.
    """

    def __init__(self, fault_type: str, detail: str) -> None:
        super().__init__(f"fault {fault_type!r} payload invalid: {detail}")


class FaultUnknownReferenceError(FaultPortError):
    """`manual-recover-fault`-Command zeigt auf eine unbekannte
    `(fault_id, target_device_id)`-Kombination (ADR 0025 §2.1).
    """

    def __init__(self, fault_id: str, target_device_id: str) -> None:
        super().__init__(
            f"manual-recover-fault references unknown "
            f"(fault_id={fault_id!r}, target_device_id={target_device_id!r})"
        )


# ---------------------------------------------------------------------------
# Multi-Agent-Bus (M3 Welle 3, ADR 0023 §2.2 + §2.6)
# ---------------------------------------------------------------------------


class AgentBusError(GridGymError):
    """Wurzel der `AgentMessageBus`-/`Agent`-Vertragsverletzungen
    (`GG-AGENT-001..008`).

    ADR 0023 §2.4 Exception-Propagation-Vertrag: Agent-Fehler
    propagieren ungewrappt aus `TickLoop.tick()` heraus
    (analog Welle-1-FaultPort-Pattern). Welle-4-Implementer
    werfen typisierte Subklassen, damit Aufrufer an der
    Hexagon-Boundary differenzieren koennen.

    **Welle-3-Surface** (Review-Folge L-4, 2026-05-21):
    `AgentBusInvalidSequenceError` (Sentinel-Vertrag-Defense)
    + `AgentBusInvalidReceiverError` (`drain_for("*")`-Guard).
    Welle 4 ergaenzt um `AgentUnknownReceiverError` o. ae., wenn
    der `RuleBasedAgent`-Slice Validation an der Decision-Surface
    braucht. Die Basis-Klasse `AgentBusError` selbst wird in
    Welle 3 nur als Vererbungs-Wurzel referenziert (Snapshot-
    Format-Subklassen + Defensive-Validations).
    """


class AgentBusInvalidSequenceError(AgentBusError):
    """`AgentMessageBus.publish(...)` mit `message.sequence < -1`.

    ADR 0023 §2.2 fixiert `-1` als Sentinel fuer "Bus vergibt
    naechste freie Nummer"; `sequence >= 0` ist explizite
    Vergabe (Test-Code-Pfad). Werte `< -1` wuerden in der
    Sortier-Logik (`drain_for(...)` sortiert nach
    `(simulation_time, sender, sequence)`) vor den echten
    Sequenzen 0, 1, 2, ... landen und den Determinismus-
    Vertrag verzerren. Welle-3-Review-Folge L-2 (2026-05-21).
    """

    def __init__(self, sequence: int) -> None:
        super().__init__(
            f"AgentMessage.sequence must be -1 (sentinel) or >= 0 (explicit), got {sequence}"
        )


class AgentBusInvalidReceiverError(AgentBusError):
    """`AgentMessageBus.drain_for(receiver=...)` mit
    semantisch unzulaessigem Receiver.

    Welle-3-Vertrag (ADR 0023 §2.2 + Review-Folge L-3,
    2026-05-21): `receiver="*"` ist Broadcast-Adressierung
    **am Publish-Pfad** (`AgentMessage.receiver = "*"`),
    **nicht** am Drain-Pfad. Ein `drain_for("*")`-Aufruf wuerde
    nur Broadcasts liefern (nicht alles, wie ein Aufrufer
    intuitiv erwarten koennte) — wir verbieten den Aufruf
    typisiert.
    """

    def __init__(self, receiver: str) -> None:
        super().__init__(
            f"drain_for(receiver={receiver!r}) is not a valid query — "
            "'*' is publish-side broadcast, not drain-side wildcard"
        )


class AgentBusSnapshotFormatError(AgentBusError, SnapshotFormatError):
    """Wurzel der `AgentMessageBus`-Snapshot-Format-Verstoesse.

    Multi-Inheritance von `SnapshotFormatError` (M2 Welle 0a,
    Trigger 014); `subsystem` ist auf `"agent_bus"` vorbelegt.
    `super().__init__` folgt der C3-MRO — Pattern aus
    `RandomPortSnapshotFormatError`.
    """

    def __init__(self, message: str) -> None:
        super().__init__("agent_bus", message)


class AgentBusSnapshotNotAMappingError(AgentBusSnapshotFormatError):
    """`from_snapshot(state)` erhaelt einen Wert, der kein Mapping ist.

    Format-Pruefung VOR der `version`-Pruefung — analog
    `RandomPortSnapshotNotAnObjectError`.
    """

    def __init__(self, actual_type: str) -> None:
        super().__init__(f"snapshot must be a Mapping, got {actual_type}")


class AgentBusSnapshotMissingKeysError(AgentBusSnapshotFormatError):
    """Pflicht-Keys fehlen im AgentMessageBus-Snapshot.

    `sorted(missing)` defensiv (siehe
    `RandomPortSnapshotMissingKeysError`-Begruendung).
    """

    def __init__(self, missing: list[str]) -> None:
        super().__init__(f"missing agent_bus snapshot keys: {sorted(missing)}")


class AgentBusSnapshotWrongTypeError(AgentBusSnapshotFormatError):
    """Ein Snapshot-Key hat den falschen Typ."""

    def __init__(self, key: str, expected: str, actual: str) -> None:
        super().__init__(f"agent_bus snapshot key {key!r} must be {expected}, got {actual}")


class AgentBusSnapshotVersionError(AgentBusError):
    """AgentMessageBus-Snapshot traegt eine unbekannte `version`."""

    def __init__(self, expected: int, found: object) -> None:
        super().__init__(
            f"unsupported agent_bus snapshot version: expected {expected}, got {found!r}"
        )


# ---------------------------------------------------------------------------
# Agent-Registry (M3 Welle 4a, ADR 0026 §2.5)
# ---------------------------------------------------------------------------


class AgentRegistryError(GridGymError):
    """Wurzel der TickLoop-Agent-Registry-Vertragsverletzungen
    (M3 Welle 4a, ADR 0026 §2.5).

    Konstruktor-Vertrags-Probleme rund um die `agents`-Tuple
    (z. B. doppelte `agent_id`-Werte). Getrennt von
    `AgentBusError` (Bus-Vertrag) und
    `AgentCommandDrainError` (Schritt-A0-TickLoop-Vertrag).
    """


class AgentDuplicateIdError(AgentRegistryError):
    """Konstruktor erhaelt mehrere Agents mit gleichem `agent_id`.

    Welle-3-`_set_agents_for_testing(...)`-Helper hatte das
    bereits defensiv als ValueError abgefangen; Welle 4a hebt
    den Check in den produktiven TickLoop-Konstruktor und gibt
    ihm eine typisierte Subklasse.
    """

    def __init__(self, agent_id: str) -> None:
        super().__init__(f"TickLoop received duplicate agent_id: {agent_id!r}")


# ---------------------------------------------------------------------------
# Agent-Command-Drain (M3 Welle 4a, ADR 0026 §2.5)
# ---------------------------------------------------------------------------


class AgentCommandDrainError(TickLoopError):
    """Wurzel der TickLoop-Schritt-A0-Drain-Vertragsverletzungen
    (M3 Welle 4a, ADR 0026 §2.5).

    Drain-Pfad-Probleme (z. B. Pending-Command auf unbekanntes
    Device). Erbt von `TickLoopError`, weil Drain ein TickLoop-
    interner Schritt-Vertrag ist, kein `AgentMessageBus`-Fehler.
    """


class AgentInvalidCommandTargetError(AgentCommandDrainError):
    """Schritt A0v erkennt eine `target_device_id`, die im
    `_device_by_id`-Lookup nicht existiert.

    Atomizitaets-Vertrag (ADR 0026 §2.1): wird VOR
    `clock.advance(...)` und `scheduler.pop_due(...)` geworfen,
    damit der Tick komplett unangetastet bleibt. Pending-Buffer
    wird nicht geleert; Retry/Resume bleibt sauber moeglich.
    """

    def __init__(self, target_device_id: str, command_id: str) -> None:
        super().__init__(
            f"Schritt A0v: pending agent command targets unknown device "
            f"{target_device_id!r} (command_id={command_id!r})"
        )


# ---------------------------------------------------------------------------
# TickLoop-Agent-Foundation-State-Snapshot (M3 Welle 4a, ADR 0026 §2.6)
# ---------------------------------------------------------------------------


class TickLoopAgentSnapshotMissingKeysError(TickLoopSnapshotFormatError):
    """Pflicht-Keys fehlen im Agent-Foundation-State-Snapshot
    (z. B. `pending_agent_commands`-Sub-Snapshot ohne
    `commands`-Key).
    """

    def __init__(self, sub_snapshot: str, missing: list[str]) -> None:
        super().__init__(
            f"agent foundation sub-snapshot {sub_snapshot!r} missing keys: {sorted(missing)}"
        )


class TickLoopAgentSnapshotWrongTypeError(TickLoopSnapshotFormatError):
    """Ein Key im Agent-Foundation-State-Snapshot hat den
    falschen Typ (z. B. `pending_agent_commands.commands` ist
    kein Sequence).
    """

    def __init__(self, key: str, expected: str, actual: str) -> None:
        super().__init__(f"agent foundation snapshot key {key!r} must be {expected}, got {actual}")


class TickLoopAgentSnapshotInvalidCommandResultError(TickLoopSnapshotFormatError):
    """Ein Eintrag in `pending_agent_commands.commands` traegt
    einen unbekannten `CommandResult`-String beim Restore.

    Welle-4a-Snapshot-Vertrag (ADR 0026 §2.6): `result` wird
    als CommandResult-Stringwert serialisiert und beim Restore
    via `CommandResult(state["result"])` typisiert
    zurueckgeparst.
    """

    def __init__(self, index: int, raw_value: object) -> None:
        super().__init__(
            f"pending_agent_commands.commands[{index}].result is not a known "
            f"CommandResult string: {raw_value!r}"
        )


class TickLoopAgentSnapshotDeviceMismatchError(TickLoopSnapshotFormatError):
    """Injizierte Device-Instanz passt nicht zum vorhandenen
    `devices.<type>.<id>`-Sub-Snapshot (ADR 0026 §2.6
    Resume-Match-Check).

    Drei Mismatch-Achsen: Device-ID fehlt im Snapshot,
    Device-Typ stimmt nicht mit Snapshot-Key-Segment ueberein,
    oder `device.snapshot()` weicht vom persistierten Sub-
    Snapshot-State ab.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(f"agent-foundation resume device mismatch: {detail}")


class TickLoopAgentSnapshotGridModelMismatchError(TickLoopSnapshotFormatError):
    """Injiziertes `grid_model.snapshot()` passt nicht zum
    vorhandenen `grid_model`-Sub-Snapshot (ADR 0026 §2.6
    Resume-Match-Check)."""

    def __init__(self, detail: str) -> None:
        super().__init__(f"agent-foundation resume grid_model mismatch: {detail}")


class TickLoopAgentSnapshotLoadOverlayMismatchError(TickLoopSnapshotFormatError):
    """Injizierte `active_load_events`/`active_load_profiles`
    passen nicht zum persistierten GridModel-Overlay-State
    (ADR 0026 §2.6 Resume-Match-Check, ADR 0019 §6 GridModel-
    v2-Overlay-Snapshot).

    Nur aktiv, wenn ein `grid_model`-Sub-Snapshot vorhanden ist
    UND nicht-leere LoadOverlay-Tupel injiziert wurden.
    Overlay-only-Szenarien ohne GridModel sind weiter gueltig.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(f"agent-foundation resume load_overlay mismatch: {detail}")


# ---------------------------------------------------------------------------
# Welle-4b — Scenario-Agents-Block + RuleBasedAgent (M3 Welle 4b, ADR 0027)
# ---------------------------------------------------------------------------


class ScenarioUnknownAgentTypeError(ScenarioError):
    """ADR 0027 §2.2: `ScenarioAgent.type` ist in der
    Welle-4b-Agent-Factory-Map (`_AGENT_FACTORIES`) nicht
    registriert. Welle-4c+/M5-Agent-Typen muessen sich dort
    eintragen, analog `ScenarioUnknownDeviceTypeError`-Pattern.
    """

    def __init__(self, agent_type: str, known: tuple[str, ...]) -> None:
        super().__init__(
            f"scenario references unknown agent type {agent_type!r}. "
            f"Welle-4b-Factory-Map kennt: {sorted(known)}."
        )


class ScenarioUnknownAgentTargetError(ScenarioError):
    """ADR 0027 §2.2: Ein `params.target_device_id` eines Agents
    referenziert eine Geraete-ID, die nicht in `devices` definiert
    ist. Spiegelt das Pattern aus `ScenarioUnknownEventTargetError`
    + `ScenarioUnknownFaultTargetError`."""

    def __init__(self, agent_id: str, target: str) -> None:
        super().__init__(f"scenario agent {agent_id!r} targets unknown device: {target!r}")


class ScenarioInvalidRuleMetricError(ScenarioError):
    """ADR 0027 §2.3 Welle-4b-Metric-Whitelist: Ein `rules`-
    Eintrag eines `RuleBasedAgent` verwendet einen `metric`-Namen,
    der in Welle-4b nicht zulaessig ist.

    Welle-4b-Whitelist (context-basiert): `tick`, `simulation_time`.
    Telemetry-basierte Metrics (`state_of_charge_pct` u. ae.) sind
    Welle-4c+-Material und brauchen einen Telemetry-Forwarding-
    Mechanismus (siehe ADR 0027 §7).
    """

    def __init__(self, agent_id: str, metric: str, allowed: tuple[str, ...]) -> None:
        super().__init__(
            f"scenario agent {agent_id!r} rule metric {metric!r} not in "
            f"Welle-4b whitelist: allowed={sorted(allowed)}"
        )


class ScenarioInvalidRuleComparatorError(ScenarioError):
    """ADR 0027 §2.3: Ein `rules`-Eintrag verwendet einen
    `comparator`, der nicht in der deterministischen Liste
    `<`, `<=`, `==`, `!=`, `>=`, `>` ist."""

    def __init__(self, agent_id: str, comparator: str, allowed: tuple[str, ...]) -> None:
        super().__init__(
            f"scenario agent {agent_id!r} rule comparator {comparator!r} not "
            f"in allowed set: {sorted(allowed)}"
        )


class ScenarioInvalidAgentParamsError(ScenarioError):
    """ADR 0027 §2.3: `RuleBasedAgent.params` verstoesst gegen
    den Hybrid-Mutual-Exclusivity-Vertrag — entweder enthaelt
    der Block sowohl `rules` als auch `plugin` (Mutual-Exclusivity-
    Verstoss, Drift-Risiko), oder er enthaelt keines von beiden
    (kein Decision-Pfad, stiller No-op verboten).
    """

    def __init__(self, agent_id: str, detail: str) -> None:
        super().__init__(f"scenario agent {agent_id!r} params invalid: {detail}")


class ScenarioUnknownAgentPluginError(ScenarioError):
    """ADR 0027 §2.3: Ein `params.plugin`-Wert referenziert
    eine Plugin-Factory, die in `_AGENT_PLUGIN_FACTORIES` nicht
    registriert ist (Welle 4b leer; konkrete Plugins sind
    Welle 4c+ Material).
    """

    def __init__(self, agent_id: str, plugin: str, known: tuple[str, ...]) -> None:
        super().__init__(
            f"scenario agent {agent_id!r} plugin {plugin!r} not registered. "
            f"Known plugins: {sorted(known)}."
        )


class TickLoopAgentInstanceSnapshotMismatchError(TickLoopSnapshotFormatError):
    """ADR 0027 §2.4: Bidirektionaler Resume-Match-Check fuer
    `agents.<agent_type>.<agent_id>`-Sub-Snapshots —
    jeder injizierte Agent muss einen Snapshot-Slot haben, jeder
    Snapshot-Slot muss einen injizierten Agent haben (analog
    Welle-4a-Review-Folge `_assert_device_resume_match`,
    Commit `38272f6`).
    """

    def __init__(self, detail: str) -> None:
        super().__init__(f"agent-instance resume mismatch: {detail}")
