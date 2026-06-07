# SPDX-License-Identifier: GPL-3.0-only
"""IEC-61850-Adapter-Profile-Konfiguration (M4 Welle 5b, ADR 0035 §2.1).

Simulation only — diese Adapter-Konfiguration ist dafuer gedacht,
simulierte IEC-61850-IEDs oder Test-Server anzusprechen, nicht
produktive Anlagen (`GG-SAFE-007`, `GG-NONGOAL-001`).

`Iec61850ProtocolPortConfig` ist eine frozen-dataclass mit dem
inline-im-`protocol_ports`-Block deklarierten LN/CDC-Schema
(Decision I-a). Pro `device_id` traegt `Iec61850LnConfig`
`object_reference` (LD/LN.DO.DA) + `functional_constraint` + `datatype`
+ `access` (Decision I-a/I-c). Validation-Errors werfen typed
Sub-Exceptions analog der Welle-3/4/5a-Pattern.

Welle-5b-Felder (`Iec61850ProtocolPortConfig`):

- `host` — IEC-61850-Server-Hostname (Pflicht).
- `port` — TCP-Port (Default `102`; IEC-61850-Standard MMS-Port).
- `ied_name` — IED-Name (Pflicht; muss mit MODEL-Name im CFG-Modell
  ueberein­stimmen).
- `response_timeout_s` — Connect-/Read-Timeout in Sekunden
  (Default `5.0`).
- `points` — Mapping `device_id` -> `Iec61850LnConfig`
  (Decision I-a inline-Schema). Mindestens ein Eintrag noetig.

Welle-5b-Felder (`Iec61850LnConfig`):

- `object_reference` — vollqualifizierte Object-Reference im
  Format `<MODEL+LD>/<LN>.<DO>.<DA>` (z. B.
  `simpleIOGenericIO/GGIO1.AnIn1.mag.f`). Pflicht; muss `/`
  enthalten.
- `functional_constraint` — FC-Code als Two-Letter-String
  (Decision I-c Allow-List `{"MX", "ST", "SP", "CF", "DC"}`).
  Adapter-Default ist `"MX"` (Measurand-Subtree; Welle-5b-Probe-
  Run-Befund: passt fuer float/int32/string sauber; bool kann
  CFG-/DO-spezifisch FC=ST brauchen).
- `datatype` — `"bool"`, `"int32"`, `"float"` oder `"string"`
  (Welle-5b-Allow-List; UINT/OCTET_STRING/UTC_TIME/Arrays/Structs
  Welle-6-Schaerfung).
- `access` — `"read"` (Welle-5b-Minimum; `"write"` ist
  Welle-6-Schaerfung — wird hier validiert aber im Port nicht
  produktiv ausgefuehrt).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal


_DEFAULT_PORT: Final[int] = 102
_DEFAULT_TIMEOUT_S: Final[float] = 5.0
_MIN_PORT: Final[int] = 1
_MAX_PORT: Final[int] = 65535

# Welle-5b-Allow-List fuer FC-Codes (ADR 0035 §2.3).
_ALLOWED_FCS: Final[frozenset[str]] = frozenset({"MX", "ST", "SP", "CF", "DC"})

# Welle-5b-Allow-List fuer Datatype-Strings (ADR 0035 §2.3).
_ALLOWED_DATATYPES: Final[frozenset[str]] = frozenset({"bool", "int32", "float", "string"})


class Iec61850ConfigError(ValueError):
    """Base-Klasse fuer `Iec61850ProtocolPortConfig`-Validation-
    Fehler (ADR 0035 §2.1).

    Erbt von `ValueError` analog Welle-3/4/5a-Pattern.
    """


class Iec61850ConfigEmptyFieldError(Iec61850ConfigError):
    """String-Pflichtfeld (`host`/`ied_name`) ist leer."""

    def __init__(self, field_name: str) -> None:
        super().__init__(f"Iec61850ProtocolPortConfig.{field_name} darf nicht leer sein.")
        self.field_name: str = field_name


class Iec61850ConfigInvalidPortError(Iec61850ConfigError):
    """`port` liegt ausserhalb des TCP-Port-Bereichs."""

    def __init__(self, value: int) -> None:
        super().__init__(
            f"Iec61850ProtocolPortConfig.port={value}: muss in [{_MIN_PORT}, {_MAX_PORT}] liegen."
        )
        self.value: int = value


class Iec61850ConfigInvalidTimeoutError(Iec61850ConfigError):
    """`response_timeout_s` ist nicht > 0."""

    def __init__(self, value: float) -> None:
        super().__init__(f"Iec61850ProtocolPortConfig.response_timeout_s={value} muss > 0 sein.")
        self.value: float = value


class Iec61850ConfigEmptyPointsError(Iec61850ConfigError):
    """`points` ist leer; mindestens ein Eintrag noetig."""

    def __init__(self) -> None:
        super().__init__("Iec61850ProtocolPortConfig.points darf nicht leer sein.")


class Iec61850ConfigInvalidReferenceError(Iec61850ConfigError):
    """`object_reference` ist leer oder traegt kein `/`-Trennzeichen
    zwischen LD und LN.DO.DA."""

    def __init__(self, value: str, device_id: str) -> None:
        super().__init__(
            f"Iec61850LnConfig({device_id!r}).object_reference={value!r}: "
            "muss nicht-leerer String im Format <LD>/<LN>.<DO>[.<DA>] sein."
        )
        self.value: str = value
        self.device_id: str = device_id


class Iec61850ConfigInvalidFcError(Iec61850ConfigError):
    """`functional_constraint` ist nicht in der Welle-5b-Allow-List
    (ADR 0035 §2.3)."""

    def __init__(self, value: str, device_id: str) -> None:
        allowed = sorted(_ALLOWED_FCS)
        super().__init__(
            f"Iec61850LnConfig({device_id!r}).functional_constraint={value!r}: "
            f"muss in {allowed} liegen (Welle-5b-Allow-List; weitere FCs "
            "Welle-6-Schaerfung)."
        )
        self.value: str = value
        self.device_id: str = device_id


class Iec61850ConfigInvalidDatatypeError(Iec61850ConfigError):
    """`datatype` ist nicht in der Welle-5b-Allow-List
    (ADR 0035 §2.3)."""

    def __init__(self, value: str, device_id: str) -> None:
        allowed = sorted(_ALLOWED_DATATYPES)
        super().__init__(
            f"Iec61850LnConfig({device_id!r}).datatype={value!r}: "
            f"muss in {allowed} liegen (Welle-5b-Allow-List; "
            "UINT/OCTET_STRING/UTC_TIME/Arrays/Structs Welle-6-Schaerfung)."
        )
        self.value: str = value
        self.device_id: str = device_id


class Iec61850ConfigInvalidAccessError(Iec61850ConfigError):
    """`access` ist nicht `"read"`.

    Welle-5b-C2-Review-Folge 2026-06-01: Anti-Scope-Hardening —
    `access="write"` wird **bei Konstruktion** abgelehnt statt erst
    zur Laufzeit in `port.write()` mit
    `Iec61850PortWriteNotImplementedError` zu crashen. Welle-6 fuehrt
    den Write-Pfad ein und wird diese Validation entsprechend
    erweitern.
    """

    def __init__(self, value: str, device_id: str) -> None:
        super().__init__(
            f"Iec61850LnConfig({device_id!r}).access={value!r}: "
            'muss "read" sein (Welle-5b-Anti-Scope; Write-Pfad ist '
            "Welle-6-Schaerfung — ADR 0035 §2.4)."
        )
        self.value: str = value
        self.device_id: str = device_id


@dataclass(frozen=True, slots=True)
class Iec61850LnConfig:
    """LN/CDC-Profil fuer ein einzelnes Target (Decision I-a inline-
    Schema).

    Pflicht-Felder: `object_reference`, `functional_constraint`,
    `datatype`, `access`. `functional_constraint` ist Two-Letter-
    String (z. B. `"MX"`); die pyiec61850-ng-Library-Konvertierung
    auf den int-Enum erfolgt intern.
    """

    object_reference: str
    functional_constraint: Literal["MX", "ST", "SP", "CF", "DC"]
    datatype: Literal["bool", "int32", "float", "string"]
    access: Literal["read", "write"]


@dataclass(frozen=True, slots=True)
class Iec61850ProtocolPortConfig:
    """IEC-61850-Adapter-Profile (Decision I-a inline-Schema im
    Scenario-YAML).

    Konstruktor validiert fail-fast — Konstruktor-Aufrufer
    (Scenario-Loader oder Test) bekommt sofort eine typed
    `Iec61850ConfigError`-Subclass bei fehlerhafter Konfig.
    """

    host: str
    ied_name: str
    points: Mapping[str, Iec61850LnConfig]
    port: int = _DEFAULT_PORT
    response_timeout_s: float = _DEFAULT_TIMEOUT_S

    def __post_init__(self) -> None:
        self._validate()
        # Immutable nach Konstruktion (Pattern aus Welle 3/4/5a).
        object.__setattr__(self, "points", MappingProxyType(dict(self.points)))

    def _validate(self) -> None:
        if not self.host:
            raise Iec61850ConfigEmptyFieldError("host")
        if not self.ied_name:
            raise Iec61850ConfigEmptyFieldError("ied_name")
        if not (_MIN_PORT <= self.port <= _MAX_PORT):
            raise Iec61850ConfigInvalidPortError(self.port)
        if self.response_timeout_s <= 0:
            raise Iec61850ConfigInvalidTimeoutError(self.response_timeout_s)
        if not self.points:
            raise Iec61850ConfigEmptyPointsError
        for device_id, ln_cfg in self.points.items():
            _validate_single_ln_config(device_id, ln_cfg)


def _validate_single_ln_config(device_id: str, ln_cfg: Iec61850LnConfig) -> None:
    """Prueft Pflicht-Felder und Wertebereiche fuer einen einzelnen
    `Iec61850LnConfig`. Wirft typed Errors mit Kontext."""
    if not ln_cfg.object_reference or "/" not in ln_cfg.object_reference:
        raise Iec61850ConfigInvalidReferenceError(ln_cfg.object_reference, device_id)
    if ln_cfg.functional_constraint not in _ALLOWED_FCS:
        raise Iec61850ConfigInvalidFcError(ln_cfg.functional_constraint, device_id)
    if ln_cfg.datatype not in _ALLOWED_DATATYPES:
        raise Iec61850ConfigInvalidDatatypeError(ln_cfg.datatype, device_id)
    # Welle-5b-C2-Review-Folge 2026-06-01: Anti-Scope-Hardening —
    # nur `"read"` ist erlaubt (vorher: `("read", "write")`, wobei
    # `"write"` erst zur Laufzeit in `port.write()` crashte).
    if ln_cfg.access != "read":
        raise Iec61850ConfigInvalidAccessError(ln_cfg.access, device_id)
