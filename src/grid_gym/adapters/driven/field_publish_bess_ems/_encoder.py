"""Reiner bess-ems-Feldvertrags-Encoder (Slice 077 S2a, ADR 0078 §2.2/§2.3).

Uebersetzt grid-gyms per-Punkt-Battery-Telemetrie + Fault-Surface eines
`(battery, tick)` in die **breiten** bess-ems-Envelope-Frames (`telemetry`/
`status`/`fault`). **Pur** (kein MQTT, kein Driver, kein I/O) — direkt gegen das
publizierte Schema (`$defs.telemetry`) + die Golden-Vektoren strukturell testbar.

Feld-Mapping (ADR 0078 §2.2), gegen die lokalen bess-ems-Golden-Vektoren gepinnt:

- `offset_millis` ← `simulation_time` (ms seit Lauf-Start, **integer**).
- `soc_percent` ← `soc_pct`, `temperature_celsius`/`dc_voltage`/`soh_percent`/
  `reactive_power_kvar` 1:1 aus den [`ADR 0077`]-Emissionen.
- **`active_power_kw` = -`power_kw`** (Vorzeichen-Flip: grid-gym laedt mit **+**,
  bess-ems zeigt Laden als **-**; Golden `telemetry-charging`).
- **`dc_current` abgeleitet** = `active_power_kw·1000 / dc_voltage` (P=V·I;
  Vorzeichen folgt `active_power_kw`; Frame-Spannung).
- `available`/`fault_status` aus der Fault-Surface ([`ADR 0077`] §2.5).

Werte fliessen als `Decimal` (→ `canonical_json`-Fixed-Point-**Zahl**, kein
`float`/String-Bruch); auf 6 Nachkommastellen quantisiert (`GG-DATA-005`).
`offset_millis` als `int`, `available` als `bool`, `fault_status` als `str`.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Final

_ZERO: Final[Decimal] = Decimal(0)
_THOUSAND: Final[Decimal] = Decimal(1000)
_QUANTUM: Final[Decimal] = Decimal("0.000001")
_PRECISION: Final[int] = 28

# Battery-Metrik-Namen (grid-gym-Emissionen, ADR 0077).
_METRIC_SOC_PCT: Final[str] = "soc_pct"
_METRIC_POWER_KW: Final[str] = "power_kw"
_METRIC_DC_VOLTAGE: Final[str] = "dc_voltage"
_METRIC_SOH_PCT: Final[str] = "soh_percent"
_METRIC_REACTIVE: Final[str] = "reactive_power_kvar"
_METRIC_TEMPERATURE: Final[str] = "temperature_celsius"

# Pflicht-Metriken fuer einen konformen `telemetry`-Frame (die Battery muss die
# vollstaendigen Field-Envelope-Bloecke tragen, ADR 0078 §2.5).
REQUIRED_METRICS: Final[frozenset[str]] = frozenset(
    {
        _METRIC_SOC_PCT,
        _METRIC_POWER_KW,
        _METRIC_DC_VOLTAGE,
        _METRIC_SOH_PCT,
        _METRIC_REACTIVE,
        _METRIC_TEMPERATURE,
    }
)

# `fault_status`-Werte, die den `fault`-Topic **unterdruecken** (ADR 0078 §2.3;
# Golden `fault-suppressed-ok`).
_FAULT_SUPPRESSED: Final[frozenset[str]] = frozenset({"ok", ""})

# Always-Accept-`command_ack`-Reason (ADR 0078 §2.9; Golden `command-ack-accepted-echo`).
_ACK_ACCEPTED_REASON: Final[str] = "accepted"


class BessEmsEncoderMissingMetricError(ValueError):
    """Ein `telemetry`-Frame ist nicht bildbar: der Battery fehlen Pflicht-
    Metriken (die Field-Envelope-Bloecke aus [`ADR 0077`] sind nicht konfiguriert).
    Fail-fast statt eines Schema-invaliden Frames (ADR 0078 §2.5)."""

    def __init__(self, asset_id: str, missing: tuple[str, ...]) -> None:
        super().__init__(
            f"bess-ems telemetry frame for asset {asset_id!r} not buildable: "
            f"missing required battery metrics {missing} — configure the ADR-0077 "
            "field-envelope blocks (health/dc_bus/reactive/thermal)."
        )
        self.asset_id: str = asset_id
        self.missing: tuple[str, ...] = missing


def _dc_current(active_power_kw: Decimal, dc_voltage: Decimal) -> Decimal:
    """Abgeleiteter DC-Strom `= active_power_kw·1000 / dc_voltage` (P=V·I),
    quantisiert auf 6 Nachkommastellen. `dc_voltage == 0` → `0` (kein
    Div-by-Zero; die ADR-0077-`DcBusConfig` haelt `dc_voltage > 0`)."""
    if dc_voltage == _ZERO:
        return _ZERO
    with localcontext() as ctx:
        ctx.prec = _PRECISION
        ctx.rounding = ROUND_HALF_EVEN
        return (active_power_kw * _THOUSAND / dc_voltage).quantize(_QUANTUM)


def encode_telemetry(
    asset_id: str,
    offset_millis: int,
    metrics: Mapping[str, Decimal],
    *,
    available: bool,
    fault_status: str,
) -> dict[str, object]:
    """Baut den breiten `telemetry`-Envelope-Frame (10 Pflicht-Felder,
    `$defs.telemetry`). Fehlt eine Pflicht-Metrik → `BessEmsEncoderMissingMetricError`
    (fail-fast, ADR 0078 §2.5)."""
    missing = REQUIRED_METRICS - metrics.keys()
    if missing:
        raise BessEmsEncoderMissingMetricError(asset_id, tuple(sorted(missing)))
    active_power_kw = -metrics[_METRIC_POWER_KW]
    dc_voltage = metrics[_METRIC_DC_VOLTAGE]
    return {
        "offset_millis": offset_millis,
        "soc_percent": metrics[_METRIC_SOC_PCT],
        "soh_percent": metrics[_METRIC_SOH_PCT],
        "active_power_kw": active_power_kw,
        "reactive_power_kvar": metrics[_METRIC_REACTIVE],
        "dc_voltage": dc_voltage,
        "dc_current": _dc_current(active_power_kw, dc_voltage),
        "temperature_celsius": metrics[_METRIC_TEMPERATURE],
        "available": available,
        "fault_status": fault_status,
    }


def encode_status(offset_millis: int, *, available: bool, fault_status: str) -> dict[str, object]:
    """Baut den `status`-Frame `{available, fault_status, offset_millis}`
    (ADR 0078 §2.3, Golden `status-nominal`)."""
    return {
        "available": available,
        "fault_status": fault_status,
        "offset_millis": offset_millis,
    }


def encode_fault(offset_millis: int, *, fault_status: str) -> dict[str, object] | None:
    """Baut den `fault`-Frame `{fault_status, offset_millis}` — **nur** wenn
    `fault_status ∉ {ok, ""}`; sonst `None` (der `fault`-Topic wird unterdrueckt,
    ADR 0078 §2.3, Golden `fault-suppressed-ok`)."""
    if fault_status in _FAULT_SUPPRESSED:
        return None
    return {"fault_status": fault_status, "offset_millis": offset_millis}


def encode_command_ack(
    command_id: str,
    dispatched_at: str,
    *,
    accepted: bool = True,
    reason: str = _ACK_ACCEPTED_REASON,
) -> dict[str, object]:
    """Baut den Always-Accept-`command_ack`-Frame (ADR 0078 §2.9, `$defs.command_ack`;
    Golden `command-ack-accepted-echo`): `{command_id` (aus dem empfangenen Command
    echoed)`, accepted, dispatched_at, reason}`.

    `dispatched_at` ist ein **ISO-8601-UTC-String** (Schema-`type: string`, Golden
    `"1970-01-01T00:00:00Z"`) — Wall-Clock, vom Adapter injiziert (**exogen**, geht
    nicht in den Determinismus-Vertrag ein, §2.9). **Echo ≠ Feldeffekt**: das Ack
    haelt bess-ems' `MqttCommandSink` vom `ack-timeout`→Safe-Stop ab; der Sollwert-
    Effekt-Pfad bleibt Modbus (ADR 0076/Slice 075)."""
    return {
        "command_id": command_id,
        "accepted": accepted,
        "dispatched_at": dispatched_at,
        "reason": reason,
    }


def command_id_from_payload(payload: Mapping[str, object]) -> str | None:
    """Extrahiert `command_id` aus einem dekodierten bess-ems-`command`-Objekt
    (`$defs.command` required `command_id: string`). Fehlt es / ist es kein
    nicht-leerer String → `None` (der Adapter sendet dann kein Ack; tolerant gegen
    Fremd-/Fehl-Payloads, kein Raise im Loop-Thread)."""
    command_id = payload.get("command_id")
    if isinstance(command_id, str) and command_id:
        return command_id
    return None
