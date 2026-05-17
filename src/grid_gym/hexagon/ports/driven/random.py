"""RandomPort — deterministisch-reproduzierbare Zufalls-Quelle (`ADR 0007`).

Driven-Port-Vertrag fuer `GG-AR-PORT-DRN-010` (Lastenheft
`GG-SIM-001`, `GG-SCN-002`, `GG-SEED-001`): Fachlogik in
`hexagon/core/**` darf Zufall nur ueber `RandomPort` beziehen — nie
direkt aus `random.*`/`secrets.*`/`numpy.random.*` (`AC-NO-RAND`,
`ADR 0002 §A-1`).

Welle 2 liefert das Protocol und die konkrete
`MersenneTwisterRandomPort`-Implementation unter
`adapters/driven/random_mt/` (`ADR 0007 §5.2`/`§6`).
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Protocol


class RandomPort(Protocol):
    """Deterministisch-reproduzierbarer Zufalls-Port (`ADR 0007`).

    Vertrag (`ADR 0007 §5.1`):
    - `next_int` und `next_float` sind deterministisch ueber den
      internen Seed; gleicher Seed + gleiche Aufruf-Reihenfolge →
      identische Sequenz.
    - `sub_port(name)` erzeugt einen unabhaengigen Sub-Stream mit
      reproduzierbarem Sub-Seed; gleicher Parent-Seed + gleicher
      Sub-Name → gleicher Sub-Stream, unabhaengig von Parent-Calls.
    - `snapshot()` + adapter-spezifische `from_snapshot`-classmethod
      bilden den Resume-Vertrag (`GG-SIM-005`); der konkrete
      Konstruktor lebt am Adapter
      (`adapters.driven.random_mt.MersenneTwisterRandomPort.
      from_snapshot`), nicht hier — `AC-PORTS-NO-OUT` verbietet
      `ports → adapters`-Importe (`ADR 0007 §5.1`, geschaerft
      2026-05-17 bei Acceptance).
    """

    def next_int(self, low: int, high: int) -> int:
        """Liefert einen Integer in `[low, high]` (inklusive)."""
        ...  # pragma: no cover — Protocol-Stub

    def next_float(self) -> Decimal:
        """Liefert einen Decimal-Wert in `[0, 1)` mit maximal 6
        Nachkommastellen (`GG-DATA-005`-konform).

        Implementierungs-Vertrag (`ADR 0007 §5.2`):
        `Decimal(str(rng.random())).quantize(Decimal("0.000001"),
        rounding=ROUND_HALF_EVEN)`. Stabilitaet basiert auf
        CPythons `repr(float)`-Round-Trip (PEP 3101); auf
        Nicht-CPython-Runtimes nicht garantiert.
        """
        ...  # pragma: no cover — Protocol-Stub

    def sub_port(self, name: str) -> RandomPort:
        """Erzeugt einen unabhaengigen Sub-Port mit deterministischem
        Sub-Seed (`ADR 0007 §5.2`).

        Sub-Seed = SHA-256 ueber `f"{parent_seed}:{name}"`-UTF-8-
        Bytes; die ersten 16 Hex-Stellen als Integer (0..2^64-1)
        dienen als Sub-Seed. Gleicher Parent-Seed + gleicher
        Sub-Name → gleicher Sub-Stream, unabhaengig davon, wie
        viele Calls auf dem Parent vorher liefen.
        """
        ...  # pragma: no cover — Protocol-Stub

    def snapshot(self) -> bytes:
        """Serialisiert den internen Zustand als UTF-8-Bytes im
        `canonical_json`-Format (`ADR 0007 §5.2`, Snapshot-Schema
        per `ADR 0009`).

        Enthaelt mindestens: `version: int`, `seed`, `sub_path`,
        `rng_version`, `rng_state`. Der `version`-Schluessel folgt
        der M1-Welle-1-Konvention aus `SnapshotEnvelope` (jedes
        Sub-Snapshot-Dokument traegt `version: int`).

        Der Resume-Konstruktor `from_snapshot` lebt am konkreten
        Adapter (`adapters/driven/random_mt`), nicht hier —
        `AC-PORTS-NO-OUT` verbietet `ports → adapters`-Importe. Bei
        ADR-0007-Acceptance wurde §5.1 entsprechend geschaerft.
        """
        ...  # pragma: no cover — Protocol-Stub

    def snapshot_as_mapping(self) -> Mapping[str, object]:
        """Liefert den State im `SnapshotEnvelope`-tauglichen
        Mapping-Format (`ADR 0010`).

        Pflicht-Schluesselsatz identisch zu `snapshot()` (siehe
        `ADR 0009 §2`). Implementations MUESSEN sicherstellen,
        dass `canonical_json(port.snapshot_as_mapping()) ==
        port.snapshot()` gilt — d. h. beide Methoden lesen aus
        derselben internen Quelle (`_build_payload()`-Pattern).

        **Sequenz-Felder MUESSEN strukturell als `list[...]`
        typisiert sein** (nicht `tuple`), damit ein
        `==`-Vergleich gegen ein per `canonical_json` + `json.
        loads` rekonstruiertes Mapping symmetrisch bleibt
        (`TickLoop.from_snapshot` nutzt das fuer
        `TickLoopSnapshotRandomMismatchError`). `tuple`-Felder
        wuerden den Mismatch-Check still kollabieren lassen.

        Diese Methode ist die Composition-API fuer den
        `SnapshotEnvelope`; `snapshot()` bleibt fuer
        Disk-Persistenz und Resume.
        """
        ...  # pragma: no cover — Protocol-Stub
