# Carveout-Index

**Status:** Lebend ab 2026-06-04 (M5-Closure-Folge-Sync).
**Zweck:** Eine **einzige Cross-Meilenstein-Sicht** auf alle
Scope-Entscheidungen, die bewusst auf spaetere Meilensteine /
spaetere Wellen verschoben wurden. Ergaenzt — ersetzt nicht —
die vier bestehenden Carveout-Surfaces des Repos:

| Surface | Granularitaet | Wo |
| ------- | ------------- | -- |
| Per-Welle `§1.3 Anti-Scope`-Block | feinste Aufloesung pro Welle | jede Welle-Slice-Doc unter `done/M{N}-welle-*.md §1.3` |
| Pro-M-Closure `§5 Erbschaft` + `§7/§8 Nicht-vollzogen` | aggregiert pro Meilenstein | [`../done/M3-results.md`](../done/M3-results.md), [`../done/M4-results.md`](../done/M4-results.md), [`../done/M5-results.md`](../done/M5-results.md) |
| `open/`-Trigger-Docs | formal-akzeptierter Trigger-Watch | [`../open/`](../open/) Bestand-Tabelle |
| `roadmap.md §3 M{N+1}`-Vorbelegung | DoD-Checkbox-Skizze | [`roadmap.md`](roadmap.md) §3 M6 |

**Warum dieses Dokument trotzdem?** Bisher mussten Reviewer
fuer eine vollstaendige Carveout-Sicht **drei M-results-Docs**
zusammen mit **17 `open/`-Trigger-Docs** und den Welle-Anti-
Scope-Bloecken querverlinken. Dieses Doc ist die zentrale
Index-Tabelle ueber alle aktiven Carveouts; jede Zeile zeigt
auf die kanonische Source, die im Welle/M-Closure verankert
wurde.

---

## 1. Konvention

**Carveout** = bewusster Verzicht im aktuellen Lieferumfang
mit dokumentiertem Forward-Pointer auf eine spaetere Welle /
einen spaeteren Meilenstein. Drei Sub-Typen:

- **Explicit Anti-Scope** — pro Welle/M `§1.3 Anti-Scope`
  oder `§7/§8 Nicht-vollzogen` aufgezaehlt.
- **Stub-Aufloesung** — Surface ist heute Stub (z. B.
  `GET /snapshot`-`schema_ref`-Pointer); volle Lieferung
  wandert.
- **Pattern-Generalisierung** — Welle-internes Pattern, das
  als Forward-Pointer fuer wiederverwendbare Hardening-
  Idiome dokumentiert ist (kein klassisches Carvout, aber
  unter dem Index-Dach gefuehrt fuer Sichtbarkeit).

**Status-Werte:**

- `Open` — Forward-Pointer aktiv, keine Aufloesungs-Welle
  vorgesehen.
- `In Trigger Watch` — formaler Trigger-Doc in
  [`../open/`](../open/) mit Aktivierungs-Bedingung.
- `Active in M{N}-Welle-X` — Carveout in aktiver Welle in
  Bearbeitung.
- `Resolved {date} ({M-Welle-Hash})` — geschlossen; Eintrag
  wandert in §3 Resolved-Block oder raus.

---

## 2. Aktive Carveouts

### 2.1 M5-Erbschaft fuer M6+ (6 Items)

Quelle: [`../done/M5-results.md §5`](../done/M5-results.md)
„Welle-7-Erbschaft fuer M6+" + §8 „Nicht-vollzogene Items".

