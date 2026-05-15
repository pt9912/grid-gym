# 006 — `--strict-bytes`-Modus aktivieren

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-15
**Quelle:** [`ADR 0005`](../../adr/0005-type-check-gate.md) §6

---

## Trigger

`GG-DATA-005` verlangt UTF-8-Bytes als Vertragsschnittstelle der
kanonischen Serialisierung (A-2). ADR 0005 nennt:

> Aktivierung des `--strict-bytes`-Modus (bei `bytes`/`str`-Trenn-
> scharfe) sobald das Domain-Modell konsolidiert ist
> (`GG-DATA-005` UTF-8-Bytes-Vertrag).

## Erwartete Lieferung

- `[tool.mypy]`-Erweiterung um `strict_bytes = true` (oder
  Eintrag in `enable_error_code`, je nach mypy-Version).
- Pruefung, dass kein `bytes ↔ str`-Implicit-Coercion im Kern
  passiert (Persistenz, Replay-Diff, WebSocket-Frame).
- Anpassung der Test-Suite, falls Tests bisher `bytes` und `str`
  vermischt haben.

## Aktivierungs-Kriterium

Sobald `core/domain/*` und `core/serialization/*` konsolidiert sind
und die ersten Konsumenten (Persistenz, Replay, WebSocket) ihre
Bytes-Schreibpfade nutzen.

## Wandert nach

- `next/`, sobald Domain-Modell und Encoder produktiv sind,
- `in-progress/`, wenn Konfigurations-Slice geplant ist.
