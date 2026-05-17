"""Mersenne-Twister-`RandomPort` (`ADR 0007 §5.2`).

Konkrete Driven-Adapter-Implementation des `RandomPort`-Protocols
auf Basis von `random.Random` (stdlib, Mersenne Twister) mit
SHA-256-Sub-Seeding und `canonical_json`-Snapshot-Format.

Snapshot-Schema (`version: 1`):

```json
{
  "version": 1,
  "seed": <int>,
  "sub_path": [<str>, ...],
  "rng_version": <int>,
  "rng_state": [<int>, ...]
}
```

`rng_gauss_next` ist absichtlich NICHT serialisiert: `next_int` und
`next_float` rufen niemals `random.gauss()` auf — `gauss_next`
bleibt also `None`. `snapshot()` validiert das defensiv und wirft
`UnexpectedGaussNextError`, falls jemand den Generator extern
manipuliert haben sollte. So bleibt der `canonical_json`-Pfad
float-frei (`FloatNotAllowedError`-Schutz).
"""

from __future__ import annotations

import hashlib
import json
import random as _random
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final

from grid_gym.hexagon.core.errors import (
    RandomPortSnapshotInvalidBytesError,
    RandomPortSnapshotInvalidRngStateLengthError,
    RandomPortSnapshotListItemWrongTypeError,
    RandomPortSnapshotMissingKeysError,
    RandomPortSnapshotNotAnObjectError,
    RandomPortSnapshotWrongTypeError,
    RandomPortVersionError,
    UnexpectedGaussNextError,
)
from grid_gym.hexagon.core.serialization.canonical import canonical_json

_SNAPSHOT_VERSION: Final[int] = 1
"""Schema-Version des `canonical_json`-Snapshot-Envelopes.

Eine Erhoehung bedeutet ein nicht-kompatibles Snapshot-Format und
braucht eine Folge-ADR zu `ADR 0007 §5.2`.
"""

_SUB_SEED_HEX_DIGITS: Final[int] = 16
"""Erste 16 Hex-Stellen aus SHA-256 — Sub-Seed-Wertebereich
`0..2^64-1` (ADR 0007 §5.2)."""

_QUANTUM_6_PLACES: Final[Decimal] = Decimal("0.000001")
"""Quantum fuer `next_float()` (6 Nachkommastellen, `GG-DATA-005`)."""

_RNG_STATE_LENGTH: Final[int] = 625
"""Mersenne-Twister-Statelaenge aus `random.Random.getstate()`.

624 MT-Werte + 1 Index — `ADR 0007 §5.2`. `from_snapshot` validiert
diese Laenge typisiert, damit `random.Random.setstate(...)` nicht
mit unkategorisiertem `ValueError` bricht.
"""


class MersenneTwisterRandomPort:
    """`RandomPort`-Implementation auf `random.Random`-Basis.

    Vertrag aus `ADR 0007 §5.1`/`§5.2`:
    - PRNG: `random.Random` (Mersenne Twister).
    - Sub-Seeding: SHA-256(`f"{parent_seed}:{name}"`) → erste 16
      Hex-Stellen als `int`.
    - `next_float`: `Decimal(str(rng.random()))
      .quantize(Decimal("0.000001"), ROUND_HALF_EVEN)`.

    TODO(M1-Welle-4): Snapshot-Codec (snapshot/from_snapshot) als
    eigene Klasse / Modul-Funktion abgrenzen, sobald der TickLoop-
    Snapshot-Envelope mehrere Sub-Snapshots versioniert
    zusammenfuehrt. Heute zwei fachliche Aenderungsgruende in einer
    Klasse (PRNG-Wahl + Snapshot-Schema), bei ~240 LOC noch
    vertretbar; bei Schema-v2 trennen.
    """

    def __init__(self, seed: int, sub_path: Sequence[str] = ()) -> None:
        """Initialisiert den Port mit `seed` als Wurzel.

        `sub_path` traegt den Pfad an Sub-Port-Namen vom Wurzel-
        Generator bis hierhin (leer fuer den Root-Port). Dient nur
        der Snapshot-Reproduzierbarkeit (`ADR 0007 §5.2`).
        """
        self._seed: int = seed
        self._sub_path: tuple[str, ...] = tuple(sub_path)
        self._rng: _random.Random = _random.Random(seed)  # noqa: S311 — Determinismus, nicht Krypto

    def next_int(self, low: int, high: int) -> int:
        """Integer in `[low, high]` (inklusive)."""
        return self._rng.randint(low, high)

    def next_float(self) -> Decimal:
        """Decimal in `[0, 1)` mit 6 Nachkommastellen.

        Quantisierungs-Vertrag aus `ADR 0007 §5.2`:
        `Decimal(str(rng.random())).quantize(...)`. `repr(float)`-
        Round-Trip-Annahme greift nur unter CPython 3.13+/3.14.
        """
        raw = self._rng.random()
        return Decimal(str(raw)).quantize(_QUANTUM_6_PLACES, rounding=ROUND_HALF_EVEN)

    def sub_port(self, name: str) -> MersenneTwisterRandomPort:
        """Erzeugt einen Sub-Port mit SHA-256-abgeleitetem Sub-Seed.

        Sub-Seed = `int(sha256(f"{self._seed}:{name}").hexdigest()[:16], 16)`.
        Reproduzierbar **unabhaengig** von Parent-Calls — Sub-Seed
        haengt nur von `self._seed` und `name` ab, nicht vom
        aktuellen `rng`-State (`ADR 0007 §4a AC4`).
        """
        digest = hashlib.sha256(f"{self._seed}:{name}".encode()).hexdigest()
        sub_seed = int(digest[:_SUB_SEED_HEX_DIGITS], 16)
        return MersenneTwisterRandomPort(sub_seed, sub_path=(*self._sub_path, name))

    def snapshot(self) -> bytes:
        """Serialisiert den State als `canonical_json`-Bytes.

        Schema siehe Modul-Docstring. Wirft
        `UnexpectedGaussNextError`, falls `gauss_next` nicht `None`
        ist — `next_int`/`next_float` setzen das nie, daher ist
        ein Non-`None`-Wert ein Hinweis auf externe Manipulation.
        """
        rng_version, rng_state, gauss_next = self._rng.getstate()
        if gauss_next is not None:
            raise UnexpectedGaussNextError(type(gauss_next).__name__)
        payload: dict[str, object] = {
            "version": _SNAPSHOT_VERSION,
            "seed": self._seed,
            "sub_path": list(self._sub_path),
            "rng_version": rng_version,
            "rng_state": list(rng_state),
        }
        return canonical_json(payload)

    @classmethod
    def from_snapshot(cls, state: bytes) -> MersenneTwisterRandomPort:
        """Stellt einen Port aus `snapshot()`-Bytes wieder her.

        `__init__` laeuft durch (mit dem persistierten Seed) — wenn
        spaetere Wellen dort Invarianten pruefen, greifen sie hier
        automatisch. Anschliessend ueberschreibt `setstate(...)`
        den RNG-State auf den persistierten Wert.

        Wirft `RandomPortSnapshotFormatError` (oder eine Subklasse)
        bei strukturell kaputten Snapshots und `RandomPortVersionError`
        bei unbekannter `version`.
        """
        parsed = _parse_snapshot_payload(state)
        if parsed.version != _SNAPSHOT_VERSION:
            raise RandomPortVersionError(_SNAPSHOT_VERSION, parsed.version)
        if len(parsed.rng_state) != _RNG_STATE_LENGTH:
            raise RandomPortSnapshotInvalidRngStateLengthError(
                _RNG_STATE_LENGTH, len(parsed.rng_state)
            )
        instance = cls(parsed.seed, sub_path=parsed.sub_path)
        instance._rng.setstate((parsed.rng_version, tuple(parsed.rng_state), None))
        return instance