| Item | Sub-Typ | Quell-Welle | Status | Aktivierungs-Bedingung | Trigger-Doc |
| ---- | ------- | ----------- | ------ | ---------------------- | ----------- |
| Snapshot-Envelope-v2-Body-Serialisierung (`GET /snapshot`) | Stub-Aufloesung | Welle 1 (Stub) + ADR 0015 v2 | Open | M6-Replay-Surface oder eigener Slice | — (kein Open-Trigger) |
| CSV/JSONL-Export-Endpunkte | Explicit Anti-Scope | Welle 6c §1.3 + `GG-ACCEPT-003` | Open | M6 oder eigener Slice | — |
| Inline-SVG-Geraete-Grafik | Explicit Anti-Scope | Welle 6b §1.3 + Decision 23 | Open | M6 (UI-Polish-Welle) | — |
| Dynamische Fault-Activation ueber `POST /faults` | Explicit Anti-Scope | Welle 6a Decision 19 | Open | M6 (Fault-Pipeline-Erweiterung) | — |
| URL-Versionierung `/api/v1`-Mount-Prefix | Realization-Erbschaft | Welle 6b §10.1 URL-Realization-Note | Open | vor naechster URL-Kollision oder M6-Welle-X | — |
| Welle-3-Pre-init-Defense-Pattern verallgemeinern | Pattern-Generalisierung | Welle 6b Review-Folge F2 (`cd7cfc6`) | Open | M6-Welle-X-Adapter-Hardening-Sweep | — |

### 2.2 M4-Erbschaft (2 Items; ueber M5 weitergereicht)

Quelle: [`../done/M4-results.md §5`](../done/M4-results.md) +
[`../done/M5-results.md §5`](../done/M5-results.md) +
[`../open/`](../open/).

| Item | Sub-Typ | Quelle | Status | Aktivierungs-Bedingung | Trigger-Doc |
| ---- | ------- | ------ | ------ | ---------------------- | ----------- |
| IEC-61850-In-Process-Smoke Reaktivierung | Explicit Anti-Scope (2c-Mock-Fallback) | M4-Welle-5b + M4-Welle-6b-C3 | In Trigger Watch | `pyiec61850-ng` cp314-Wheel (Pfad A) ODER Multi-Python-Test-Stage (Pfad B) | [`009-iec61850-smoke-reactivation.md`](../open/009-iec61850-smoke-reactivation.md) |
| Base-Image-Bump fuer krb5-CVE-Drift (`make fullbuild`-Defer) | Externer Defer | M3-Welle-7-`c61ab0d` pre-existing | In Trigger Watch | `make fullbuild` als CI-Pflicht ODER Compliance-Druck ODER Library-Bump-Folge | [`010-base-image-krb5-cve-bump.md`](../open/010-base-image-krb5-cve-bump.md) |

### 2.3 M3-Erbschaft (RL-Adapter)

Quelle: [`../done/M3-results.md §5`](../done/M3-results.md).

| Item | Sub-Typ | Quelle | Status | Aktivierungs-Bedingung | Trigger-Doc |
| ---- | ------- | ------ | ------ | ---------------------- | ----------- |
| Reinforcement-Learning-Agent-Adapter (`RL-Adapter`) | Forward-Linked Trigger | M3-Welle-7 Decision (C3) | In Trigger Watch | RL-Forschungs-Bedarf oder Stakeholder-Aktivierung | [`030-rl-adapter.md`](../open/030-rl-adapter.md) |

### 2.4 M2-Erbschaft (SOLLTE-Geraete + Netzbilanz, 9 Items)

Quelle: [`../done/M2-devices-results.md §5`](../done/M2-devices-results.md) +
[`../done/M3-results.md §5`](../done/M3-results.md) +
[`../done/M4-results.md §5`](../done/M4-results.md) (Re-Triage).

| Item | Lastenheft-ID | Status | Trigger-Doc |
| ---- | ------------- | ------ | ----------- |
| EV-Charger-Device | `GG-DEV-015` | In Trigger Watch | [`016-sollte-ev-charger-device.md`](../open/016-sollte-ev-charger-device.md) |
| Transformer-Device | `GG-DEV-016` | In Trigger Watch | [`017-sollte-transformer-device.md`](../open/017-sollte-transformer-device.md) |
| Wind-Device | `GG-DEV-017` | In Trigger Watch | [`018-sollte-wind-device.md`](../open/018-sollte-wind-device.md) |
| Diesel-Device | `GG-DEV-018` | In Trigger Watch | [`019-sollte-diesel-device.md`](../open/019-sollte-diesel-device.md) |
| Inselnetz-Bilanzmodell | `GG-GRID-005` | In Trigger Watch | [`020-sollte-island-grid.md`](../open/020-sollte-island-grid.md) |
| Transformatorgrenzen im Netzbilanzmodell | `GG-GRID-006` | In Trigger Watch | [`021-sollte-transformer-limits.md`](../open/021-sollte-transformer-limits.md) |
| Blindleistung im Netzbilanzmodell | `GG-GRID-007` | In Trigger Watch | [`022-sollte-reactive-power.md`](../open/022-sollte-reactive-power.md) |
| Battery-Temperatur-Telemetry | `GG-BESS-006` | In Trigger Watch | [`023-sollte-battery-temperature.md`](../open/023-sollte-battery-temperature.md) |
| Battery-Zellspannung-Telemetry | `GG-BESS-007` | In Trigger Watch | [`024-sollte-battery-cell-voltage.md`](../open/024-sollte-battery-cell-voltage.md) |

