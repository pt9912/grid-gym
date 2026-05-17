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
