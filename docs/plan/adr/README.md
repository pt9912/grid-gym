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
| 0006 | [ADR-Lifecycle, Superseding und Prozess-Korrekturen](0006-adr-lifecycle-superseding-and-process-corrections.md) | Accepted    | 2026-05-15  | **§3-Aenderungsregeln** geschaerft durch [`ADR 0011`](0011-schaerfung-ohne-abloesung.md): „Schaerfung ohne Supersedes" als zulaessige Folge-ADR-Form. |
| 0007 | [`RandomPort`-Implementierung](0007-random-port.md)             | Accepted    | 2026-05-15  | **§5.2-Snapshot-Schema** abgeloest durch [`ADR 0009`](0009-randomport-snapshot-schema-rng-version.md): `state`-Feld → `rng_version` + `rng_state`. **§5.1-Protocol-Erweiterung** durch [`ADR 0010`](0010-randomport-snapshot-as-mapping.md): zusaetzliche Methode `snapshot_as_mapping()`. Beide reine Erweiterungen, kein Supersedes. |
| 0008 | [Enum-Subklassen als AC-DOMAIN-FROZEN-Form](0008-enum-as-domain-frozen-form.md) | Provisional | 2026-05-17  | Erweitert `ADR 0002 §A-1` AC-DOMAIN-FROZEN; Acceptance synchron zur M1-Welle-1-PR-Mergung                          |
| 0009 | [`RandomPort`-Snapshot-Schema](0009-randomport-snapshot-schema-rng-version.md) | Accepted    | 2026-05-17  | Erweitert `ADR 0007 §5.2`; reine Erweiterung, kein Supersedes                                                       |
| 0010 | [`RandomPort.snapshot_as_mapping`](0010-randomport-snapshot-as-mapping.md) | Accepted    | 2026-05-17  | Erweitert `ADR 0007 §5.1` + `ADR 0009`: Composition-API fuer `SnapshotEnvelope`. Single-Source-of-Truth `_build_payload()`. Reine Erweiterung, kein Supersedes. |
| 0011 | [Schaerfung durch parallele ADR ohne Supersedes](0011-schaerfung-ohne-abloesung.md) | Accepted    | 2026-05-17  | Schaerft `ADR 0006 §3`: dokumentiert die „Schaerfung ohne Supersedes"-Form, die ADR 0008/0009/0010 bereits implizit nutzen. Self-bootstrap (ist selbst dieses Muster). |
| 0012 | [API + Simulation als zwei Prozesse](0012-api-simulation-two-processes.md) | Accepted    | 2026-05-17  | Schliesst `GG-AR-OPEN-002` (spec/architecture.md §19): api + simulation als zwei Prozesse, Postgres als Persistenz-Bus. Welle 6c hat den Pattern bereits implementiert; ADR formalisiert nachtraeglich. |
| 0013 | [`DeviceModel`-Protocol als Core-internes Protocol](0013-device-model-protocol.md) | Accepted    | 2026-05-18  | `DeviceModel`-Vertrag fuer M2-Geraete (`GG-DEV-001..003`). §2.4 `from_snapshot`-Pflicht schaerft durch [`ADR 0014`](0014-battery-snapshot-schema.md) (Battery), [`ADR 0016`](0016-pv-load-device-pattern.md) (PV+Load), [`ADR 0017`](0017-grid-connection-device-pattern.md) (GridConnection), [`ADR 0018`](0018-smart-meter-device-pattern.md) (SmartMeter) — alle reine Erweiterungen je Geraet, kein Supersedes. |
| 0014 | [Battery-Snapshot-Schema + Command-Surface (M2 Welle 2)](0014-battery-snapshot-schema.md) | Accepted    | 2026-05-18  | Vorlage fuer das Geraete-Snapshot-/Command-Pattern. Schaerft `ADR 0013 §2.4` fuer den Battery-spezifischen Snapshot-Vertrag (`Schaerfung ohne Supersedes`-Pattern, ADR 0011). §§3/7 cross-referenziert durch [`ADR 0016`](0016-pv-load-device-pattern.md) (`set_mode` ist Welle-5+-Material). |
| 0016 | [PV + Load Generation/Consumption-Device-Pattern (M2 Welle 3)](0016-pv-load-device-pattern.md) | Accepted    | 2026-05-18  | Gemeinsame ADR fuer PV (`GG-DEV-011`) und Load (`GG-DEV-013`). Spiegelt das ADR-0014-Pattern in einfacherer Form (kein SOC / Ramp / Wirkungsgrad). §2.2 Sign-Konvention bindet [`ADR 0017`](0017-grid-connection-device-pattern.md) §2.2 (gleiche Netzbilanz-Formel) und [`ADR 0018`](0018-smart-meter-device-pattern.md) §2.4 (Aggregation respektiert Quellen-Sign). |
| 0017 | [GridConnection-Anschlusspunkt-Pattern (M2 Welle 4a)](0017-grid-connection-device-pattern.md) | Accepted    | 2026-05-19  | Welle-4a-Geraet `GG-DEV-012`. Stateful Anschlusspunkt mit kumulativem `import_kwh`/`export_kwh`. Sign-Konvention `power_kw > 0 = Import` schliesst die Welle-5-Netzbilanz-Formel aus [`ADR 0016`](0016-pv-load-device-pattern.md) §2.2. Separate ADR statt geteilt mit [`ADR 0018`](0018-smart-meter-device-pattern.md) (verschiedene State-Modelle). §§2.4/2.5 geschaerft durch Welle-4a-Review-Folge (Commit `1ed976a`: IGNORED-Klarstellung + Decimal-Praezisions-Note). Status-Uebergang: `Proposed → Provisional` (Welle 4a-Merge) → `Accepted` (Welle-4-Closure). |
| 0018 | [SmartMeter-Aggregator-Pattern (M2 Welle 4b)](0018-smart-meter-device-pattern.md) | Accepted    | 2026-05-19  | Welle-4b-Geraet `GG-DEV-014`. Stateless Aggregator ueber `aggregate_device_ids: tuple[str, ...]` via neuem `attach_sources(...)`-Lifecycle-Hook (Analogie zu Welle-3-Review-M-6-`attach_random`). Snapshot persistiert **keine** Aggregat-Werte (derived). Schwester-ADR zu [`ADR 0017`](0017-grid-connection-device-pattern.md). §2.2 geschaerft durch Welle-4b-Review-Folge (Commit `1093b2c`: `aggregate_metric_name`-Pflicht auf `"power_kw"` in Welle 4b; Welle 5+ aktiviert Forward-Looking). Status-Uebergang: `Proposed → Accepted` direkt (Welle-4-Closure). |

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
