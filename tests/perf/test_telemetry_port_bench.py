"""`GG-RT-005` Bench: 10 000 Points/s am Telemetry-Port (M6 Welle 4b-b).

Pflicht-Doppel-Akzeptanz per `GG-RT-005`-Spec (Lastenheft Z. 491-495):

1. **Payload-Schwelle ≤ 256 Byte**: jeder `TelemetryPoint` wird vor
   dem Bench-Lauf canonical-serialisiert; Pflicht-Konversion:
   `dataclasses.asdict(point)` plus `value: float → Decimal(repr(...))`-
   Replacement (Welle-4b-b-D-2: `canonical_json` lehnt `float` ab
   und akzeptiert keine Dataclasses). Bytes-Length ueber das
   Mapping; Asserts `<= 256`.
2. **Throughput-Schwelle ≥ 10 000 OPS**: Bench misst `publish`-
   Rate gegen `InMemoryTelemetryStream`. Setup-Pflicht per Welle-
   4b-b-D-3: `asyncio.Queue(maxsize=128)` programmatisch in
   `stream._subscribers` einhaengen (umgeht `async def
   subscribe()`-Pfad bewusst, weil das asyncio-Kontext braucht).
   Niemand drained die Queue — Drop-Oldest greift ab dem 129.
   Publish; der publish-Pfad faehrt seine reale Queue-
   Manipulation-Substanz.

Bench-Framework: pytest-benchmark via Welle-4b-a-Foundation
(ADR-0041; opt-in via `--extra perf`).

Run: `make perf` (Dockerfile-`perf`-Stage). Baseline-Update:
`make perf-baseline-update`.
"""

from __future__ import annotations

import asyncio
import dataclasses
from decimal import Decimal

from grid_gym.adapters.driven.telemetry_stream_inmemory.stream import (
    InMemoryTelemetryStream,
)
from grid_gym.hexagon.core.serialization.canonical import canonical_json
from grid_gym.hexagon.ports.driving.telemetry_stream import (
    TelemetryPoint,
    TelemetryQuality,
)

_PUBLISH_COUNT = 10_000
_DEVICE_COUNT = 100
_QUEUE_MAXSIZE = 128
_PAYLOAD_LIMIT_BYTES = 256

# Median-Sekunden-Schwelle: 1e-4 s pro Publish = 10 000 OPS.
# `GG-RT-005` SOLLTE >= 10 000 Points/s.
_PUBLISH_LATENCY_LIMIT_SECONDS = 1e-4


def _canonical_point_payload(point: TelemetryPoint) -> bytes:
    """Welle-4b-b-D-2 Pflicht-Konversion.

    `canonical_json` lehnt `float` ab (`FloatNotAllowedError`) und
    akzeptiert keine Dataclasses; `TelemetryPoint.value` ist `float`.
    Hier wird das Frozen-Dataclass per `dataclasses.asdict()` in ein
    Mapping konvertiert und `value` ueber `Decimal(repr(...))` zu
    `Decimal` gehoben — das erhaelt die Float-Praezision via
    `repr()`-Roundtrip-Garantie und ist canonical-konform.
    """

    mapping = dataclasses.asdict(point)
    mapping["value"] = Decimal(repr(mapping["value"]))
    return canonical_json(mapping)


def _build_payload_pool() -> tuple[TelemetryPoint, ...]:
    """Vor-allokierter Pool von 10 000 TelemetryPoints fuer den Bench.

    Werte sind so gewaehlt, dass `_canonical_point_payload(point)`
    unter 256 Byte bleibt (Welle-4b-b-D-2-Akzeptanz). 100 Geraete
    werden zyklisch durchgegangen, damit `device_id` realistisch
    variiert.
    """

    points = []
    for sequence in range(_PUBLISH_COUNT):
        device_index = sequence % _DEVICE_COUNT
        point = TelemetryPoint(
            run_id="run-bench",
            device_id=f"dev-{device_index:03d}",
            metric="power_kw",
            value=12.5 + sequence * 0.01,
            unit="kW",
            simulation_time_ms=sequence * 100,
            quality="ok",
            sequence=sequence,
        )
        points.append(point)
    return tuple(points)


