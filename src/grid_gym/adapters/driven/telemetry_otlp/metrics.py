"""OTLP-Metrics-Adapter (M3 Welle 6, ADR 0024 §2.3 + §4.5.2).

Implementiert `MetricsPort` mit drei Methoden, jede mappt auf das
passende OTel-Metrics-Instrument:

- `increment(name, value, attributes)` → OTel-`Counter.add(...)`
  (monoton steigend; Welle-5-`tick_count` ist der erste Konsument,
  ADR 0024 §4.5.2 fixiert das Counter-Naming).
- `gauge(name, value, attributes)` → OTel-`Gauge.set(...)` (momentan-
  Wert; Welle-5-`event_queue_len` ist der erste Konsument).
- `observe(name, value, attributes)` → OTel-`Histogram.record(...)`
  (Verteilung; Welle 5 hat keinen Konsumenten — siehe ADR 0024
  §4.5.3, `tick_duration_ms` ist OTLP-Adapter-Material; der Histogram-
  Pfad steht hier fuer Welle-6-OTLP-extern instrumentierte Werte
  und ist nicht von TickLoop angesteuert).

Instrument-Caching: jeder Name wird beim ersten Aufruf zu einem
OTel-Instrument der jeweiligen Familie erzeugt; Folge-Aufrufe
benutzen den gecachten Eintrag. Das matched die OTel-Konvention
(Instrumente sind langlebig, Aufrufe sind billig) und vermeidet
wiederholtes `create_counter`/`create_gauge`/`create_histogram`.
Cross-Family-Kollisionen (gleicher Name als Counter und Gauge)
sind nicht abgefangen — der Aufrufer ist verantwortlich, eine
saubere Namenskonvention zu fuehren (ADR 0024 §4.5.2: Counter
`*_count`, Gauge `*_len` / `*_index`).

Thread-Safety: die OTel-Instrumente sind thread-safe; das interne
Instrument-Cache-Dict ist es nicht (Welle-6-Use-Case: single-threaded
TickLoop).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from opentelemetry.sdk.metrics import MeterProvider

__all__ = ["OtlpMetricsAdapter"]


class OtlpMetricsAdapter:
    """Metrics-Adapter fuer OTLP-gRPC-Export (M3 Welle 6).

    Implementiert `MetricsPort` (`increment`/`gauge`/`observe`).
    Konstruktor erwartet ein bereits konfiguriertes `MeterProvider` —
    der Adapter besitzt es nicht, sondern bekommt es injiziert
    (typisch von `build_otlp_adapters(config)` in C1.3c).
    """

    def __init__(
        self,
        meter_provider: MeterProvider,
        *,
        instrumentation_name: str = "grid-gym",
    ) -> None:
        self._meter = meter_provider.get_meter(instrumentation_name)
        # Per-Instrument-Caches; gefuellt lazy beim ersten Aufruf.
        # Typing als `Any`, weil OTel-SDK 1.42 die konkreten Instrument-
        # Klassen (`Counter`/`Gauge`/`Histogram`) unterschiedlich
        # exponiert — `_Gauge` ist privat, ein Mix aus public und
        # `_internal`-Imports waere drift-anfaellig. Runtime-API
        # (`counter.add`/`gauge.set`/`histogram.record`) bleibt stabil.
        self._counters: dict[str, Any] = {}
        self._gauges: dict[str, Any] = {}
        self._histograms: dict[str, Any] = {}

    def increment(
        self,
        name: str,
        value: int = 1,
        *,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        """Inkrementiert einen Counter."""
        counter = self._counters.get(name)
        if counter is None:
            counter = self._meter.create_counter(name)
            self._counters[name] = counter
        counter.add(value, attributes=self._to_otel_attributes(attributes))

    def gauge(
        self,
        name: str,
        value: float,
        *,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        """Setzt einen Gauge-Wert."""
        gauge = self._gauges.get(name)
        if gauge is None:
            gauge = self._meter.create_gauge(name)
            self._gauges[name] = gauge
        gauge.set(value, attributes=self._to_otel_attributes(attributes))

    def observe(
        self,
        name: str,
        value: float,
        *,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        """Beobachtet einen Verteilungs-Wert (Histogram-Record)."""
        histogram = self._histograms.get(name)
        if histogram is None:
            histogram = self._meter.create_histogram(name)
            self._histograms[name] = histogram
        histogram.record(value, attributes=self._to_otel_attributes(attributes))

    @staticmethod
    def _to_otel_attributes(
        attributes: Mapping[str, object] | None,
    ) -> Mapping[str, Any] | None:
        """Konvertiert Mapping-basierte Attributes zu OTel-konformem `dict | None`.

        Rueckgabetyp `Mapping[str, Any]` matched die OTel-API-Default-
        Konvention; vgl. `OtlpTraceAdapter._to_otel_attributes` fuer die
        gleiche Begruendung (Port-Layer-Vertrag breiter als OTel-SDK-
        Vertrag).
        """
        if attributes is None:
            return None
        return cast("Mapping[str, Any]", dict(attributes))
