# 039 — Oeffentliche API-Replay-Bedienung (1b-b-Carveout)

**Status:** Open — dokumentierter Scope-Carveout aus M7-Welle-1b-b
**Datum:** 2026-06-09
**Quelle:** M7-Welle-1b-b-C0 (Decision 1b-b-D-7;
[`docs/plan/planning/done/M7-welle-1b-b.md`](../done/M7-welle-1b-b.md)).

---

## Kontext

M7-Welle-1b-b liefert den **integrierten Replay-Lifecycle** (Core-
`TickLoop.finalize()`-Naht + `replay_diff_status`-Metrik +
`GG-TERM-002/003`-Preflight + `GG-SAFE-006`-Detail-Evidence). Die
Referenz-Lauf-Verknuepfung (`expected = read_samples(reference_run_
id)`) ist dort eine **Runtime/Test/Demo-interne Bindung** ueber die
Core-Kwargs `replay_snapshot` + `replay_reference_run_id` (1b-b-D-2).

Der `GG-MVP-002`-Determinismus-Beleg wird in 1b-b ueber einen
**Zwei-Lauf-E2E-Smoke** (Original + Replay-Lauf, leerer Diff)
erbracht. **Nicht** geliefert wird die **oeffentliche,
API-getriggerte Replay-Bedienung** — d. h. ein Endnutzer kann
ueber die HTTP-API noch keinen Lauf als „Replay von Lauf X"
starten.

## Offene Substanz (dieser Trigger)

- **`POST /runs` `replay_of: <run_id>`-Request-Feld** (oder ein
  dediziertes `POST /runs/{id}/replay`-Endpoint) — mit
  `RunCreateRequest`-Strict-Validation-Schaerfung ([`ADR 0045`](../../adr/0045-http-api-request-strict-validation.md):
  `strict=True`/`extra="forbid"`).
- **`RunMetadata`-`replay_of`-Spalte** (oder
  `ReplayComparisonMetadata`-Envelope) + **Alembic-Migration** —
  damit die Referenz-Bindung persistent + auditierbar am Lauf
  haengt (statt nur Runtime-Kwarg).
- **Verdrahtung** der persistierten `replay_of`-Bindung in den
  `finalize()`-Hook (statt der Test/Demo-internen Kwarg-Injektion).
- **API-Reject-Semantik** fuer unbekannte/abweichende
  `reference_run_id` (vor Lauf-Start, nicht erst im Preflight).

## Aktivierungs-Bedingung

- Reviewer-/Stakeholder-Forderung nach **API-getriggertem**
  Replay (statt Zwei-Lauf-E2E-Smoke) als `GG-MVP-002`-Beleg
  (siehe 1b-b-Risiko R1) — dann ggf. vorgezogen nach 1b-c.
- ODER Abnahme-CLI (`GG-MVP-003`, M7-Welle-2) braucht eine
  programmatische Replay-Bedienung.
- ODER Compliance-Bedarf, dass die Referenz-Bindung persistent
  am Lauf dokumentiert ist.

## Wandert nach

`done/`, sobald ein Lauf ueber die oeffentliche API als Replay
eines Referenzlaufs gestartet werden kann, die Bindung persistent
in `RunMetadata`/Envelope liegt und der `finalize()`-Hook sie
konsumiert.

## References

- [`../done/M7-welle-1b-b.md`](../done/M7-welle-1b-b.md)
  — 1b-b-D-7 (Scope-Schalter + Begruendung).
- [`../done/M7-welle-1.md`](../done/M7-welle-1.md)
  — [`GG-MVP-002`](../../../../spec/lastenheft.md#gg-mvp-002)-Gruppenplan.
- [`../../adr/0045-http-api-request-strict-validation.md`](../../adr/0045-http-api-request-strict-validation.md)
  — Strict-Request-Body-Vertrag fuer ein `replay_of`-Feld.
- [`../../adr/0048-replay-snapshot-port-reconstruction.md`](../../adr/0048-replay-snapshot-port-reconstruction.md)
  — `ReplaySnapshotPort` (die Bindung konsumiert ihn).
- [`../../../../spec/lastenheft.md`](../../../../spec/lastenheft.md#gg-mvp-002)
  — `GG-MVP-002`-Akzeptanz.
