# 012 — Snapshot-Composition fuer den `SnapshotEnvelope` — Closure-Notiz

**Status:** Done — geschlossen 2026-05-17 mit Acceptance von
[`ADR 0010`](../../adr/0010-randomport-snapshot-as-mapping.md)
und der `TickLoop`-Composition aus M1 Welle 4. Das in §1 (Option A)
empfohlene Pattern ist umgesetzt.
**Datum:** 2026-05-17 (geoeffnet aus Welle-3-Review S1);
2026-05-17 ADR 0010 `Accepted`; 2026-05-17 Trigger-Closure.
**Quelle:** Welle-3-Review S1/N2/N4 (`docs(review)`-Befunde aus
Commit `ae20b4f`); Modul-Docstring von
`src/grid_gym/hexagon/core/simulation/scheduler.py` (Welle 3).
**Verlinkt:**
[`ADR 0007`](../../adr/0007-random-port.md) §5.1
(bytes-Vertrag, unveraendert),
[`ADR 0009`](../../adr/0009-randomport-snapshot-schema-rng-version.md)
(Snapshot-Schema, unveraendert),
[`ADR 0010`](../../adr/0010-randomport-snapshot-as-mapping.md)
(Schaerfung — Composition-API),
M1-Slice-Plan
[`M1-tick-loop-spine.md`](../done/M1-tick-loop-spine.md)
§3 Welle 4.

---

## Trigger (historisch)

Welle 2 und Welle 3 haben Snapshot-Vertraege mit
**inkonsistenten Rueckgabetypen** etabliert:

- `MersenneTwisterRandomPort.snapshot() -> bytes` (canonical-JSON).
- `Scheduler.snapshot() -> Mapping[str, object]`.

`SnapshotEnvelope` aus Welle 1 verlangt
`sub_snapshots: Mapping[str, Mapping[str, object]]`. Welle 4 muss
den `TickLoop` aus beiden komponieren — Drift war strukturell
absehbar.

Sekundaer:

- `SchedulerSnapshotFormatError`-Hierarchie als Pattern-Duplikat
  zu `RandomPortSnapshotFormatError`.
- Payload-Canonical-Validierung dupliziert sich beim dritten
  Subsystem.
- Snapshot-Codec-Free-Functions colokiert mit der besitzenden
  Klasse — Welle-2/3-Muster, das bei drei Subsystemen in ein
  Sub-Modul gehoert.

## Lieferung

- **ADR 0010 `Accepted`** (2026-05-17): `RandomPort.
  snapshot_as_mapping() -> Mapping[str, object]` als Composition-
  API. `snapshot() -> bytes` bleibt fuer Disk-Persistenz. Beide
  lesen aus `_build_payload()` als Single-Source-of-Truth →
  Drift strukturell ausgeschlossen.
- **TickLoop-Composition** (Welle 4b): `TickLoop.snapshot()`
  liefert `Mapping[str, object]` mit
  `sub_snapshots = {"scheduler": ..., "random_root": ...}`, beide
  Sub-Snapshots als `Mapping[str, object]`. Keine
  `json.loads`-Logik in der Domain.
- **TickLoop-Resume-Konsistenz**: `from_snapshot` prueft typisiert
  `clock.now() == state['simulation_time']` und
  `random.snapshot_as_mapping() == state['sub_snapshots']
  ['random_root']`. Resume-Drift wird hart erkannt.

## Was bewusst NICHT in Welle 4 geloest wurde

Trigger 012 §2/§3/§4 bleiben offen — sie sind keine Welle-4-
Voraussetzung mehr:

- **Generischer Snapshot-Codec**
  (`hexagon/core/serialization/snapshot_codec.py`) ist drei mal
  Pattern-Duplikat. Wird in Welle 5 (Scenario) refaktoriert,
  wenn der vierte Subsystem-Snapshot ansteht. Pre-mature
  abstraction in Welle 4 vermieden.
- **`SnapshotEnvelope.sub_snapshots`-Schaerfung** um Payload-
  Canonical-Pflicht (Trigger 012 §4) — separater Folge-Trigger
  bei Bedarf in Welle 5.
- **`assert_payload_canonical_compatible`-Free-Function**
  (Trigger 012 §3) — lebt heute als
  `Scheduler._assert_payload_canonical` und kann in Welle 5
  zusammen mit dem generischen Codec extrahiert werden.

## Wandert nach

`done/` (jetzt). Folge-Trigger 013 zu „Generischer Snapshot-Codec"
oeffnet sich, sobald Welle 5 ein viertes Subsystem (Scenario)
liefert.
