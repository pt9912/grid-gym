"""OTLP-Log-Adapter (M3 Welle 6, ADR 0024 §2.2).

Implementiert `LogPort` und emittiert strukturierte Logs direkt
ueber die OTel-SDK-`Logger.emit(LogRecord)`-Surface. Pflicht-Felder
aus `GG-OTEL-002` (`level`, `message`, `run_id`, `module`, `event_id`,
`attributes`) werden zu OTel-Log-Records gemappt:

- `level` (String) → `SeverityNumber` + `severity_text` (Uppercase).
  Mapping-Tabelle deckt die typischen Werte ab; unbekannte Levels
  fallen auf `INFO`.
- `message` (String) → `body`.
- `run_id` / `module` / `event_id` / `attributes` → konsolidierte
  Attributes-Mapping am Log-Record. `event_id` traegt das Welle-5-
  Domain-Event-ID-Konzept; `run_id` matched ADR-0010-`RunMetadata.run_id`.

Direct-Emit (statt der OTel-`LoggingHandler`-Python-Logging-Bridge),
weil der globale Python-Logger-Singleton mit pytest-Test-Isolation
schlecht zusammenspielt (Handler-Persistenz ueber Test-Tear-Downs
hinaus) — wir konstruieren `LogRecord` selbst und uebergeben ihn an
den per Konstruktor injizierten Logger.

Per ADR 0024 §4.5.5 (D-4) wird **kein** `time.*` importiert — der
`observed_timestamp` des LogRecords wird von der OTel-SDK selbst
gesetzt, wenn `LogRecord(...)` ohne explizite Zeitwerte konstruiert
wird.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final, cast

from opentelemetry._logs import SeverityNumber
from opentelemetry.sdk._logs import LoggerProvider

# `LogRecord` ist in OTel-SDK 1.42 unter dem `_internal`-Modul
# implementiert; das public `opentelemetry.sdk._logs` exportiert
# `LoggerProvider`/`LoggingHandler` etc., aber `LogRecord` nicht
# in der `__init__`-Surface. Der `_internal`-Pfad ist der documented
# Implementation-Path; das `type: ignore[attr-defined]` adressiert nur
# den mypy-`__all__`-Sichtbarkeits-Schwund (kein API-Stabilitaets-Risiko
# — `LogRecord` ist seit OTel-Python 1.18 unter diesem Pfad stabil).
from opentelemetry.sdk._logs._internal import LogRecord  # type: ignore[attr-defined]

__all__ = ["OtlpLogAdapter"]

# String-Level → OTel-SeverityNumber. Lower-case-Key-Lookup unten.
_LEVEL_TO_SEVERITY: Final[dict[str, SeverityNumber]] = {
    "trace": SeverityNumber.TRACE,
    "debug": SeverityNumber.DEBUG,
    "info": SeverityNumber.INFO,
    "notice": SeverityNumber.INFO2,
    "warn": SeverityNumber.WARN,
    "warning": SeverityNumber.WARN,
    "error": SeverityNumber.ERROR,
    "critical": SeverityNumber.FATAL,
    "fatal": SeverityNumber.FATAL,
}

# Fallback fuer unbekannte Level-Strings (z. B. wenn ein Aufrufer einen
# Custom-Level wie "audit" emittiert). OTel-Spec sagt: `INFO` ist der
# neutrale Default.
_DEFAULT_SEVERITY: Final[SeverityNumber] = SeverityNumber.INFO


class OtlpLogAdapter:
    """Log-Adapter fuer OTLP-gRPC-Export (M3 Welle 6).

    Implementiert `LogPort` (`log(level, message, ...)`). Konstruktor
    erwartet ein bereits konfiguriertes `LoggerProvider` — der Adapter
    besitzt es nicht, sondern bekommt es injiziert (typisch von
    `build_otlp_adapters(config)` in C1.3c).
    """

    def __init__(
        self,
        logger_provider: LoggerProvider,
        *,
        instrumentation_name: str = "grid-gym",
    ) -> None:
        self._logger = logger_provider.get_logger(instrumentation_name)

    def log(  # noqa: PLR0913 — 6 Felder spiegeln das Pflicht-Set aus Architektur §15 `GG-OTEL-002` (`level`, `message`, `run_id`, `module`, `event_id`, `attributes`).
        self,
        level: str,
        message: str,
        *,
        run_id: str | None = None,
        module: str | None = None,
        event_id: str | None = None,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        """Emittiert ein strukturiertes Log-Event ueber OTLP."""
        severity_number = _LEVEL_TO_SEVERITY.get(level.lower(), _DEFAULT_SEVERITY)
        merged_attrs = self._merge_attributes(
            run_id=run_id,
            module=module,
            event_id=event_id,
            extra=attributes,
        )
        record = LogRecord(
            severity_text=level.upper(),
            severity_number=severity_number,
            body=message,
            attributes=cast("Mapping[str, Any]", merged_attrs),
        )
        self._logger.emit(record)

    @staticmethod
    def _merge_attributes(
        *,
        run_id: str | None,
        module: str | None,
        event_id: str | None,
        extra: Mapping[str, object] | None,
    ) -> dict[str, object]:
        """Baut den konsolidierten Attributes-Block aus den Pflicht-Feldern + extra.

        Pflicht-Felder werden nur eingetragen, wenn sie gesetzt sind
        (`None` faellt weg). `extra` ueberschreibt explizit gesetzte
        Pflicht-Felder, falls der Aufrufer das wollte — das ist
        bewusst nachgiebig, weil `attributes` per `GG-OTEL-002` die
        flexible Extension-Surface ist.
        """
        merged: dict[str, object] = {}
        if run_id is not None:
            merged["run_id"] = run_id
        if module is not None:
            merged["module"] = module
        if event_id is not None:
            merged["event_id"] = event_id
        if extra is not None:
            merged.update(extra)
        return merged
