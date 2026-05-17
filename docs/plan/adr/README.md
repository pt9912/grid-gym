# ADR-Index — grid-gym

Lebende Uebersicht ueber alle ADRs, ihren Status und die
Vorrang-/Schaerfungs-Beziehungen zwischen ihnen. Diese Datei ist
**kein** ADR-Entscheidungstext — sie ist eine Service-Notiz fuer
Reviewer, damit Drift zwischen Accepted-Texten (die per
`ADR 0006 §3` immutable sind) und nachgelagerten Folge-ADRs
sichtbar bleibt.

Reihenfolge: aufsteigend nach ADR-Nummer. Eine ADR mit Schaerfung
durch eine Folge-ADR traegt eine Spalte „Schaerfungen" mit
Verweisen — die Folge-ADR ist verbindlich, der Original-Text
historisch.

---

## Aktive ADRs

| ADR  | Titel                                                           | Status      | Datum       | Schaerfungen / Folge-ADRs                                                                                          |
| ---- | --------------------------------------------------------------- | ----------- | ----------- | ------------------------------------------------------------------------------------------------------------------ |
| 0001 | [Dokumentations- und Planungsstruktur](0001-documentation-and-planning-structure.md) | Accepted    | 2026-05-13  | —                                                                                                                  |
| 0002 | [Sprach- und Build-Stack](0002-language-and-build-stack.md)     | Accepted    | 2026-05-14  | [`ADR 0008`](0008-enum-as-domain-frozen-form.md) erweitert §A-1 AC-DOMAIN-FROZEN um Enum-Subklasse als dritte Form |
| 0003 | [ADR-Lifecycle](0003-adr-lifecycle.md)                          | Superseded  | 2026-05-13  | Abgeloest durch [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)                            |
| 0004 | [Kennungs-basierte Querverweise](0004-identifier-based-cross-references.md) | Accepted    | 2026-05-13  | —                                                                                                                  |
| 0005 | [Type-Check-Gate (`mypy --strict`)](0005-type-check-gate.md)    | Accepted    | 2026-05-15  | —                                                                                                                  |
| 0006 | [ADR-Lifecycle, Superseding und Prozess-Korrekturen](0006-adr-lifecycle-superseding-and-process-corrections.md) | Accepted    | 2026-05-15  | —                                                                                                                  |
| 0007 | [`RandomPort`-Implementierung](0007-random-port.md)             | Accepted    | 2026-05-15  | **§5.2-Snapshot-Schema** abgeloest durch [`ADR 0009`](0009-randomport-snapshot-schema-rng-version.md): `state`-Feld → `rng_version` + `rng_state`. **§5.1-Protocol-Erweiterung** durch [`ADR 0010`](0010-randomport-snapshot-as-mapping.md): zusaetzliche Methode `snapshot_as_mapping()`. Beide reine Erweiterungen, kein Supersedes. |
| 0008 | [Enum-Subklassen als AC-DOMAIN-FROZEN-Form](0008-enum-as-domain-frozen-form.md) | Provisional | 2026-05-17  | Erweitert `ADR 0002 §A-1` AC-DOMAIN-FROZEN; Acceptance synchron zur M1-Welle-1-PR-Mergung                          |
| 0009 | [`RandomPort`-Snapshot-Schema](0009-randomport-snapshot-schema-rng-version.md) | Accepted    | 2026-05-17  | Erweitert `ADR 0007 §5.2`; reine Erweiterung, kein Supersedes                                                       |
| 0010 | [`RandomPort.snapshot_as_mapping`](0010-randomport-snapshot-as-mapping.md) | Accepted    | 2026-05-17  | Erweitert `ADR 0007 §5.1` + `ADR 0009`: Composition-API fuer `SnapshotEnvelope`. Single-Source-of-Truth `_build_payload()`. Reine Erweiterung, kein Supersedes. |

---

## Lese-Reihenfolge bei Drift

Wenn Code, Tests oder Slice-Plaene auf einen Vertrag referenzieren,
der in einer aelteren `Accepted`-ADR steht, **immer pruefen, ob
eine Folge-ADR in der „Schaerfungen"-Spalte oben die Stelle
schaerft.** Im Zweifel:

1. Folge-ADR lesen — sie traegt die maßgebliche Fassung.
2. Original-ADR-Stelle bleibt historisch (kein Edit per
   `ADR 0006 §3`).
3. Adapter-/Modul-Code-Docstrings zitieren beide ADRs ueber den
   `ADR NNNN`-Tag (siehe z. B.
   `src/grid_gym/adapters/driven/random_mt/mersenne_twister.py`).

---

## Konvention

- Neuer ADR-Eintrag in dieser Tabelle ist Pflicht bei jeder neuen
  ADR. Reihenfolge: aufsteigend nach Nummer.
- Wenn eine ADR eine andere abloest oder schaerft, wird die
  „Schaerfungen"-Spalte der **alten** ADR aktualisiert. Die alte
  ADR selbst bleibt textlich unveraendert (per ADR 0006 §3).
- Statuswechsel (z. B. `Provisional → Accepted`) werden in der
  ADR-Datei selbst dokumentiert (Header-Pflichtfelder per
  `ADR 0006 §4`); diese Tabelle reflektiert sie.
