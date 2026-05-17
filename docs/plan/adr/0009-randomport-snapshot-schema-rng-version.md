# ADR 0009 — Snapshot-Schema fuer `MersenneTwisterRandomPort`: `rng_version` + `rng_state`

**Status:** Accepted — kein Validierungs-Spike erforderlich
(Implementierung in M1 Welle 2 bereits abgenommen, Tests gruen
gegen das in dieser ADR codifizierte Schema). Direkter
`Proposed → Accepted`-Sprung per `ADR 0006 §2`-Klausel
(„Eine ADR ohne Validierungsbedarf darf direkt
`Proposed → Accepted` springen").
**Datum:** 2026-05-17
**Status geaendert am:** 2026-05-17 — `Proposed → Accepted`.
**Bezug:** [`ADR 0007`](0007-random-port.md) §5.2 (Snapshot-
Skizze, abgeloeste Felder),
[`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
§3 (Erweiterungs-ADR ohne `Supersedes`, weil rein erweiternd),
M1-Slice-Plan
[`docs/plan/planning/in-progress/M1-tick-loop-spine.md`](../planning/in-progress/M1-tick-loop-spine.md)
§3 Welle 2,
[`docs/plan/planning/done/003-random-port-adr.md`](../planning/done/003-random-port-adr.md)
(Trigger-Closure).

---

## 1. Kontext

`ADR 0007 §5.2` skizziert das `MersenneTwisterRandomPort`-
Snapshot-Format als `canonical_json`-Bytes mit den Feldern
`version`, `seed`, `sub_path` und `state`. Die Implementation in
`src/grid_gym/adapters/driven/random_mt/mersenne_twister.py` hat
das Snapshot-Schema bei der Welle-2-Lieferung in zwei separate
Felder geteilt: `rng_version` und `rng_state`. Diese Drift
zwischen ADR-Text und produktivem Code ist im externen
Welle-2-Review (P2) gemeldet worden.

ADR 0007 ist seit 2026-05-17 `Accepted` und damit per
`ADR 0006 §3` im Entscheidungstext immutable. Eine Schaerfung
braucht eine Folge-ADR — diese.

---

## 2. Entscheidung

Das `canonical_json`-Snapshot-Schema von
`MersenneTwisterRandomPort.snapshot()` ist verbindlich:

```json
{
  "version": 1,
  "seed": <int>,
  "sub_path": [<str>, ...],
  "rng_version": <int>,
  "rng_state": [<int>, ..., <int>]
}
```

- `version: int` — Envelope-Schema-Version. Heute `1`. Eine
  Erhoehung erfordert eine weitere Folge-ADR zu dieser hier.
- `seed: int` — Wurzel-Seed des Generators (`ADR 0007 §5.2`).
- `sub_path: list[str]` — Liste der Sub-Port-Namen vom Wurzel-
  Generator bis hierhin; `[]` fuer den Root-Port.
- `rng_version: int` — Versions-Marker aus
  `random.Random.getstate()[0]`. CPython 3.13+/3.14 liefert
  heute `3`; spaetere CPython-Versionen koennten das Tuple-
  Layout aendern.
- `rng_state: list[int]` — `random.Random.getstate()[1]` als
  Liste, exakt 625 Elemente (624 MT-Werte + 1 Index). Laenge
  ist Pflicht und wird im Resume-Pfad typisiert geprueft
  (`RandomPortSnapshotInvalidRngStateLengthError`).

`random.Random.getstate()[2]` (`gauss_next`) wird **nicht**
persistiert: `RandomPort.next_int`/`next_float` rufen niemals
`random.gauss()` auf, ein non-`None`-Wert deutet auf externe
Manipulation hin und wird im `snapshot()`-Pfad mit
`UnexpectedGaussNextError` typisiert abgelehnt
(siehe `ADR 0007 §5.2` und Code-Kommentar).

---

## 3. Begruendung

Drei Gruende fuer das Zwei-Felder-Layout statt eines einzigen
`state`:

1. **Audit der CPython-`getstate`-Version.** Die `version_int`-
   Komponente aus `getstate()` ist Teil des Mersenne-Twister-
   Vertrags; ohne explizites Feld muesste der Resume-Pfad sie
   implizit als Konstante annehmen (`3` in CPython 3.13+). Ein
   zukuenftiger CPython-Bump auf `version_int = 4` wuerde dann
   ohne typisierte Fehlermeldung Drift erzeugen. Mit
   `rng_version` als Feld kann `from_snapshot` die Versions-
   Kompatibilitaet typisiert pruefen (`RandomPortVersionError`).
2. **Trennung „Envelope-Schema" vs. „PRNG-getstate-Layout".**
   `version: int` zaehlt die Aenderungen am `canonical_json`-
   Envelope (z. B. „neues `tool_version`-Feld kommt hinzu");
   `rng_version` zaehlt die Aenderungen am Mersenne-Twister-
   `getstate()`-Format. Beide Versionen sind orthogonal — eine
   gemeinsame Versionszahl waere irrefuehrend.
3. **`canonical_json`-Determinismus.** Das `rng_state`-Tupel
   enthaelt 625 Integer; ein verschachteltes Single-`state`-Tupel
   `(version, [int, ...], None)` muesste entweder als
   heterogenes Array oder als Sub-Objekt persistiert werden.
   Die Aufteilung in zwei Felder ist deterministischer im
   `canonical_json`-Sort (kein heterogenes Top-Level-Array).

---

## 4. Reichweite

- Diese ADR beschreibt ausschliesslich das Snapshot-Schema von
  `MersenneTwisterRandomPort`. `MLRandomPort` und
  `AsyncRandomPort` (`ADR 0007 §6`) bekommen je eine eigene
  Folge-ADR mit eigenem Snapshot-Schema.
- ADR 0007 §5.2 bleibt per ADR 0006 §3 im Entscheidungstext
  unveraendert. Diese ADR liegt nebenan und schaerft den
  Snapshot-Block. Aufrufer, die das Schema implementieren,
  lesen beide ADRs.

---

## 5. Operative Artefakte

Die folgenden Stellen sind bereits in M1 Welle 2 ausgeliefert
und entsprechen dem in §2 fixierten Schema:

- `src/grid_gym/adapters/driven/random_mt/mersenne_twister.py`
  `MersenneTwisterRandomPort.snapshot()` produziert das oben
  beschriebene Layout (Kommentar im Modul-Docstring).
- `_validate_parsed_keys`, `_require_int`,
  `_require_list_of_str`, `_require_list_of_int` und die
  Konstante `_RNG_STATE_LENGTH = 625` setzen die Pflicht-
  Schluesselmenge und das 625-Element-Constraint um.
- `src/grid_gym/hexagon/core/errors.py` traegt die typisierten
  Fehler:
  `RandomPortSnapshotMissingKeysError`,
  `RandomPortSnapshotWrongTypeError`,
  `RandomPortSnapshotListItemWrongTypeError`,
  `RandomPortSnapshotInvalidRngStateLengthError`,
  `RandomPortVersionError`.
- `tests/unit/adapters/driven/random_mt/test_mersenne_twister.py`
  testet das vollstaendige Schema inkl. aller Negativ-Pfade.

---

## 6. Konsequenzen

- **Positiv:** Snapshot-Vertrag ist auditierbar — beide
  Versions-Achsen sind explizit, der Pflicht-Schluesselsatz ist
  fixiert, alle Drift-Pfade sind typisiert.
- **Positiv:** Die externe Welle-2-Review-Drift P2 ist
  geschlossen.
- **Neutral:** Snapshot-Bytes sind ein paar Bytes laenger als
  bei der `state`-Skizze in `ADR 0007 §5.2` — `canonical_json`
  ist robust dagegen.
- **Negativ:** Wer nur `ADR 0007 §5.2` liest, sieht das alte
  Schema. Mitigation: `ADR 0007 §5.2`-Snippet kommentiert in
  `mersenne_twister.py` als „abgeloest durch ADR 0009"
  verlinkt.

---

## 7. Nicht Gegenstand dieser ADR

- Versions-Bumps des Envelope-Schemas (z. B. wenn `tool_version`
  oder `created_at` als Felder hinzukommen). Bei Bedarf eigene
  Folge-ADR.
- Versions-Bumps von `rng_version` (CPython-`getstate()`-
  Aenderung). Bei Bedarf Migrations-ADR mit Resume-Routing.
- Alternative PRNG-Implementationen (`MLRandomPort` /
  `AsyncRandomPort`, `ADR 0007 §6`).
