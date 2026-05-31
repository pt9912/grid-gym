"""Konstruktor-Validation fuer `OpcuaProtocolPortConfig` /
`OpcuaNodeConfig` (M4 Welle 4, ADR 0033 §2.1).
"""

from __future__ import annotations

import pytest

from grid_gym.adapters.driven.protocol_opcua import (
    OpcuaConfigEmptyFieldError,
    OpcuaConfigEmptyNodesError,
    OpcuaConfigInvalidAccessError,
    OpcuaConfigInvalidNamespaceError,
    OpcuaConfigInvalidNodeIdError,
    OpcuaConfigInvalidTimeoutError,
    OpcuaDatatype,
    OpcuaNodeConfig,
    OpcuaProtocolPortConfig,
)


def _basic_node() -> dict[str, OpcuaNodeConfig]:
    return {
        "battery1_soc": OpcuaNodeConfig(
            node_id="ns=2;i=1001", datatype=OpcuaDatatype.FLOAT, access="read"
        ),
    }


def test_minimal_config_construction_succeeds() -> None:
    config = OpcuaProtocolPortConfig(endpoint_url="opc.tcp://localhost:4840", nodes=_basic_node())
    assert config.endpoint_url == "opc.tcp://localhost:4840"
    assert config.timeout_s == pytest.approx(5.0)
    assert "battery1_soc" in config.nodes


def test_config_rejects_empty_endpoint_url() -> None:
    with pytest.raises(OpcuaConfigEmptyFieldError) as exc_info:
        OpcuaProtocolPortConfig(endpoint_url="", nodes=_basic_node())
    assert exc_info.value.field_name == "endpoint_url"


def test_config_rejects_non_positive_timeout() -> None:
    with pytest.raises(OpcuaConfigInvalidTimeoutError) as exc_info:
        OpcuaProtocolPortConfig(
            endpoint_url="opc.tcp://localhost:4840",
            nodes=_basic_node(),
            timeout_s=0.0,
        )
    assert exc_info.value.value == pytest.approx(0.0)


def test_config_rejects_empty_nodes() -> None:
    with pytest.raises(OpcuaConfigEmptyNodesError):
        OpcuaProtocolPortConfig(endpoint_url="opc.tcp://localhost:4840", nodes={})


def test_node_id_must_match_pattern() -> None:
    bad = {
        "device1": OpcuaNodeConfig(node_id="i=1001", datatype=OpcuaDatatype.INT32, access="read"),
    }
    with pytest.raises(OpcuaConfigInvalidNodeIdError) as exc_info:
        OpcuaProtocolPortConfig(endpoint_url="opc.tcp://localhost:4840", nodes=bad)
    assert exc_info.value.device_id == "device1"
    assert exc_info.value.value == "i=1001"


def test_node_id_string_identifier_accepted() -> None:
    nodes = {
        "device1": OpcuaNodeConfig(
            node_id="ns=2;s=foo.bar", datatype=OpcuaDatatype.STRING, access="read"
        ),
    }
    config = OpcuaProtocolPortConfig(endpoint_url="opc.tcp://localhost:4840", nodes=nodes)
    assert config.nodes["device1"].node_id == "ns=2;s=foo.bar"


def test_namespace_out_of_range_rejected() -> None:
    bad = {
        "device1": OpcuaNodeConfig(
            node_id="ns=70000;i=1001", datatype=OpcuaDatatype.INT32, access="read"
        ),
    }
    with pytest.raises(OpcuaConfigInvalidNamespaceError) as exc_info:
        OpcuaProtocolPortConfig(endpoint_url="opc.tcp://localhost:4840", nodes=bad)
    assert exc_info.value.value == 70000
    assert exc_info.value.device_id == "device1"


def test_access_must_be_read_or_write() -> None:
    bad = {
        "device1": OpcuaNodeConfig(
            node_id="ns=2;i=1001",
            datatype=OpcuaDatatype.INT32,
            access="readwrite",  # type: ignore[arg-type]
        ),
    }
    with pytest.raises(OpcuaConfigInvalidAccessError) as exc_info:
        OpcuaProtocolPortConfig(endpoint_url="opc.tcp://localhost:4840", nodes=bad)
    assert exc_info.value.value == "readwrite"


def test_nodes_become_immutable_after_construction() -> None:
    config = OpcuaProtocolPortConfig(endpoint_url="opc.tcp://localhost:4840", nodes=_basic_node())
    with pytest.raises(TypeError):
        config.nodes["x"] = OpcuaNodeConfig(  # type: ignore[index]
            node_id="ns=2;i=999", datatype=OpcuaDatatype.INT32, access="read"
        )


@pytest.mark.parametrize(
    "datatype",
    [
        OpcuaDatatype.BOOLEAN,
        OpcuaDatatype.INT16,
        OpcuaDatatype.UINT16,
        OpcuaDatatype.INT32,
        OpcuaDatatype.UINT32,
        OpcuaDatatype.FLOAT,
        OpcuaDatatype.DOUBLE,
        OpcuaDatatype.STRING,
    ],
)
def test_all_welle4_datatypes_accepted(datatype: OpcuaDatatype) -> None:
    nodes = {
        "device1": OpcuaNodeConfig(node_id="ns=2;i=1001", datatype=datatype, access="read"),
    }
    config = OpcuaProtocolPortConfig(endpoint_url="opc.tcp://localhost:4840", nodes=nodes)
    assert config.nodes["device1"].datatype is datatype