Aktivierungs-Bedingung pro Item: „wenn konkreter Bedarf —
eigener Slice".

### 2.5 Tooling- / Build- / Type-System-Trigger (5 Items)

Quelle: [`../open/`](../open/).

| Item | Sub-Typ | Status | Aktivierungs-Bedingung | Trigger-Doc |
| ---- | ------- | ------ | ---------------------- | ----------- |
| Canonical-Encoder-Alternative-ADR (orjson, msgspec) | Forward-Linked | In Trigger Watch | bei messbarem Perf-Druck am Telemetrie-Pfad | [`004-canonical-encoder-alternative-adr.md`](../open/004-canonical-encoder-alternative-adr.md) |
| Pyright-vs-mypy-Re-Eval | Forward-Linked | In Trigger Watch | sobald `ports/*` Generic-Protocols einfuehrt | [`005-pyright-vs-mypy-reeval.md`](../open/005-pyright-vs-mypy-reeval.md) |
| Pyright-als-Pre-Commit-Hook-ADR | Forward-Linked | In Trigger Watch | bei Editor-Parity-Druck | [`007-pyright-precommit-adr.md`](../open/007-pyright-precommit-adr.md) |
| `make sbom` scharfschalten (`GG-CICD-007`) | Forward-Linked | In Trigger Watch | mit erster Artefakt-Veroeffentlichung | [`008-sbom-activation.md`](../open/008-sbom-activation.md) |
| `MLRandomPort` Sub-Seed-Wortbreite (ADR 0007 §5.2/§6) | Forward-Linked | In Trigger Watch | bei `> 10⁶` Sub-Ports / hochskalierter Multi-Agent-Welle | [`011-mlrandomport-subseed-width.md`](../open/011-mlrandomport-subseed-width.md) |

### 2.6 Spike-Optional (1 Item)

| Item | Sub-Typ | Status | Aktivierungs-Bedingung | Trigger-Doc |
| ---- | ------- | ------ | ---------------------- | ----------- |
| BESS-Simulation Reserve-Market-Spike | Forward-Linked (optionaler Spike) | In Trigger Watch | bei Reserve-Market-Agent / BESS-SOC-Management / LER-Demo | [`026-bess-simulation-reserve-market-spike.md`](../open/026-bess-simulation-reserve-market-spike.md) |

### 2.7 M6-Vorbelegung (Lastenheft-Pflicht-IDs)

Quelle: [`roadmap.md §3 M6`](roadmap.md). Diese sind keine
Carveouts im engeren Sinne (M6 ist der Hauptbestimmungs-Ort),
sondern Vorbelegungs-DoD-Items, die mit M6-Welle-0 in einen
formalen M6-Slice-Plan wandern.

| Lastenheft-Familie | Anzahl IDs | Lieferziel |
| ------------------ | ---------- | ---------- |
| `GG-RT-001..005` | 5 | Performance-Schranken (10k-Points/s-Benchmark) |
| `GG-SAFE-001..006` | 6 | Sicherheits-Audit |
| `GG-CICD-001..00X` | ≥7 | CI/CD-Vollausbau (4 Slice-025-ausgelagerte Items + Release-Workflow + SBOM + Test-Matrix) |
| `GG-DEPLOY-001..00X` | ≥X | Deploy-Hardening (Container-Smoke + Image-Audit + krb5-Bump-Erbschaft) |
| `GG-SBOM-001..00X` | ≥1 | SBOM-Generierung (Trigger 008) |

