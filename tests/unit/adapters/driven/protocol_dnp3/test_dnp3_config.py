"""Konstruktor-Validation fuer `Dnp3ProtocolPortConfig` /
`Dnp3PointConfig` (M4 Welle 5a, ADR 0034 §2.1).
"""

from __future__ import annotations

import pytest

from grid_gym.adapters.driven.protocol_dnp3 import (
    Dnp3ConfigEmptyFieldError,
    Dnp3ConfigEmptyPointsError,
    Dnp3ConfigInvalidAccessError,
    Dnp3ConfigInvalidAddressError,
    Dnp3ConfigInvalidGroupVariationError,
    Dnp3ConfigInvalidIndexError,
    Dnp3ConfigInvalidPortError,
    Dnp3ConfigInvalidTimeoutError,
    Dnp3PointConfig,
    Dnp3ProtocolPortConfig,
)


def _basic_point() -> dict[str, Dnp3PointConfig]:
    return {
        "battery1_power": Dnp3PointConfig(group=30, variation=5, index=0, access="read"),
    }


def test_minimal_config_construction_succeeds() -> None:
    config = Dnp3ProtocolPortConfig(host="127.0.0.1", points=_basic_point())
    assert config.host == "127.0.0.1"
    assert config.port == 20000
    assert config.master_address == 1
    assert config.outstation_address == 10
    assert config.response_timeout_s == pytest.approx(5.0)
    assert "battery1_power" in config.points


def test_config_rejects_empty_host() -> None:
    with pytest.raises(Dnp3ConfigEmptyFieldError) as exc_info:
        Dnp3ProtocolPortConfig(host="", points=_basic_point())
    assert exc_info.value.field_name == "host"


@pytest.mark.parametrize("port", [0, 65536, -1])
def test_config_rejects_invalid_port(port: int) -> None:
    with pytest.raises(Dnp3ConfigInvalidPortError) as exc_info:
        Dnp3ProtocolPortConfig(host="127.0.0.1", port=port, points=_basic_point())
    assert exc_info.value.value == port


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("master_address", -1),
        ("master_address", 65536),
        ("outstation_address", -1),
        ("outstation_address", 70000),
    ],
)
def test_config_rejects_invalid_address(field: str, value: int) -> None:
    kwargs: dict[str, object] = {"host": "127.0.0.1", "points": _basic_point()}
    kwargs[field] = value
    with pytest.raises(Dnp3ConfigInvalidAddressError) as exc_info:
        Dnp3ProtocolPortConfig(**kwargs)  # type: ignore[arg-type]
    assert exc_info.value.field_name == field
    assert exc_info.value.value == value


def test_config_rejects_non_positive_timeout() -> None:
    with pytest.raises(Dnp3ConfigInvalidTimeoutError):
        Dnp3ProtocolPortConfig(
            host="127.0.0.1",
            points=_basic_point(),
            response_timeout_s=0.0,
        )


def test_config_rejects_empty_points() -> None:
    with pytest.raises(Dnp3ConfigEmptyPointsError):
        Dnp3ProtocolPortConfig(host="127.0.0.1", points={})


@pytest.mark.parametrize(
    ("group", "variation"),
    [
        (30, 2),  # Variation 2 — Welle-6-Schaerfung
        (32, 1),  # Group 32 = Analog Input Event — Welle-6
        (20, 1),  # Group 20 = Counter — Welle-6
        (10, 1),  # Group 10 = Binary Output — Welle-6
        (1, 3),  # Group 1/V3 — kein Welle-5a-Profil
    ],
)
def test_config_rejects_invalid_group_variation(group: int, variation: int) -> None:
    bad = {
        "device1": Dnp3PointConfig(group=group, variation=variation, index=0, access="read"),
    }
    with pytest.raises(Dnp3ConfigInvalidGroupVariationError) as exc_info:
        Dnp3ProtocolPortConfig(host="127.0.0.1", points=bad)
    assert exc_info.value.group == group
    assert exc_info.value.variation == variation


def test_config_rejects_negative_index() -> None:
    bad = {
        "device1": Dnp3PointConfig(group=30, variation=5, index=-1, access="read"),
    }
    with pytest.raises(Dnp3ConfigInvalidIndexError) as exc_info:
        Dnp3ProtocolPortConfig(host="127.0.0.1", points=bad)
    assert exc_info.value.value == -1


def test_config_rejects_invalid_access() -> None:
    bad = {
        "device1": Dnp3PointConfig(
            group=30,
            variation=5,
            index=0,
            access="readwrite",  # type: ignore[arg-type]
        ),
    }
    with pytest.raises(Dnp3ConfigInvalidAccessError) as exc_info:
        Dnp3ProtocolPortConfig(host="127.0.0.1", points=bad)
    assert exc_info.value.value == "readwrite"


def test_points_become_immutable_after_construction() -> None:
    config = Dnp3ProtocolPortConfig(host="127.0.0.1", points=_basic_point())
    with pytest.raises(TypeError):
        config.points["x"] = Dnp3PointConfig(  # type: ignore[index]
            group=30, variation=5, index=99, access="read"
        )


@pytest.mark.parametrize(
    ("group", "variation"),
    [(1, 1), (1, 2), (30, 1), (30, 5)],
)
def test_all_welle5a_group_variations_accepted(group: int, variation: int) -> None:
    points = {
        "device1": Dnp3PointConfig(group=group, variation=variation, index=0, access="read"),
    }
    config = Dnp3ProtocolPortConfig(host="127.0.0.1", points=points)
    assert config.points["device1"].group == group
    assert config.points["device1"].variation == variation