def _assert_payload_threshold(points: tuple[TelemetryPoint, ...]) -> None:
    """Welle-4b-b-D-2: jeder Point <= 256 Byte canonical-serialisiert."""

    for point in points:
        payload = _canonical_point_payload(point)
        assert len(payload) <= _PAYLOAD_LIMIT_BYTES, (
            f"GG-RT-005 Payload-Schwelle verletzt: "
            f"point.sequence={point.sequence}, "
            f"len(payload)={len(payload)} > {_PAYLOAD_LIMIT_BYTES} Byte"
        )


def _build_stream_with_subscriber_slot() -> InMemoryTelemetryStream:
    """Welle-4b-b-D-3 Setup: Single-Queue-Subscriber-Slot.

    Haengt eine `asyncio.Queue(maxsize=128)` programmatisch direkt in
    `stream._subscribers` ein — umgeht `async def subscribe()` (das
    braucht asyncio-Kontext). Niemand drained die Queue; Drop-Oldest
    greift ab dem 129. Publish (der publish-Pfad faehrt
    `subscriber.full()` + `get_nowait()` + `put_nowait()`-Substanz).
    """

    stream = InMemoryTelemetryStream(queue_maxsize=_QUEUE_MAXSIZE)
    queue: asyncio.Queue[TelemetryPoint] = asyncio.Queue(maxsize=_QUEUE_MAXSIZE)
    stream._subscribers.append(queue)
    return stream


def _publish_all(
    stream: InMemoryTelemetryStream,
    points: tuple[TelemetryPoint, ...],
) -> int:
    """Publisht alle Points sequentiell; Returns die Anzahl publishter Points."""

    for point in points:
        stream.publish(point)
    return len(points)


def test_gg_rt_005_telemetry_port_publish_throughput(benchmark) -> None:  # type: ignore[no-untyped-def]
    """`GG-RT-005` Doppel-Akzeptanz:

    - Payload-Schwelle: alle 10 000 Points canonical-serialisiert
      ≤ 256 Byte (Pre-Bench-Assert).
    - Throughput-Schwelle: Median-OPS >= 10 000
      (`benchmark.stats["median"] <= 1e-4` Sekunden).
    """

    points = _build_payload_pool()

    # Assert 1: Payload-Schwelle vor dem Bench-Lauf.
    _assert_payload_threshold(points)

    # Bench: publishing all 10 000 points mit Single-Queue-Subscriber-Slot.
    def _bench() -> int:
        stream = _build_stream_with_subscriber_slot()
        return _publish_all(stream, points)

    published_count = benchmark(_bench)

    assert published_count == _PUBLISH_COUNT, (
        f"GG-RT-005 publish-Count-Drift: erwartet {_PUBLISH_COUNT}, got {published_count}"
    )

    # Assert 2: Throughput-Schwelle. benchmark.stats liefert Sekunden pro
    # Iteration (= 10 000 publishes). Median pro publish = stats / count.
    median_seconds_per_run = benchmark.stats["median"]
    median_seconds_per_publish = median_seconds_per_run / _PUBLISH_COUNT
    median_ops = 1.0 / median_seconds_per_publish

    assert median_seconds_per_publish <= _PUBLISH_LATENCY_LIMIT_SECONDS, (
        f"GG-RT-005 Throughput-Schwelle verletzt: "
        f"median publish-Latency = {median_seconds_per_publish * 1e6:.2f} us "
        f"(>= {_PUBLISH_LATENCY_LIMIT_SECONDS * 1e6:.2f} us); "
        f"median OPS = {median_ops:.0f} < {1 / _PUBLISH_LATENCY_LIMIT_SECONDS:.0f}"
    )
