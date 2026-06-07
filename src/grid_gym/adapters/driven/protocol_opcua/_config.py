"""OPC-UA-Adapter-Profile-Konfiguration (M4 Welle 4, ADR 0033 §2.1).

Simulation only — diese Adapter-Konfiguration ist dafuer gedacht,
simulierte OPC-UA-Server oder Testaufbauten anzusprechen, nicht
produktive Anlagen (`GG-SAFE-007`, `GG-NONGOAL-001`).

`OpcuaProtocolPortConfig` ist eine frozen-dataclass mit dem inline-im-
`protocol_ports`-Block deklarierten Node-ID-Schema (Decision O-a).
Pro `device_id` traegt `OpcuaNodeConfig` Node-ID + Datatype + Access
(Decision O-a/O-c/O-d). Validation-Errors werfen typed Sub-Exceptions
analog `ModbusConfigError`-Familie aus M4-Welle-3.

Welle-4-Felder (`OpcuaProtocolPortConfig`):

- `endpoint_url` — OPC-UA-Server-Endpoint
  (`opc.tcp://host:port`-Form; Pflicht, nicht leer).
- `timeout_s` — Connect-/Read-/Write-Timeout in Sekunden
  (Default `5.0`; gilt fuer das Loop-Thread-Marshal aus ADR 0033 §2.2).
- `nodes` — Mapping `device_id` -> `OpcuaNodeConfig`
  (Decision O-a inline-Schema). Mindestens ein Eintrag noetig.

Welle-4-Felder (`OpcuaNodeConfig`):

- `node_id` — OPC-UA-Node-ID-String (Pflicht; Format `"ns=N;i=M"`
  oder `"ns=N;s=Identifier"`).
- `datatype` — `OpcuaDatatype` Enum (Decision O-c: Boolean/Int16/
  UInt16/Int32/UInt32/Float/Double/String).
- `access` — `"read"` oder `"write"` (Pflicht).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final, Literal


_DEFAULT_TIMEOUT_S: Final[float] = 5.0
_NODE_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^ns=(?P<ns>\d+);(?P<kind>[is])=(?P<ident>.+)$"
)
_MIN_NAMESPACE: Final[int] = 0
_MAX_NAMESPACE: Final[int] = 65535


class OpcuaDatatype(StrEnum):
    """Erlaubte Datatypes in Welle 4 (ADR 0033 §2.3 Decision O-c).

    `Byte`/`SByte`/`Int64`/`UInt64`/`DateTime`/`Guid`/`ByteString`/
    `ExtensionObject` sind Welle-6-Schaerfungspfad (ADR 0011); nicht
    hier.
    """

    BOOLEAN = "Boolean"
    INT16 = "Int16"
    UINT16 = "UInt16"
    INT32 = "Int32"
    UINT32 = "UInt32"
    FLOAT = "Float"
    DOUBLE = "Double"
    STRING = "String"


class OpcuaConfigError(ValueError):
    """Base-Klasse fuer `OpcuaProtocolPortConfig`-Validation-Fehler
    (ADR 0033 §2.1).

    Erbt von `ValueError`, damit defensiv-coded Aufrufer den Standard-
    Konstruktor-Fehler-Pfad nicht aendern muessen. Konkrete Fehlerfaelle
    werfen Subklassen mit strukturierten Konstruktor-Parametern
    (TRY003-Konvention, Message-Bildung in Subklasse).
    """


class OpcuaConfigEmptyFieldError(OpcuaConfigError):
    """String-Pflichtfeld (z. B. `endpoint_url`) ist leer."""

    def __init__(self, field_name: str) -> None:
        super().__init__(f"OpcuaProtocolPortConfig.{field_name} darf nicht leer sein.")
        self.field_name: str = field_name


class OpcuaConfigInvalidTimeoutError(OpcuaConfigError):
    """`timeout_s` ist nicht > 0."""

    def __init__(self, value: float) -> None:
        super().__init__(f"OpcuaProtocolPortConfig.timeout_s={value} muss > 0 sein.")
        self.value: float = value


class OpcuaConfigEmptyNodesError(OpcuaConfigError):
    """`nodes` ist leer; mindestens ein Eintrag noetig."""

    def __init__(self) -> None:
        super().__init__("OpcuaProtocolPortConfig.nodes darf nicht leer sein.")


class OpcuaConfigInvalidNodeIdError(OpcuaConfigError):
    """Node-ID-String matcht nicht das `"ns=N;i=M"`/`"ns=N;s=Ident"`-
    Format (ADR 0033 §2.1 Decision O-a)."""

    def __init__(self, value: str, device_id: str) -> None:
        super().__init__(
            f"OpcuaNodeConfig({device_id!r}).node_id={value!r}: "
            'muss "ns=N;i=M" (numerisch) oder "ns=N;s=Identifier" '
            "(String) sein (ADR 0033 §2.1)."
        )
        self.value: str = value
        self.device_id: str = device_id


class OpcuaConfigInvalidNamespaceError(OpcuaConfigError):
    """Namespace-Index ausserhalb des OPC-UA-`UInt16`-Bereichs."""

    def __init__(self, value: int, device_id: str) -> None:
        super().__init__(
            f"OpcuaNodeConfig({device_id!r}).node_id: "
            f"namespace={value} muss in [{_MIN_NAMESPACE}, {_MAX_NAMESPACE}] "
            "liegen (OPC-UA-Spec UInt16)."
        )
        self.value: int = value
        self.device_id: str = device_id


class OpcuaConfigInvalidAccessError(OpcuaConfigError):
    """`access` ist nicht `"read"` oder `"write"`."""

    def __init__(self, value: str, device_id: str) -> None:
        super().__init__(
            f'OpcuaNodeConfig({device_id!r}).access={value!r}: muss "read" oder "write" sein.'
        )
        self.value: str = value
        self.device_id: str = device_id


@dataclass(frozen=True, slots=True)
class OpcuaNodeConfig:
    """Node-Profil fuer ein einzelnes Target (Decision O-a inline-
    Schema).

    Pflicht-Felder: `node_id`, `datatype`, `access`.
    """

    node_id: str
    datatype: OpcuaDatatype
    access: Literal["read", "write"]


@dataclass(frozen=True, slots=True)
class OpcuaProtocolPortConfig:
    """OPC-UA-Adapter-Profile (Decision O-a inline-Schema im
    Scenario-YAML).

    Konstruktor validiert fail-fast — Konstruktor-Aufrufer (Scenario-
    Loader oder Test) bekommt sofort eine typed `OpcuaConfigError`-
    Subclass bei fehlerhafter Konfig.
    """

    endpoint_url: str
    nodes: Mapping[str, OpcuaNodeConfig]
    timeout_s: float = _DEFAULT_TIMEOUT_S

    def __post_init__(self) -> None:
        self._validate()
        # Immutable nach Konstruktion (Pattern analog
        # `ModbusProtocolPortConfig` aus Welle 3).
        object.__setattr__(self, "nodes", MappingProxyType(dict(self.nodes)))

    def _validate(self) -> None:
        if not self.endpoint_url:
            raise OpcuaConfigEmptyFieldError("endpoint_url")
        if self.timeout_s <= 0:
            raise OpcuaConfigInvalidTimeoutError(self.timeout_s)
        if not self.nodes:
            raise OpcuaConfigEmptyNodesError
        for device_id, node_cfg in self.nodes.items():
            _validate_single_node_config(device_id, node_cfg)


def _validate_single_node_config(device_id: str, node_cfg: OpcuaNodeConfig) -> None:
    """Prueft Pflicht-Felder und Wertebereiche fuer einen einzelnen
    `OpcuaNodeConfig`. Wirft typed Errors mit Kontext.

    Slice-032-Nachzug (Welle-4-Review Finding 1): `i=`-Variante muss
    einen parsbaren Integer-Identifier tragen — `ns=2;i=abc` matchte
    bisher den Regex (`.+` ist beliebig), wurde aber nie weiter
    geprueft.
    """
    match = _NODE_ID_PATTERN.match(node_cfg.node_id)
    if match is None:
        raise OpcuaConfigInvalidNodeIdError(node_cfg.node_id, device_id)
    namespace = int(match.group("ns"))
    if not (_MIN_NAMESPACE <= namespace <= _MAX_NAMESPACE):
        raise OpcuaConfigInvalidNamespaceError(namespace, device_id)
    kind = match.group("kind")
    ident = match.group("ident")
    if kind == "i":
        try:
            int(ident)
        except ValueError as exc:
            raise OpcuaConfigInvalidNodeIdError(node_cfg.node_id, device_id) from exc
    if node_cfg.access not in ("read", "write"):
        raise OpcuaConfigInvalidAccessError(node_cfg.access, device_id)
