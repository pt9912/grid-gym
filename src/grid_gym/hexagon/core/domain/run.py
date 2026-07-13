"""Lauf-Metadaten (`GG-DATA-001`, `GG-SIM-003`, `GG-TERM-003`).

`RunMetadata` haelt die Reproduzierbarkeits-Metadaten eines
Simulationslaufs. Die Akzeptanz aus `GG-TERM-003` verlangt mindestens
Version, Szenario-Hash, Konfiguration, Startzeit im Simulationszeit-
modell, Seed, Tick-Groesse und aktivierte Adapter — seit Slice 038
(ADR 0073) sind alle Felder strukturiert: die vier Vollfelder
`platform_arch`/`enabled_adapters`/`sim_start_time`/`config_hash`
ergaenzen den Welle-1-Spine.

`started_at`/`ended_at` sind Wall-Clock-Zeiten in ISO-8601-UTC
(`GG-DATA-005`), nicht Simulationszeit. Simulationszeit wird in
`TelemetryPoint.simulation_time` als ganzzahlige ms gefuehrt.

`RunStatus` (M5 Welle 4a, ADR 0039 Decision 12) ist der orthogonale
Run-Lifecycle-State, der ausserhalb der Frozen-`RunMetadata` lebt:
das Repository haelt ihn als zweiten Lookup neben den Metadaten,
damit die Reproduzierbarkeits-Hash-Stabilitaet aus `RunMetadata`
nicht durch mutable Status-Felder gebrochen wird.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final, Literal

from grid_gym.hexagon.core.errors import (
    InvalidAdapterNameError,
    NonCanonicalEnabledAdaptersError,
    NonCanonicalPlatformArchError,
)


RunStatus = Literal["pending", "running", "paused", "stopped", "completed"]
"""Lifecycle-Status eines Simulationslaufs (M5 Welle 4a, ADR 0039
Decision 12).

- ``pending``  — Run persistiert, Tick-Driver noch nicht gestartet.
- ``running``  — Tick-Driver aktiv; ``tick()`` fortschreitet.
- ``paused``   — Tick-Driver aktiv, aber Pre-Tick-Guard blockt.
- ``stopped``  — Final-Terminierung durch Benutzer.
- ``completed``— Final-Terminierung durch Tick-Loop-Ende oder
  Lifespan-Shutdown.

