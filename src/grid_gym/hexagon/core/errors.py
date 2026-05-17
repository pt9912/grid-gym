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


class RandomPortSnapshotFormatError(RandomPortError):
    """Snapshot-Bytes sind strukturell nicht parsebar oder Pflicht-
    Keys fehlen / haben falsche Typen.

    Wird vor `RandomPortVersionError` ausgeloest, wenn die Bytes
    schon nicht als JSON-Objekt durchgehen. Konkrete Auspraegungen
    folgen als Subklassen — Aufrufer pruefen typisiert, nicht ueber
    Message-String-Matching.
    """


class RandomPortSnapshotInvalidBytesError(RandomPortSnapshotFormatError):
    """Snapshot-Bytes sind kein gueltiges UTF-8 oder kein JSON."""

    def __init__(self) -> None:
        super().__init__("snapshot bytes are not valid utf-8 JSON")


class RandomPortSnapshotNotAnObjectError(RandomPortSnapshotFormatError):
    """Snapshot-JSON ist kein Top-Level-Objekt (dict)."""

    def __init__(self, actual_type: str) -> None:
        super().__init__(f"snapshot must be a JSON object, got {actual_type}")


class RandomPortSnapshotMissingKeysError(RandomPortSnapshotFormatError):
    """Pflicht-Keys fehlen im Snapshot."""

    def __init__(self, missing: list[str]) -> None:
        super().__init__(f"missing snapshot keys: {missing}")


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


class SchedulerSnapshotFormatError(SchedulerError):
    """Wurzel der Snapshot-Format-Vertragsverletzungen am `Scheduler`.

    Auspraegungen als Subklassen — Aufrufer pruefen typisiert,
    nicht ueber Message-String-Matching. Spiegelt das Pattern aus
    `RandomPortSnapshotFormatError` (`ADR 0009`).
    """


class SchedulerSnapshotMissingKeysError(SchedulerSnapshotFormatError):
    """Pflicht-Keys fehlen im Snapshot-Dict."""

    def __init__(self, missing: list[str]) -> None:
        super().__init__(f"missing scheduler snapshot keys: {missing}")


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
