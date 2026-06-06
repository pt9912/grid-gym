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
from grid_gym.hexagon.ports.driving.telemetry_stream import TelemetryPoint

_PUBLISH_COUNT = 10_000
_DEVICE_COUNT = 100
_QUEUE_MAXSIZE = 128
_PAYLOAD_LIMIT_BYTES = 256

# `GG-RT-005` SOLLTE: >= 10 000 Publish-OPS am Telemetry-Port.
# Latency-Schwelle = Reziproke der OPS-Schwelle (1 Sek / 10 000 = 1e-4 s).
_GG_RT_005_MIN_OPS = 10_000
_PUBLISH_LATENCY_LIMIT_SECONDS = 1.0 / _GG_RT_005_MIN_OPS


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
        # `round(..., 2)` schneidet IEEE-754-Akkumulations-Drift ab
        # (`12.5 + n * 0.01` produziert sonst Werte wie
        # `12.510000000000001`, deren `repr()` `Decimal(repr(...))`-
        # Konversion ueber 18 Zeichen lang werden laesst — gegen die
        # 256-Byte-Payload-Schwelle fragil).
        point = TelemetryPoint(
            run_id="run-bench",
            device_id=f"dev-{device_index:03d}",
            metric="power_kw",
            value=round(12.5 + sequence * 0.01, 2),
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
    # Ruff SLF001 (private-member-access) ist heute NICHT in der
    # Lint-Konfig aktiviert; falls spaeter aktiviert: ADR-0038-Bypass
    # ist per Welle-4b-b-D-3 dokumentiert; ein lint-Suppress mit
    # dieser Begruendungs-Referenz waere dann zulaessig.
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

    # Assert 2: Drop-Oldest-Auslosung verifizieren (Welle-4b-b-D-3-
    # Pflicht). Separater post-bench-Lauf, damit der Assert nicht
    # in die benchmark-Timing-Substanz wandert. 10 000 publishes auf
    # Queue mit maxsize=128 = Drop-Oldest greift 9872x; finale qsize
    # ist genau die maxsize.
    verification_stream = _build_stream_with_subscriber_slot()
    _publish_all(verification_stream, points)
    verification_queue = verification_stream._subscribers[0]
    assert verification_queue.qsize() == _QUEUE_MAXSIZE, (
        f"GG-RT-005 Drop-Oldest-Pflicht-Path nicht ausgeloest: "
        f"qsize={verification_queue.qsize()} != {_QUEUE_MAXSIZE}"
    )

    # Assert 3: Throughput-Schwelle. benchmark.stats liefert Sekunden
    # pro Iteration (= published_count publishes). Median pro publish
    # = stats / published_count (NICHT modul-konstante; sonst Konsistenz-
    # Drift bei Constant-Refactor).
    median_seconds_per_run = benchmark.stats["median"]
    median_seconds_per_publish = median_seconds_per_run / published_count
    median_ops = 1.0 / median_seconds_per_publish

    assert median_seconds_per_publish <= _PUBLISH_LATENCY_LIMIT_SECONDS, (
        f"GG-RT-005 Throughput-Schwelle verletzt: "
        f"median publish-Latency = {median_seconds_per_publish * 1e6:.2f} us "
        f"(>= {_PUBLISH_LATENCY_LIMIT_SECONDS * 1e6:.2f} us); "
        f"median OPS = {median_ops:.0f} < {_GG_RT_005_MIN_OPS}"
    )
