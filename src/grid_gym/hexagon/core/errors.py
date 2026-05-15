"""Wurzel-Fehlerklasse fuer Domain- und Application-Fehler (AC-TYPED-ERRORS)."""

from __future__ import annotations


class GridGymError(Exception):
    """Wurzel aller Domain- und Application-Fehler in `grid_gym`.

    AC-TYPED-ERRORS (ADR 0002 A-1) verlangt, dass alle Domain-/
    Application-Fehler von dieser Klasse erben. Adapter-spezifische
    Boundary-Translation-Module duerfen `Exception` fangen und auf
    Subklassen von `GridGymError` abbilden.
    """
