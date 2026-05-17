# 012 — Snapshot-Composition fuer den `SnapshotEnvelope` (Welle 4)

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-17
**Quelle:** M1 Welle 3 Closure (Commit `75b0940`) plus M1 Welle 2
Lieferung. Konkret aus dem Modul-Docstring von
`src/grid_gym/hexagon/core/simulation/scheduler.py` und dem
externen Welle-3-Review (Befunde S1/N2/N4).
**Verlinkt:** [`ADR 0007`](../../adr/0007-random-port.md) §5.2,
[`ADR 0009`](../../adr/0009-randomport-snapshot-schema-rng-version.md),
M1-Welle-1-Konvention in
`src/grid_gym/hexagon/core/domain/snapshot.py`
(`SnapshotEnvelope.sub_snapshots: Mapping[str, Mapping[str, object]]`),
Slice-Plan
[`M1-tick-loop-spine.md`](../in-progress/M1-tick-loop-spine.md)
§3 Welle 4.

---

## Trigger

Welle 2 und Welle 3 haben Snapshot-Vertraege mit
**inkonsistenten Rueckgabetypen** etabliert:

- `MersenneTwisterRandomPort.snapshot() -> bytes` —
  canonical-JSON-Bytes (`ADR 0007 §5.2` / `ADR 0009`).
- `Scheduler.snapshot() -> Mapping[str, object]` — dict-Form
  (Welle 3).

Welle 1 hat den `SnapshotEnvelope` als
`Mapping[str, Mapping[str, object]]` fixiert
(`hexagon/core/domain/snapshot.py`) — alle Sub-Snapshots sollten
strukturell Maps sein, damit der Envelope sie ohne Encoder-Layer
zusammenfuegen kann. Der `bytes`-Vertrag aus Welle 2 bricht
das.

Sekundaer:

- **`SchedulerSnapshotFormatError`-Hierarchie ist eine
  wortwoertliche Kopie von `RandomPortSnapshotFormatError`**
  (`core/errors.py`). Pattern-Duplikat — zwei Instanzen sind
  Koinzidenz, eine dritte (TickLoop-Snapshot in Welle 4) waere
  ein klares Signal fuer einen generischen
  `SnapshotMissingKeysError` / `SnapshotWrongTypeError` etc. mit
  `subsystem: str`-Tag.
- **Payload-Canonical-Validierung** lebt heute in der
  `Scheduler.from_snapshot`-Validierung als Eager-Check (Welle 3
  S2-Polish). Bei einer geteilten Codec-Schicht waere das ein
  einziger Helper, nicht pro Sub-Snapshot dupliziert.
- **Snapshot-Codec als Free-Functions colokiert mit der
  besitzenden Klasse** ist das Welle-2/3-Muster (`_parse_...`,
  `_validate_...`, `_event_from_dict` jeweils auf Modul-Ebene
  neben `MersenneTwisterRandomPort` und `Scheduler`). Bei drei
  Subsystemen mit gleichem Bedarf gehoert das in ein eigenes
  `snapshot_codec`-Sub-Modul.

## Erwartete Lieferung

Wenn Welle 4 den TickLoop-`SnapshotEnvelope` baut, sind zu
entscheiden / zu liefern:

1. **Snapshot-Rueckgabetyp einheitlich** —
   `Mapping[str, object]` ist der natuerliche
   `SnapshotEnvelope.sub_snapshots`-Wertetyp. Optionen:
   - (A) `MersenneTwisterRandomPort.snapshot()` zusaetzlich
     ein `snapshot_mapping()` liefern lassen (oder als
     Replacement); die `bytes`-Variante als
     `snapshot_canonical_bytes()` umbenennen. Erfordert
     **Folge-ADR** zu `ADR 0007 §5.2`/`ADR 0009` (Vertrag
     aendert sich).
   - (B) Envelope wickelt jeden Sub-Snapshot in
     `json.loads(...)` zurueck. Nicht-konstruktiv (Verlust der
     Determinismus-Pruefung) — **nicht empfohlen**.
   - (C) Envelope traegt `sub_snapshots:
     Mapping[str, Mapping[str, object] | bytes]` als
     Union-Typ; Encoder unterscheidet beim Serialisieren.
     Verschiebt das Problem nur — **nicht empfohlen**.
   Empfohlene Richtung: (A).
2. **Generischer Snapshot-Codec** in
   `src/grid_gym/hexagon/core/serialization/snapshot_codec.py`
   (oder vergleichbar): `parse_snapshot(state, required_keys,
   subsystem) -> dict[str, object]`, plus typisierte
   `SnapshotMissingKeysError(subsystem, missing)`,
   `SnapshotWrongTypeError(subsystem, key, expected, actual)`
   etc. RandomPort/Scheduler/TickLoop nutzen alle die gleichen
   Bausteine.
3. **Payload-Canonical-Validierung als Free-Function**:
   `assert_payload_canonical_compatible(payload, subsystem,
   path)` — wird in jedem Snapshot-Codec-Pfad einmal aufgerufen.
4. **`SnapshotEnvelope.sub_snapshots`-Vertrag schaerfen**:
   Welle 1 hatte die `version: int`-Pflicht; Welle 4 ergaenzt
   die Pflicht „canonical-kompatibler Payload" (keine `float`,
   keine non-str-keys). Das ist im `__post_init__` zu pruefen,
   damit der Envelope kein Folge-`FloatNotAllowedError` erst
   beim Encoder einfaengt.

## Aktivierungs-Kriterium

Mit Welle 4 (TickLoop + Snapshot-Envelope), in der der
`SnapshotEnvelope` erstmals mehrere Sub-Snapshots aggregieren
muss. Dann ist (A) als Folge-ADR fixierbar — bis dahin bleibt
die Doppel-Welt aus `bytes` und `Mapping` ein Welle-4-Problem,
kein Welle-3-Bug.

## Wandert nach

- `next/`, sobald Welle 4 die Composition als Slice aktiviert,
- `in-progress/`, wenn die Folge-ADR-Schreibarbeit beginnt,
- `done/`, wenn der gemeinsame Codec liegt und ADR-Vertrag
  geschlossen.
