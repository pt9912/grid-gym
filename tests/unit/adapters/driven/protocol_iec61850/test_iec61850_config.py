# SPDX-License-Identifier: GPL-3.0-only
"""Konstruktor-Validation fuer `Iec61850ProtocolPortConfig` /
`Iec61850LnConfig` (M4 Welle 5b, ADR 0035 §2.1).
"""

from __future__ import annotations

import pytest

from grid_gym.adapters.driven.protocol_iec61850 import (
    Iec61850ConfigEmptyFieldError,
    Iec61850ConfigEmptyPointsError,
    Iec61850ConfigInvalidAccessError,
    Iec61850ConfigInvalidDatatypeError,
    Iec61850ConfigInvalidFcError,
    Iec61850ConfigInvalidPortError,
    Iec61850ConfigInvalidReferenceError,
    Iec61850ConfigInvalidTimeoutError,
    Iec61850LnConfig,
    Iec61850ProtocolPortConfig,
)


def _basic_point() -> dict[str, Iec61850LnConfig]:
    return {
        "battery1_voltage": Iec61850LnConfig(
            object_reference="simpleIOGenericIO/GGIO1.AnIn1.mag.f",
            functional_constraint="MX",
            datatype="float",
            access="read",
        ),
    }


def test_minimal_config_construction_succeeds() -> None:
    config = Iec61850ProtocolPortConfig(
        host="127.0.0.1", ied_name="SimpleIO", points=_basic_point()
    )
    assert config.host == "127.0.0.1"
    assert config.ied_name == "SimpleIO"
    assert config.port == 102
    assert config.response_timeout_s == pytest.approx(5.0)
    assert "battery1_voltage" in config.points


def test_config_rejects_empty_host() -> None:
    with pytest.raises(Iec61850ConfigEmptyFieldError) as exc_info:
        Iec61850ProtocolPortConfig(host="", ied_name="SimpleIO", points=_basic_point())
    assert exc_info.value.field_name == "host"


def test_config_rejects_empty_ied_name() -> None:
    with pytest.raises(Iec61850ConfigEmptyFieldError) as exc_info:
        Iec61850ProtocolPortConfig(host="127.0.0.1", ied_name="", points=_basic_point())
    assert exc_info.value.field_name == "ied_name"


@pytest.mark.parametrize("port", [0, 65536, -1])
def test_config_rejects_invalid_port(port: int) -> None:
    with pytest.raises(Iec61850ConfigInvalidPortError) as exc_info:
        Iec61850ProtocolPortConfig(
            host="127.0.0.1", ied_name="SimpleIO", port=port, points=_basic_point()
        )
    assert exc_info.value.value == port


def test_config_rejects_non_positive_timeout() -> None:
    with pytest.raises(Iec61850ConfigInvalidTimeoutError):
        Iec61850ProtocolPortConfig(
            host="127.0.0.1",
            ied_name="SimpleIO",
            points=_basic_point(),
            response_timeout_s=0.0,
        )


def test_config_rejects_empty_points() -> None:
    with pytest.raises(Iec61850ConfigEmptyPointsError):
        Iec61850ProtocolPortConfig(host="127.0.0.1", ied_name="SimpleIO", points={})


@pytest.mark.parametrize("reference", ["", "no-slash"])
def test_config_rejects_invalid_reference(reference: str) -> None:
    """Welle-5b-Validation: `object_reference` muss nicht-leer sein
    **und** ein `/`-Trennzeichen enthalten. Stricter validation
    (leading-/trailing-slash, format details) ist Welle-6-Schaerfung
    — der Adapter scheitert spaeter beim Library-`read_value`-Call
    mit einer typed `Iec61850PortPointNotFoundError`-Translation,
    falls die Reference syntaktisch akzeptabel aber semantisch
    ungueltig ist.
    """
    bad = {
        "device1": Iec61850LnConfig(
            object_reference=reference,
            functional_constraint="MX",
            datatype="float",
            access="read",
        ),
    }
    with pytest.raises(Iec61850ConfigInvalidReferenceError) as exc_info:
        Iec61850ProtocolPortConfig(host="127.0.0.1", ied_name="SimpleIO", points=bad)
    assert exc_info.value.value == reference


@pytest.mark.parametrize("fc", ["XX", "MMX", "", "co", "ZZZ"])
def test_config_rejects_invalid_fc(fc: str) -> None:
    bad = {
        "device1": Iec61850LnConfig(
            object_reference="LD0/LN.DO",
            functional_constraint=fc,  # type: ignore[arg-type]
            datatype="float",
            access="read",
        ),
    }
    with pytest.raises(Iec61850ConfigInvalidFcError) as exc_info:
        Iec61850ProtocolPortConfig(host="127.0.0.1", ied_name="SimpleIO", points=bad)
    assert exc_info.value.value == fc


@pytest.mark.parametrize("fc", ["MX", "ST", "SP", "CF", "DC"])
def test_config_accepts_all_welle5b_fcs(fc: str) -> None:
    points = {
        "device1": Iec61850LnConfig(
            object_reference="LD0/LN.DO",
            functional_constraint=fc,  # type: ignore[arg-type]
            datatype="float",
            access="read",
        ),
    }
    config = Iec61850ProtocolPortConfig(host="127.0.0.1", ied_name="SimpleIO", points=points)
    assert config.points["device1"].functional_constraint == fc


@pytest.mark.parametrize("datatype", ["uint32", "int64", "octet_string", "bytes", ""])
def test_config_rejects_invalid_datatype(datatype: str) -> None:
    bad = {
        "device1": Iec61850LnConfig(
            object_reference="LD0/LN.DO",
            functional_constraint="MX",
            datatype=datatype,  # type: ignore[arg-type]
            access="read",
        ),
    }
    with pytest.raises(Iec61850ConfigInvalidDatatypeError) as exc_info:
        Iec61850ProtocolPortConfig(host="127.0.0.1", ied_name="SimpleIO", points=bad)
    assert exc_info.value.value == datatype


@pytest.mark.parametrize("datatype", ["bool", "int32", "float", "string"])
def test_config_accepts_all_welle5b_datatypes(datatype: str) -> None:
    points = {
        "device1": Iec61850LnConfig(
            object_reference="LD0/LN.DO",
            functional_constraint="MX",
            datatype=datatype,  # type: ignore[arg-type]
            access="read",
        ),
    }
    config = Iec61850ProtocolPortConfig(host="127.0.0.1", ied_name="SimpleIO", points=points)
    assert config.points["device1"].datatype == datatype


def test_config_rejects_invalid_access() -> None:
    bad = {
        "device1": Iec61850LnConfig(
            object_reference="LD0/LN.DO",
            functional_constraint="MX",
            datatype="float",
            access="readwrite",  # type: ignore[arg-type]
        ),
    }
    with pytest.raises(Iec61850ConfigInvalidAccessError) as exc_info:
        Iec61850ProtocolPortConfig(host="127.0.0.1", ied_name="SimpleIO", points=bad)
    assert exc_info.value.value == "readwrite"


def test_points_become_immutable_after_construction() -> None:
    config = Iec61850ProtocolPortConfig(
        host="127.0.0.1", ied_name="SimpleIO", points=_basic_point()
    )
    with pytest.raises(TypeError):
        config.points["x"] = Iec61850LnConfig(  # type: ignore[index]
            object_reference="LD0/LN.DO",
            functional_constraint="MX",
            datatype="float",
            access="read",
        )