@dataclass(frozen=True, slots=True)
class _ParsedSnapshot:
    """Geprueftes Snapshot-Payload (alle Pflicht-Keys typisiert).

    Liegt im Adapter, nicht in `hexagon/core/domain/` — AC-DOMAIN-
    FROZEN gilt nur dort, hier ist `frozen=True, slots=True` rein
    pragmatisch (Schreibschutz fuer parsed payload).
    """

    version: int
    seed: int
    sub_path: list[str]
    rng_version: int
    rng_state: list[int]


def _parse_snapshot_payload(state: bytes) -> _ParsedSnapshot:
    """Parsed `state` und validiert die Pflicht-Keys.

    `json.loads` ist hier zulaessig: `AC-NO-JSON` (`ADR 0002 §A-1`)
    verbietet nur `json.dumps`/`json.dump` ausserhalb der Whitelist.
    Decoder bleibt erlaubt — die Inverse des `canonical_json`-Pfads
    ist Adapter-Verantwortung.
    """
    try:
        raw = json.loads(state.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RandomPortSnapshotInvalidBytesError from exc
    if not isinstance(raw, dict):
        raise RandomPortSnapshotNotAnObjectError(type(raw).__name__)
    return _validate_parsed_keys(raw)


_REQUIRED_KEYS: Final[frozenset[str]] = frozenset(
    {"version", "seed", "sub_path", "rng_version", "rng_state"}
)


def _validate_parsed_keys(raw: dict[str, object]) -> _ParsedSnapshot:
    """Stellt sicher, dass alle Pflicht-Keys vorhanden und korrekt
    getypt sind. Wirft typisierte `RandomPortSnapshotFormatError`-
    Subklassen.
    """
    missing = _REQUIRED_KEYS - raw.keys()
    if missing:
        raise RandomPortSnapshotMissingKeysError(sorted(missing))
    return _ParsedSnapshot(
        version=_require_int(raw, "version"),
        seed=_require_int(raw, "seed"),
        sub_path=_require_list_of_str(raw, "sub_path"),
        rng_version=_require_int(raw, "rng_version"),
        rng_state=_require_list_of_int(raw, "rng_state"),
    )


def _require_int(raw: dict[str, object], key: str) -> int:
    value = raw[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise RandomPortSnapshotWrongTypeError(key, "int", type(value).__name__)
    return value


def _require_list_of_str(raw: dict[str, object], key: str) -> list[str]:
    value = raw[key]
    if not isinstance(value, list):
        raise RandomPortSnapshotWrongTypeError(key, "list", type(value).__name__)
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise RandomPortSnapshotListItemWrongTypeError(key, index, "str", type(item).__name__)
    return value


def _require_list_of_int(raw: dict[str, object], key: str) -> list[int]:
    value = raw[key]
    if not isinstance(value, list):
        raise RandomPortSnapshotWrongTypeError(key, "list", type(value).__name__)
    for index, item in enumerate(value):
        # bool ist int-Subklasse — explizit ausschliessen, damit
        # setstate keine bool-Werte ins Mersenne-Twister-Tupel
        # bekommt.
        if isinstance(item, bool):
            raise RandomPortSnapshotListItemWrongTypeError(key, index, "int", "bool")
        if not isinstance(item, int):
            raise RandomPortSnapshotListItemWrongTypeError(key, index, "int", type(item).__name__)
    return value


__all__ = ["MersenneTwisterRandomPort"]
