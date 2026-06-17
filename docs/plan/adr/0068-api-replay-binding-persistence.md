# ADR 0068 — API-Replay-Bindung: persistentes `replay_of` + Reject (Slice 039 Phase A)

**Status:** Accepted — Validierung mit Slice-039-Phase-A-Lieferung (`make
gates` gruen: lint/format-check/typecheck/arch-check/test-unit/
`coverage-gate`/`coverage-gate-critical` + `docs-check` + `accept-pin-check`;
Unit-Pins fuer Accept/Reject/Echo + Persistenz-Roundtrip, Postgres-Integration
um den `replay_of`-Roundtrip ergaenzt).
**Datum:** 2026-06-17
**Bezug:**

- [`ADR 0049`](0049-replay-lifecycle-finalize-hook.md) §2.2/§7 — die
  Referenzlauf-Bindung war dort **Runtime/Test/Demo-intern** (Core-Kwarg
  `replay_reference_run_id`); ADR 0049 §7 vertagt die **oeffentliche
  API-Replay-Bedienung** (Trigger 039). Diese ADR macht die Bindung
  **persistent + API-getrieben** (Phase A).
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) — Schaerfung-ohne-Supersedes
  (Form-Anker; additives `RunMetadata`-Feld + API-Feld).
- [`ADR 0037`](0037-http-api-surface-pattern.md) §2.1 — HTTP-API-Surface
  (`POST /runs`); diese ADR ergaenzt ein Request-/Response-Feld.
- [`ADR 0045`](0045-http-api-request-strict-validation.md) — `_BaseRequest`-
  Strict-Mode (`strict=True`/`extra="forbid"`) traegt das `replay_of`-Feld.
- [`ADR 0067`](0067-run-end-seam-and-partial-run.md) — Schwester-Slice (040,
  Run-End-Naht); der `finalize()`-Konsum der persistierten Bindung (Phase B)
  baut auf der dort garantierten Naht auf.
- [Trigger 039](../planning/in-progress/039-api-replay-trigger-surface.md)
  — Forward-Carveout (1b-b-D-7).

---

## 1. Kontext

[`ADR 0049`](0049-replay-lifecycle-finalize-hook.md) §2.2 bindet einen Replay-
Lauf an seinen Referenzlauf ueber den **Core-Kwarg** `replay_reference_run_id`
— eine Runtime/Test/Demo-interne Injektion. Ein Endnutzer kann ueber die
HTTP-API **keinen** Lauf als „Replay von Lauf X" anlegen, und die Bindung ist
**nicht persistent/auditierbar** am Lauf dokumentiert (Trigger 039).

Slice 039 ist zweiphasig (Slice-Doc): **Phase A** (diese ADR) liefert die
**persistente, API-getriebene Bindung + Reject**; **Phase B** (Folge) verdrahtet
die persistierte Bindung in den `finalize()`-Hook (haengt am Run-Execution-Pfad,
der einem API-Lauf einen `TickLoop` baut).

---

## 2. Entscheidung

### §2.1 `RunMetadata.replay_of` + Migration

NEU additives, optionales Feld `replay_of: str | None = None` auf
`RunMetadata` (`hexagon/core/domain/run.py`). `None` = regulaerer Lauf;
Default haelt bestehende Konstruktionen byte-stabil. Die Postgres-Persistenz
bekommt eine **nullable** `replay_of`-Spalte ueber die additive Alembic-
Migration `0003_add_replay_of` (kein Backfill — Bestands-Zeilen sind regulaere
Laeufe → `NULL`); `InMemoryRunRepository` traegt das Feld automatisch
(speichert die Frozen-Dataclass direkt). `replay_of` ist **kein**
[`GG-TERM-002`](../../../spec/lastenheft.md#gg-term-002)/003-Reproduzierbarkeits-Feld (es ist eine Referenz, kein
Konfigurations-Merkmal) — der Preflight aus ADR 0049 §2.3 bleibt unberuehrt.

### §2.2 `POST /runs` `replay_of` + Reject

