"""DNP3-Adapter-Profile-Konfiguration (M4 Welle 5a, ADR 0034 §2.1).

`Dnp3ProtocolPortConfig` ist eine frozen-dataclass mit dem inline-im-
`protocol_ports`-Block deklarierten Point-Schema (Decision D-a).
Pro `device_id` traegt `Dnp3PointConfig` Group + Variation + Index +
Access (Decision D-a/D-c). Validation-Errors werfen typed Sub-
Exceptions analog `ModbusConfigError`-Familie aus M4-Welle-3 +
`OpcuaConfigError`-Familie aus M4-Welle-4.

Welle-5a-Felder (`Dnp3ProtocolPortConfig`):

- `host` — DNP3-Outstation-Hostname (Default-frei; Pflicht).
- `port` — TCP-Port (Default `20000`; DNP3-Standard).
- `master_address` — Master-DNP3-Adresse (Default `1`).
- `outstation_address` — Outstation-DNP3-Adresse (Default `10`).
- `response_timeout_s` — Read-/Write-Timeout in Sekunden
  (Default `5.0`).
- `points` — Mapping `device_id` -> `Dnp3PointConfig`
  (Decision D-a inline-Schema). Mindestens ein Eintrag noetig.

Welle-5a-Felder (`Dnp3PointConfig`):

- `group` — DNP3-Object-Group (Pflicht; Welle-5a-Allow-List
  `{1, 30}`).
- `variation` — DNP3-Object-Variation (Pflicht; Welle-5a-Allow-
  List ist Group-spezifisch — siehe `_ALLOWED_GROUP_VARIATIONS`).
- `index` — Point-Index (Pflicht; nicht-negativ).
- `access` — `"read"` oder `"write"` (Welle-5a-Minimum: nur
  `"read"`; `"write"` ist Welle-6-Schaerfung — wird hier validiert
  aber im Port nicht produktiv ausgefuehrt).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal


_DEFAULT_PORT: Final[int] = 20000
_DEFAULT_MASTER_ADDRESS: Final[int] = 1
_DEFAULT_OUTSTATION_ADDRESS: Final[int] = 10
_DEFAULT_TIMEOUT_S: Final[float] = 5.0
_MIN_PORT: Final[int] = 1
_MAX_PORT: Final[int] = 65535
_MIN_ADDRESS: Final[int] = 0
_MAX_ADDRESS: Final[int] = 65535


# Welle-5a-Allow-List fuer Group/Variation-Tupel (ADR 0034 §2.3).
# Group 1/V1 = Binary Input single-bit; Group 1/V2 = Binary Input with
# flags; Group 30/V1 = 32-bit Integer Analog Input; Group 30/V5 = 32-bit
# Float Analog Input. Andere Groups/Variations bleiben
# Welle-6-Schaerfung (Counter, Outputs, Event-Classes).
_ALLOWED_GROUP_VARIATIONS: Final[frozenset[tuple[int, int]]] = frozenset(
    {
        (1, 1),
        (1, 2),
        (30, 1),
        (30, 5),
    }
)


class Dnp3ConfigError(ValueError):
    """Base-Klasse fuer `Dnp3ProtocolPortConfig`-Validation-Fehler
    (ADR 0034 §2.1).

    Erbt von `ValueError`, damit defensiv-coded Aufrufer den Standard-
    Konstruktor-Fehler-Pfad nicht aendern muessen. Konkrete Fehlerfaelle
    werfen Subklassen mit strukturierten Konstruktor-Parametern
    (TRY003-Konvention, Message-Bildung in Subklasse).
    """


class Dnp3ConfigEmptyFieldError(Dnp3ConfigError):
    """String-Pflichtfeld (`host`) ist leer."""

    def __init__(self, field_name: str) -> None:
        super().__init__(f"Dnp3ProtocolPortConfig.{field_name} darf nicht leer sein.")
        self.field_name: str = field_name


class Dnp3ConfigInvalidPortError(Dnp3ConfigError):
    """`port` liegt ausserhalb des TCP-Port-Bereichs."""

    def __init__(self, value: int) -> None:
        super().__init__(
            f"Dnp3ProtocolPortConfig.port={value}: muss in [{_MIN_PORT}, {_MAX_PORT}] liegen."
        )
        self.value: int = value


class Dnp3ConfigInvalidAddressError(Dnp3ConfigError):
    """`master_address` oder `outstation_address` liegt ausserhalb
    des DNP3-Adress-Bereichs."""

    def __init__(self, value: int, field_name: str) -> None:
        super().__init__(
            f"Dnp3ProtocolPortConfig.{field_name}={value}: "
            f"muss in [{_MIN_ADDRESS}, {_MAX_ADDRESS}] liegen."
        )
        self.value: int = value
        self.field_name: str = field_name


class Dnp3ConfigInvalidTimeoutError(Dnp3ConfigError):
    """`response_timeout_s` ist nicht > 0."""

    def __init__(self, value: float) -> None:
        super().__init__(f"Dnp3ProtocolPortConfig.response_timeout_s={value} muss > 0 sein.")
        self.value: float = value


class Dnp3ConfigEmptyPointsError(Dnp3ConfigError):
    """`points` ist leer; mindestens ein Eintrag noetig."""

    def __init__(self) -> None:
        super().__init__("Dnp3ProtocolPortConfig.points darf nicht leer sein.")


class Dnp3ConfigInvalidGroupVariationError(Dnp3ConfigError):
    """`(group, variation)` ist nicht in der Welle-5a-Allow-List
    (ADR 0034 §2.3)."""

    def __init__(self, group: int, variation: int, device_id: str) -> None:
        allowed = sorted(_ALLOWED_GROUP_VARIATIONS)
        super().__init__(
            f"Dnp3PointConfig({device_id!r}).group/variation=({group},{variation}): "
            f"muss in {allowed} liegen (Welle-5a-Allow-List: Group 1/V1, 1/V2, "
            "30/V1, 30/V5; Counter/Output/Event-Classes Welle-6-Schaerfung)."
        )
        self.group: int = group
        self.variation: int = variation
        self.device_id: str = device_id


class Dnp3ConfigInvalidIndexError(Dnp3ConfigError):
    """`index` ist negativ."""

    def __init__(self, value: int, device_id: str) -> None:
        super().__init__(f"Dnp3PointConfig({device_id!r}).index={value}: muss >= 0 sein.")
        self.value: int = value
        self.device_id: str = device_id


class Dnp3ConfigInvalidAccessError(Dnp3ConfigError):
    """`access` ist nicht `"read"` oder `"write"`."""

    def __init__(self, value: str, device_id: str) -> None:
        super().__init__(
            f'Dnp3PointConfig({device_id!r}).access={value!r}: muss "read" oder "write" sein.'
        )
        self.value: str = value
        self.device_id: str = device_id


@dataclass(frozen=True, slots=True)
class Dnp3PointConfig:
    """Point-Profil fuer ein einzelnes Target (Decision D-a inline-
    Schema).

    Pflicht-Felder: `group`, `variation`, `index`, `access`.
    """

    group: int
    variation: int
    index: int
    access: Literal["read", "write"]


@dataclass(frozen=True, slots=True)
class Dnp3ProtocolPortConfig:
    """DNP3-Adapter-Profile (Decision D-a inline-Schema im
    Scenario-YAML).

    Konstruktor validiert fail-fast — Konstruktor-Aufrufer
    (Scenario-Loader oder Test) bekommt sofort eine typed
    `Dnp3ConfigError`-Subclass bei fehlerhafter Konfig.
    """

    host: str
    points: Mapping[str, Dnp3PointConfig]
    port: int = _DEFAULT_PORT
    master_address: int = _DEFAULT_MASTER_ADDRESS
    outstation_address: int = _DEFAULT_OUTSTATION_ADDRESS
    response_timeout_s: float = _DEFAULT_TIMEOUT_S

    def __post_init__(self) -> None:
        self._validate()
        # Immutable nach Konstruktion (Pattern analog
        # `OpcuaProtocolPortConfig` aus Welle 4 und
        # `ModbusProtocolPortConfig` aus Welle 3).
        object.__setattr__(self, "points", MappingProxyType(dict(self.points)))

    def _validate(self) -> None:
        if not self.host:
            raise Dnp3ConfigEmptyFieldError("host")
        if not (_MIN_PORT <= self.port <= _MAX_PORT):
            raise Dnp3ConfigInvalidPortError(self.port)
        if not (_MIN_ADDRESS <= self.master_address <= _MAX_ADDRESS):
            raise Dnp3ConfigInvalidAddressError(self.master_address, "master_address")
        if not (_MIN_ADDRESS <= self.outstation_address <= _MAX_ADDRESS):
            raise Dnp3ConfigInvalidAddressError(self.outstation_address, "outstation_address")
        if self.response_timeout_s <= 0:
            raise Dnp3ConfigInvalidTimeoutError(self.response_timeout_s)
        if not self.points:
            raise Dnp3ConfigEmptyPointsError
        for device_id, point_cfg in self.points.items():
            _validate_single_point_config(device_id, point_cfg)


def _validate_single_point_config(device_id: str, point_cfg: Dnp3PointConfig) -> None:
    """Prueft Pflicht-Felder und Wertebereiche fuer einen einzelnen
    `Dnp3PointConfig`. Wirft typed Errors mit Kontext."""
    if (point_cfg.group, point_cfg.variation) not in _ALLOWED_GROUP_VARIATIONS:
        raise Dnp3ConfigInvalidGroupVariationError(point_cfg.group, point_cfg.variation, device_id)
    if point_cfg.index < 0:
        raise Dnp3ConfigInvalidIndexError(point_cfg.index, device_id)
    if point_cfg.access not in ("read", "write"):
        raise Dnp3ConfigInvalidAccessError(point_cfg.access, device_id)
