# 062 — GG-PERSIST-009: Lauf-Loeschung nicht implementiert (MUSS-Luecke)

**Status:** Open — MUSS-Luecke aus dem §27.2-Re-Sweep (Slice 060)
**Datum:** 2026-07-10
**Quelle:** Slice-060-Traceability-Audit gegen den Code-Stand M8/v0.3.1.

---

## Befund

[`GG-PERSIST-009`](../../../../spec/lastenheft.md#gg-persist-009) (MUSS): „Die
Plattform MUSS Laufdaten eindeutig loeschen koennen" — Akzeptanz: ein Lauf
inkl. Telemetrie, Alarme, Snapshots und Metadaten ueber eine dokumentierte
Operation entfernbar, ohne andere Laeufe zu veraendern. Der `RunRepositoryPort`
bietet heute **kein** `delete`, und es gibt **keinen** `DELETE /runs/{id}`-
Endpoint — nur der Save/Load-Vertrag existiert.

## Erwartete Lieferung

- `RunRepositoryPort.delete(run_id)` + Postgres-Implementierung (kaskadiert
  ueber Telemetrie/Alarme/Snapshots/Metadaten, isoliert pro Lauf).
- `DELETE /runs/{id}`-Endpoint (dokumentierte Operation) mit typisiertem
  `ErrorResponse` bei unbekanntem Lauf.
- Tests: Loesch-Roundtrip (Bestand weg, andere Laeufe unveraendert) +
  Not-Found-Pfad.

## Aktivierungs-Kriterium

Naechster Slice an der Run-Persistenz-/API-Surface ODER wenn die MUSS-Abnahme
formell eingefordert wird.

## Wandert nach

`done/`, sobald die Loesch-Operation existiert und die Anforderung via
Slice/Welle nachverfolgbar ist (`make doc-trace`; §27.2-Status-Matrix in
Slice 066 entfernt).