`RunCreateRequest` (`_BaseRequest`, ADR 0045) bekommt ein optionales
`replay_of: str | None = None`. Der `POST /runs`-Handler prueft **vor dem
Anlegen**: ist `replay_of` gesetzt und der Referenzlauf **nicht** vorhanden
(`run_repository.exists(...)` → `False`), antwortet er **HTTP 422**
`reference_run_not_found` ([`GG-API-004`](../../../spec/lastenheft.md#gg-api-004)-`ErrorResponse`-Format) und legt
**keinen** Lauf an. Reject **vor** Lauf-Start, nicht erst im
`finalize()`-Preflight (Trigger 039). Bei gueltiger Referenz wird `replay_of`
in der `RunMetadata` persistiert + in der `RunCreateResponse` geechot.

### §2.3 Lese-Surface

`RunCreateResponse` + `RunDetailResponse` (`GET /runs/{id}`) exponieren
`replay_of` — die Bindung ist damit auditierbar abrufbar.

### §2.4 finalize()-Konsum = Phase B (out-of-scope hier)

Der `finalize()`-Hook konsumiert die **persistierte** `replay_of`-Bindung
(statt des Runtime-Kwargs) erst, wenn fuer einen API-erstellten Lauf ein
`TickLoop` gebaut wird. Das ist **Phase B** dieses Slices und haengt am
Run-Execution-/Multi-Run-Driver-Pfad — eigener Folge-Schritt.

---

## 3. Begruendung

- **Persistent + auditierbar.** Die Referenz-Bindung haengt am Lauf (DB-Zeile +
  API-Response) statt nur als fluechtiger Runtime-Kwarg — Compliance-/Audit-
  Anforderung aus Trigger 039.
- **Reject vor Start.** Ein `replay_of` auf einen nicht-existenten Lauf ist ein
  Client-Fehler; ihn vor dem Anlegen abzulehnen verhindert eine unaufloesbare
  Bindung (statt sie erst im Terminal-Preflight als stillen no-op zu entdecken).
- **Additiv (ADR 0011).** `RunMetadata`/`POST /runs`/ADR 0049 bleiben textlich
  unveraendert; ein optionales Feld + eine nullable Spalte + ein Reject-Pfad.

---

## 4. Reichweite

- NEU `RunMetadata.replay_of` (`domain/run.py`) + Migration
  `0003_add_replay_of` + `PostgresRunRepository`-INSERT/SELECT-Mapping
  (`InMemoryRunRepository` automatisch).
- `RunCreateRequest`/`RunCreateResponse`/`RunDetailResponse`-`replay_of`-Feld
  (`_schemas.py`); `POST /runs`-Reject + Persist + Echo (`app.py`); `GET
  /runs/{id}`-Durchreichung (`_runs_router.py`).
- Unit-Pins (`test_app.py`): Accept/Echo/Persist, Reject-422, Default-`None`,
  `GET`-Exposure. Postgres-Integration um `replay_of`-Roundtrip ergaenzt.
- ADR-Index NEU ADR-0068-Zeile.
- **Unberuehrt:** `finalize()`/`diff_replay()`/`replay_reference_run_id`-Kwarg
  (ADR 0049), `GG-TERM`-Preflight, `control_state`-Matrix.

---

## 5. Konsequenzen

- **Positiv:** ein Lauf laesst sich per oeffentlicher API als Replay von X
  anlegen; die Bindung ist persistent + auditierbar; ungueltige Referenz wird
  frueh + typisiert abgelehnt.
- **Neutral:** der `finalize()`-Hook konsumiert die persistierte Bindung noch
  nicht (Phase B) — ein API-Replay-Lauf traegt die Bindung, der Diff laeuft
  bis Phase B weiter ueber den Runtime-Kwarg (Demo/Test).
- **Neutral (Pin):** `replay_of=None`-Default → bestehende `POST /runs`-Pfade +
  `RunMetadata`-Roundtrips byte-stabil.

---

## 6. Nicht Gegenstand dieser ADR

- **`finalize()`-Konsum der persistierten Bindung** (Phase B, Trigger 039) —
  haengt am Run-Execution-Pfad.
- **Dediziertes `POST /runs/{id}/replay`-Endpoint** — die Feld-Form auf
  `POST /runs` ist gewaehlt (minimale Surface).
- **Abweichungs-Detektion** jenseits Existenz (z. B. `scenario_hash`-Mismatch
  der Referenz schon bei Lauf-Start) — der `GG-TERM`-Preflight (ADR 0049 §2.3)
  deckt das zum `finalize()`-Zeitpunkt ab.
- **`started_at`/`ended_at`-Timestamp-Pflege** — eigener Scope (ADR 0049 §7).