---

## 3. Resolved Carveouts (Audit-Trail-Auswahl)

Geschlossen mit M-Closure oder Welle-Lieferung; Eintraege
bleiben hier eine kurze Weile fuer Audit-Trail (volle History
in `done/`).

| Item | Geloest mit | Resolution-Hash |
| ---- | ----------- | --------------- |
| `--strict-bytes`-Aktivierung (`[tool.mypy]`) | M4-Welle-6a-C3 | Trigger-Doc nach [`../done/006-mypy-strict-bytes.md`](../done/006-mypy-strict-bytes.md) |
| `GG-DEMO-008` Abnahmedoku (Welle-5-Anti-Scope-Erbschaft) | M5-Welle-6c-C2 | `0e604e4` — NEU [`../../../user/gg-demo-008-abnahme.md`](../../../user/gg-demo-008-abnahme.md) |
| `GG-DEMO-006` YAML-side Fault-Injection (Welle-5-Anti-Scope-Erbschaft) | M5-Welle-6a-C2 | `db3a0c2` |
| `GG-UI-006..008` Geraete-Grafik + Fault-Form + Sim-Zustand | M5-Welle-6a/6b-C2 | `db3a0c2` + `9fcb887` |

(Liste nicht erschoepfend; volle Resolution-Historie pro M
in `done/M{N}-results.md §5` + §8.)

---

## 4. Lifecycle + Pflege-Konvention

**Wann ergaenzt der Index?**

- Bei jeder Welle-Closure (`C3-Sync`): pro neu angelegtem
  Welle-Anti-Scope-Item pruefen, ob es als Trigger-Watch in
  `open/` formalisiert werden sollte → falls ja, Trigger-Doc
  anlegen UND Zeile hier ergaenzen.
- Bei jeder M-Closure (`Welle-7-C2 M-results.md`): die §5/§8-
  Eintraege gegen diesen Index abgleichen; redundante oder
  bereits abgedeckte Items mit Cross-Link versehen, neue als
  eigene Zeile aufnehmen.

**Wann reduziert der Index?**

- Item wird durch eine Welle-Lieferung aufgeloest → Zeile in
  §3 Resolved-Block fuer Audit-Trail; nach M-Closure (z. B.
  M+1-Welle-7) gehoert die §3-Zeile in das jeweilige
  `done/M{N}-results.md §5 Resolution` und kann hier raus.

**Was lebt nicht hier?**

- Pro-Welle-Anti-Scope-Bloecke `§1.3` (zu granular; siehe
  Source-Slice-Doc).
- Welle-interne DoD-Checkboxen (`§9` der Slice-Doc).
- Lastenheft-IDs ohne Forward-Pointer (siehe `roadmap.md §3
  M{N}` DoD-Checkliste).

**Wann sollte das Dokument selbst gesplittet werden?**

- Wenn Tabelle ≥ 50 Eintraege wird (Cross-M-Sicht wird
  unuebersichtlich).
- Wenn Resolved-Block ≥ 30 Zeilen wird (Audit-Trail-
  Verschieberung nach `done/M-results.md` faellig).

---

## 5. References

- [`../done/M5-results.md §5 + §8`](../done/M5-results.md)
  — M5-Welle-7-Erbschaft + Nicht-vollzogen.
- [`../done/M4-results.md §5 + §7`](../done/M4-results.md)
  — M4-Welle-7-Erbschaft + Nicht-vollzogen.
- [`../done/M3-results.md §5 + §7`](../done/M3-results.md)
  — M3-Welle-7-Erbschaft + Nicht-vollzogen.
- [`../done/M2-devices-results.md`](../done/M2-devices-results.md)
  — M2-SOLLTE-Geraete-Quelle.
- [`../open/README.md`](../open/README.md) — Bestand-Tabelle
  der formal-akzeptierten Trigger-Watch-Eintraege.
- [`roadmap.md §3 M6`](roadmap.md) — M6-Vorbelegung mit DoD-
  Checkbox-Skizze.
- [`../README.md`](../README.md) — Planning-Verzeichnis-
  Lifecycle-Konvention.
