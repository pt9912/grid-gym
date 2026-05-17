# ADR 0010 — `RandomPort.snapshot_as_mapping()` fuer Snapshot-Envelope-Composition

**Status:** Accepted — kein Validierungs-Spike erforderlich
(Implementation-Pattern ist trivial: `_build_payload()` als
Single-Source-of-Truth, `snapshot()` und `snapshot_as_mapping()`
teilen ihn). Direkter `Proposed → Accepted`-Sprung per
`ADR 0006 §2`-Klausel.
**Datum:** 2026-05-17
**Status geaendert am:** 2026-05-17 — `Proposed → Accepted`.
**Bezug:** [`ADR 0007`](0007-random-port.md) §5.1 (Protocol-
Vertrag), [`ADR 0009`](0009-randomport-snapshot-schema-rng-version.md)
(Snapshot-Schema), [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
§3 (Erweiterung ohne Supersedes), Welle-1-`SnapshotEnvelope`
in `hexagon/core/domain/snapshot.py`,
[`docs/plan/planning/open/012-snapshot-composition.md`](../planning/open/012-snapshot-composition.md)
(Trigger, geschlossen durch diese ADR — wandert nach `done/`
synchron zu Welle-4-Closure).

---

## 1. Kontext

Welle 2 hat `MersenneTwisterRandomPort.snapshot() -> bytes`
(canonical-JSON) gegeben (`ADR 0007 §5.1`). Welle 3 hat
`Scheduler.snapshot() -> Mapping[str, object]` etabliert. Welle 1
hatte den `SnapshotEnvelope`-Vertrag fixiert:

```python
sub_snapshots: Mapping[str, Mapping[str, object]]
```

Welle 4 baut den `TickLoop`, der einen `SnapshotEnvelope` aus
Scheduler-State + Random-State + eigenen Feldern komponieren
muss. Hier prallt der `bytes`-Vertrag mit der
`Mapping[str, Mapping[str, object]]`-Konvention zusammen:

- Variante 1: TickLoop ruft `json.loads(random.snapshot().
  decode())` und faedelt das Mapping in den Envelope. Bringt
  `json.loads` in die Domain-Schicht — Codec-Wissen sickert in
  die Composition.
- Variante 2: `RandomPort.snapshot()` aendert den Rueckgabetyp
  auf `Mapping`. Brueche bestehenden ADR-0007-Vertrag,
  Superseding-pflichtig.
- **Variante 3 (diese ADR):** `RandomPort` bekommt zusaetzlich
  `snapshot_as_mapping() -> Mapping[str, object]`. `snapshot()`
  bleibt fuer Disk-Persistenz und Resume; `snapshot_as_mapping()`
  ist die Composition-API. Beide Methoden lesen aus einer
  internen `_build_payload()`-Funktion, sodass es nur EINEN
  Wahrheitspfad fuer das Snapshot-Schema gibt.

Trigger 012 (`docs/plan/planning/open/012-snapshot-composition.md`)
hatte Variante 3 als „Option A (empfohlen)" gelistet.

---

## 2. Entscheidung

`RandomPort`-Protocol bekommt eine zusaetzliche Methode:

```python
class RandomPort(Protocol):
    # ... bestehende Methoden ...

    def snapshot_as_mapping(self) -> Mapping[str, object]:
        """Liefert den State im `SnapshotEnvelope`-tauglichen
        Mapping-Format (`Mapping[str, object]`) mit dem gleichen
        Pflicht-Schluesselsatz wie `snapshot()` (siehe `ADR 0009 §2`).

        Implementations MUESSEN sicherstellen, dass
        `canonical_json(port.snapshot_as_mapping())
        == port.snapshot()` gilt — also dass beide Methoden aus
        derselben internen Quelle (`_build_payload()`-Pattern)
        gespeist werden.
        """
        ...
```

`snapshot() -> bytes` bleibt unveraendert (`ADR 0009 §2`-Schema).

`MersenneTwisterRandomPort` implementiert das Pattern:

```python
def _build_payload(self) -> dict[str, object]:
    rng_version, rng_state, gauss_next = self._rng.getstate()
    if gauss_next is not None:
        raise UnexpectedGaussNextError(...)
    return {
        "version": _SNAPSHOT_VERSION,
        "seed": self._seed,
        "sub_path": list(self._sub_path),
        "rng_version": rng_version,
        "rng_state": list(rng_state),
    }

def snapshot_as_mapping(self) -> Mapping[str, object]:
    return self._build_payload()

def snapshot(self) -> bytes:
    return canonical_json(self._build_payload())
```

---

## 3. Begruendung

- **Single-Source-of-Truth**: `_build_payload()` ist die einzige
  Stelle, an der das Schema konstruiert wird. Drift zwischen
  bytes- und Mapping-Variante ist strukturell ausgeschlossen.
- **Kein json.loads in der Domain**: `TickLoop` (in Welle 4)
  kann den Random-Sub-Snapshot direkt als Mapping in den
  `SnapshotEnvelope` einsetzen, ohne Encoder-Wissen zu
  importieren. Die Domain-Schicht bleibt frei von
  Serialisierungs-Details.
- **Kein Breaking-Change**: bestehende Aufrufer (Persistenz-
  Adapter, Disk-Resume) nutzen `snapshot()`-bytes unveraendert.
  Welle-4-Composition addiert nur einen neuen Pfad.
- **ADR 0007 + ADR 0009 bleiben gueltig**: diese ADR ergaenzt
  beide um eine zusaetzliche Methode, ohne den jeweils
  bestehenden Entscheidungstext zu schaerfen oder zu
  widerrufen. Reine Erweiterung per `ADR 0006 §3`.

Variante 2 (Breaking-Change) wurde verworfen: der
`bytes`-Rueckgabetyp ist fuer Disk-Persistenz natuerlich (kein
Encoder-Roundtrip in der Speicherlage). Variante 1 (`json.loads`)
wurde verworfen: bringt Codec-Wissen in die Composition-Schicht
und verletzt die etablierte Boundary.

---

## 4. Reichweite

- `RandomPort`-Protocol (`hexagon/ports/driven/random.py`):
  neue Methode `snapshot_as_mapping`.
- `MersenneTwisterRandomPort`
  (`adapters/driven/random_mt/mersenne_twister.py`): interne
  `_build_payload()`-Refaktorierung, beide Methoden teilen
  diese.
- `SnapshotEnvelope`-Vertrag bleibt unveraendert: weiterhin
  `Mapping[str, Mapping[str, object]]`. Diese ADR macht
  `snapshot_as_mapping()` zum Lieferanten fuer einen
  Sub-Snapshot-Eintrag.
- ADR 0007 / ADR 0009 bleiben textlich unveraendert (Accepted-
  Immutability per ADR 0006 §3).

---

## 5. Operative Artefakte

- `src/grid_gym/hexagon/ports/driven/random.py` —
  `RandomPort.snapshot_as_mapping` als Protocol-Methode mit
  Pflicht-Docstring.
- `src/grid_gym/adapters/driven/random_mt/mersenne_twister.py` —
  `_build_payload()` als private Methode, `snapshot()` und
  `snapshot_as_mapping()` rufen sie auf.
- `tests/unit/adapters/driven/random_mt/test_mersenne_twister.py`
  — neue Tests fuer
  `test_snapshot_as_mapping_returns_canonical_json_equivalent`
  und `test_snapshot_as_mapping_is_mapping_type`.
- `docs/plan/adr/README.md` ADR-Index: ADR 0010 als Schaerfung
  zu ADR 0007/ADR 0009 eingetragen.

---

## 6. Konsequenzen

- **Positiv:** `TickLoop` in Welle 4 baut den `SnapshotEnvelope`
  ohne Encoder-Layer. `sub_snapshots`-Konvention bleibt sauber
  Mapping-only.
- **Positiv:** Single-Source-of-Truth fuer das Schema
  ausgeschlossen Drift zwischen Composition- und Disk-Pfad.
- **Neutral:** Eine zusaetzliche Methode am Protocol — alle
  konkreten `RandomPort`-Implementations muessen sie liefern.
  Heute nur `MersenneTwisterRandomPort` existiert; spaetere
  Implementations (`MLRandomPort`, `AsyncRandomPort`) fuegen
  die Methode in ihrem eigenen Scope hinzu.

---

## 7. Nicht Gegenstand dieser ADR

- Generischer Snapshot-Codec
  (`hexagon/core/serialization/snapshot_codec.py`,
  `assert_payload_canonical_compatible`) — Trigger 012 §2/§3
  bleibt fuer Welle 5+ offen (`SchedulerSnapshotFormatError`-
  Pattern-Duplikat wird mit dem dritten Subsystem in Welle 5
  refaktoriert).
- `SnapshotEnvelope.sub_snapshots`-Vertragsschaerfung um
  Payload-Canonical-Pflicht (Trigger 012 §4) — separater
  Folge-Trigger nach Welle 4.