Welle-1-`RunState`-Alias in `_schemas.py` zeigt auf denselben
Literal-Set (Re-Export). Die fuenf Werte sind die kanonische
Vokabel fuer alle Welle-4a-Schichten (Domain, Repository, HTTP-API,
UI-CSS-Klassen).
"""


ControlAction = Literal["start", "pause", "resume", "stop"]
"""Control-Action-Vokabel (M5-Welle-4a, ADR 0037 Decision API-1 + ADR
0039 Decision 13), gespiegelt aus dem HTTP-`ControlRequest`-Body.
Verschoben aus `core.simulation.tick_loop` in 041-C2 (ADR 0050 §2.3),
damit der `RunExecutionPort` sie ohne `core.simulation`-Import
referenzieren kann (`AC-ADAPTER-PURE`). `RunExecutionPort.request(action)`
und `TickLoop.request(action)` dispatchen ueber diesen Literal.
`start` (Slice 078, `GG-UI-004`): `pending → running`, nur aus `pending`
gueltig — schliesst die UI-„Start"-Luecke (der sanktionierte Literal-
Erweiterungs-Pfad, `ControlRequest`-Docstring)."""


@dataclass(frozen=True, slots=True)
class RunMetadata:
    """Metadaten eines reproduzierbaren Simulationslaufs.

    Felder:
    - `run_id`: stabile Lauf-Identitaet (UUID-String, Eingang).
    - `scenario_hash`: kanonischer Szenario-Hash (`GG-SCN-004`).
    - `schema_version`: Szenario-Schema-Version (z. B.
      `"grid-gym.scenario.v1"`).
    - `seed`: PRNG-Wurzelseed fuer `RandomPort` (`ADR 0007`).
    - `tick_ms`: Tick-Groesse in ms (10/100/1000 per `GG-SIM-002`).
    - `started_at`/`ended_at`: ISO-8601-UTC-Wall-Clock-Zeitstempel
      (`GG-DATA-005`); `ended_at` ist beim Lauf-Start typischerweise
      noch leer und wird erst beim Closure gesetzt — Welle 1
      modelliert nur den abgeschlossenen Eintrag.
      TODO(M1-Welle-7): in-flight-Repraesentation entscheiden —
      `ended_at: str | None` (Frozen-Equality-Verhalten beachten)
      vs. separate `RunMetadataInFlight`-Dataclass. Slice-Plan-
      Closure-Notiz traegt die Entscheidung.
    - `tool_version`: `grid_gym`-Version (Spec `GG-TERM-003`
      „Version").
    - `replay_of`: optionale, persistente Referenz auf den
      Lauf, dessen Replay dieser Lauf ist (Trigger 039 / ADR 0068).
      `None` = regulaerer Lauf (kein Replay). Die Bindung haengt
      damit auditierbar am Lauf statt nur als Runtime-Kwarg
      (`replay_reference_run_id`, ADR 0049 §2.2). Default `None`
      haelt bestehende Konstruktionen byte-stabil.
    - `platform_arch`: normalisierte Plattformarchitektur des
      ausfuehrenden Prozesses (Slice 038 / ADR 0073 §2.5;
      `canonical_platform_arch`, z. B. ``"x86_64"``). ``""`` =
      fehlend — der Replay-Preflight rejected fehlende Werte
      (ADR 0073 §2.6).
    - `enabled_adapters`: kanonisches Adapter-Profil des
      Composition Root (ADR 0073 §2.3;
      `canonical_enabled_adapters`: dedupliziert + lexikografisch
      sortiert). ``()`` = fehlend (Preflight-Reject, ADR 0073
      §2.6).
    - `sim_start_time`: Startzeit im Simulationszeitmodell in ms
      (ADR 0073 §2.2). Im heutigen tick-indizierten Modell
      strukturell die Konstante ``0`` (`simulation_time` ist „ms
      ab Lauf-Start"); variabel erst mit einem spaeteren
      Kalenderzeit-Modell (eigene Folge-ADR + Scenario-Schema-
      Bump).
    - `config_hash`: SHA-256-Hexdigest der versionierten
      ConfigView (ADR 0073 §2.4; `config_hash_for` in
      `core/serialization/config_view.py`). ``""`` = fehlend
      (Preflight-Reject, ADR 0073 §2.6).
    """

    run_id: str
    scenario_hash: str
    schema_version: str
    seed: int
    tick_ms: int
    started_at: str
    ended_at: str
    tool_version: str
    replay_of: str | None = None
    platform_arch: str = ""
    enabled_adapters: tuple[str, ...] = ()
    sim_start_time: int = 0
    config_hash: str = ""


SIM_START_TIME_ORIGIN: Final[int] = 0
"""Startzeit im Simulationszeitmodell (ms) des tick-indizierten
Zeitmodells (Slice 038 / ADR 0073 §2.2): `simulation_time` ist
definiert als „ms ab Lauf-Start", einen Kalenderzeit-Anker gibt es
nicht — die Startzeit ist damit strukturell ``0``. Konstruktions-
Stellen referenzieren diese Konstante statt eines Magic-Literals;
ein spaeteres Kalenderzeit-Modell macht den Wert per Folge-ADR
variabel."""


_ADAPTER_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"[a-z0-9_]+\Z")
"""Namensraum kanonischer Adapter-Namen (ADR 0073 §2.3): Package-
Namen unter `adapters/driven/` bzw. `adapters/driving/`. Der
Ausschluss von Kommata macht die komma-separierte Persistenz-Form
eindeutig."""


def canonical_platform_arch(raw: str) -> str:
    """Normalform der Plattformarchitektur (ADR 0073 §2.5).

    Trim + Lowercase ueber dem Rohwert (typisch
    ``platform.machine()`` des Composition Root — der Core selbst
    liest keine Umgebung). Ein leeres Ergebnis bedeutet „fehlend"
    und fuehrt im Replay-Preflight zum `missing`-Reject.
    """
    return raw.strip().lower()


def canonical_enabled_adapters(names: Iterable[str]) -> tuple[str, ...]:
    """Kanonisches Adapter-Profil (ADR 0073 §2.3).

    Validiert jeden Namen gegen ``[a-z0-9_]+`` (typisierter
    `InvalidAdapterNameError` sonst), dedupliziert und sortiert
    lexikografisch. Das leere Tupel ist zulaessig und bedeutet
    „fehlend" (Preflight-Reject, ADR 0073 §2.6).
    """
    for name in names:
        if _ADAPTER_NAME_PATTERN.fullmatch(name) is None:
            raise InvalidAdapterNameError(name)
    return tuple(sorted(set(names)))


@dataclass(frozen=True, slots=True)
class RunExecutionProfile:
    """Statisches Ausfuehrungs-Profil eines Composition Root
    (Slice 038 / ADR 0073 §2.3-§2.5).

    Traegt die drei composition-deklarierten `GG-TERM-002/003`-
    Vollfelder, die jede `RunMetadata`-Konstruktion dieses
    Entrypoints erbt. Der Default ist das **leere Profil**
    (Bare-Adapter-Entrypoint ohne Composition): dessen Laeufe
    werden im Replay-Preflight fail-closed rejected statt
    falsch-gruen verglichen.

    Kanonik-Zwang (Slice-038-Review-Folge): `__post_init__`
    validiert, dass `platform_arch` und `enabled_adapters` bereits
    in Normalform vorliegen — ein Composition Root, der die
    Kanonik-Funktionen umgeht, faellt fail-fast bei der
    Registrierung statt spaeter als False-Reject im Preflight.
    Das leere Profil bleibt gueltig (leer = fehlend).
    """

    platform_arch: str = ""
    enabled_adapters: tuple[str, ...] = ()
    config_hash: str = ""

    def __post_init__(self) -> None:
        if self.platform_arch != canonical_platform_arch(self.platform_arch):
            raise NonCanonicalPlatformArchError(self.platform_arch)
        if self.enabled_adapters != canonical_enabled_adapters(self.enabled_adapters):
            raise NonCanonicalEnabledAdaptersError(self.enabled_adapters)
