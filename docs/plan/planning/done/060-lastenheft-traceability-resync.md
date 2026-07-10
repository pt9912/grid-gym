# 060 — Lastenheft §27.2-Traceability-Matrix Status-Re-Sweep

**Status:** Done — 2026-07-10
**Datum:** 2026-07-10
**Quelle:** Session-Befund — die §27.2-„Anforderung zu Implementierung"-Matrix
meldete Dutzende gelieferte Anforderungen als `🔲` (Status-Drift analog zur
ADR-Index-Drift aus Slice 056).

---

## Befund

Die Status-Spalte der §27.2-Matrix
([`spec/lastenheft.md`](../../../../spec/lastenheft.md)) stand auf dem
M2-Welle-0c-Befuellungs-Stand (2026-05-18) und wurde nach M3..M8 nie
nachgezogen. 36 von ~40 `🔲`-Zeilen waren stale — das Meilenstein-Ziel war
abgeschlossen und die Arbeit geliefert (Fault-Subsystem, Multi-Agent-Bus,
OTLP, Web-UI, alle SOLLTE-Geraete/-Netz, Perf-Bench, SBOM, CI-Matrix,
Quality-Pipeline, Run-Control etc.).

## Lieferung

- **Status-Spalte gegen den Code-Stand (M8/v0.3.1) re-verifiziert**: 36 Zeilen
  von `🔲` auf `✓` (geliefert). Skript-gestuetzt, nach Kennung gekeyed, nur im
  §27.2-Scope.
- **Re-Sweep-Notiz + Legende** ergaenzt: die „kommt mit M[N]"-Formulierungen in
  der Implementierungs-Spalte sind historische Liefer-Ziele, erfuellt wo Status
  `✓` zeigt.
- **Zwei MUSS-Luecken aufgedeckt und praezisiert** (Beschreibung + Status als
  `🔲 Open`):
  - Replay-Zeit-Multiplikatoren (`0.5x/1x/10x/unbounded`) nicht implementiert
    → Trigger [`061`](../open/061-replay-time-multipliers.md).
  - Lauf-Loeschung (`DELETE`) nicht implementiert
    → Trigger [`062`](../open/062-run-deletion-operation.md).
- **Partial/Post-MVP praezisiert**: das 95%-Coverage-Ziel (Pflicht-Gate steht
  bei 90/85), Timescale/Influx-Persistenz, der Kubernetes-Deploy-Teil (Trigger
  [`037`](../open/037-deploy-007-010-multi-node-deployment.md)) und die
  SNMP/LwM2M-Adapter (Trigger
  [`047`](../open/047-device-management-protocol-adapters.md)).

## Verification-Evidence

- `make docs-check` gruen (0 Befunde). Doku-only, kein Runtime-Delta → **kein Release**.
- Verbleibende `🔲` in der Matrix = exakt die 7 echten Offen-/Partial-Punkte oben
  (verifiziert per Grep gegen `src/`, HTTP-Routes, `Makefile`-Schwellen).

## DoD

- [x] §27.2-Status-Spalte == realer Code-Stand.
- [x] Stale `🔲` (geliefert) → `✓`; echte Offen-Punkte praezise als `🔲` mit Grund.
- [x] MUSS-Luecken als Trigger 061/062 nachverfolgbar gemacht.

## Bezug

- [`spec/lastenheft.md`](../../../../spec/lastenheft.md) §27.2.
- Muster: Slice [`056`](056-adr-index-status-sync.md) (ADR-Index-Status-Sync).
