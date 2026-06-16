# Welle 3 — M8 Netz (`GG-GRID-005..007`)

**Status:** In Arbeit (M8-Welle-3, eroeffnet 2026-06-15) — **3a (Inselnetz)
Done 2026-06-16** ([`ADR 0060`](../../adr/0060-island-grid-bilanz-pattern.md)
`Accepted`, [`M8-welle-3a.md`](M8-welle-3a.md), Trigger 020 aufgeloest);
**3b (Trafo-Grenzen) + 3c (Blindleistung) offen**. Die Netz-Welle von M8:
drei Schaerfungen des bestehenden Netzbilanzmodells
(`GridModelBilanz`, [`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md))
aus Lastenheft §11.5, die M2 als SOLLTE markierte. Reine Core-Domain-/
Bilanz-Erweiterung — **kein neues Geraet, kein neuer Port/Adapter-Typ**.
Dieser Plan ist die Welle-3-C0-Substanz. Der **Wellen-Status bleibt offen**,
bis auch 3b/3c geliefert sind; die `[x]` in §6 quittieren ausschliesslich
das **C0-Eroeffnungs-Gate** (Plan + Entscheidungen + `docs-check`), **nicht**
den Wellen-Abschluss. Doc-Verschiebung der Sub-Wellen nach `done/` erfolgt
als Gruppe mit der Welle-3-Gesamt-Closure (wie Welle 2).

**Container:** Meilenstein-Scope in [`roadmap.md`](roadmap.md) §4 M8;
Welle-Triage in [`M8-welle-0.md`](../done/M8-welle-0.md) §1.1 (Welle 3 =
`T-020..022`). Voraussetzung (Welle 2, SOLLTE-Geraete) abgeschlossen
([`M8-welle-2.md`](../done/M8-welle-2.md)) — die neuen Geraete
(Wind/Diesel als `generation`, EV als `storage`) speisen bereits ueber
`_BILANZ_SOURCE_BUCKETS` in die Bilanz ein. Aufbau auf
[`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md)
(Schaerfung-Pattern, kein Supersede — wie
[`ADR 0011`](../../adr/0011-schaerfung-ohne-abloesung.md) etabliert,
[`ADR 0020`](../../adr/0020-load-profile-and-event-pattern.md) zu 0019).

---

## 1. Zweck + Architektur-Familie

Alle drei Sub-Wellen erweitern dasselbe `GridModelBilanz`
(`src/grid_gym/hexagon/core/grid_model/bilanz.py`) und seine
`GridModelConfig` (`src/grid_gym/hexagon/core/grid_model/config.py`).
Heutiger Stand ([`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md)):
**Single-Bus, nur Wirkleistung** — `imbalance_kw = generation - load -
storage + grid_connection`, Frequenz/Spannung proportional, mit
`grid_connection`-Auto-Slack im TickLoop
(`src/grid_gym/hexagon/core/simulation/tick_loop.py`). Welle 3 ist
durchgehend **Bilanz-Schaerfung im Core**, kein Geraete-Submodul.

| Sub-Welle | ID | Trigger | Wesen | Charakteristik |
|---|---|---|---|---|
| 3a Inselnetz | `GG-GRID-005` | [`020`](../open/020-sollte-island-grid.md) | Slack-Wechsel | Kein externer Slack; internes Grid-Forming-Geraet haelt Frequenz; `is_islanded`/`forming_device_id` in der Config |
| 3b Trafo-Grenzen | `GG-GRID-006` | [`021`](../open/021-sollte-transformer-limits.md) | Bilanz-Constraint | `max_apparent_power_kva` + Ueberlastkennlinie + simples Thermomodell; `GridConstraintViolationEvent` bei Verletzung |
| 3c Blindleistung | `GG-GRID-007` | [`022`](../open/022-sollte-reactive-power.md) | Cross-cutting + Schema | `reactive_power_kvar` + Q(U)-Kennlinie pro Q-Geraet; `imbalance_kvar` parallel zu `imbalance_kw`; additive **Snapshot-Erweiterung** (multi-schema) |

**Architektur-Erbschaft:** kein neuer Driving-/Driven-Port — die
Schaerfungen leben in `grid_model` + `tick_loop`. Pro Sub-Welle eine
ADR-Folge als **Erweiterung** von
[`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md) (Schaerfung-
Pattern, kein Supersede); 3c zusaetzlich Q-Emission als Folge zu
[`ADR 0016`](../../adr/0016-pv-load-device-pattern.md) (PV-Wechselrichter)
und [`ADR 0017`](../../adr/0017-grid-connection-device-pattern.md).
`grid_model` liegt bereits in `CRITICAL_COV_TARGETS` → **kein neuer
Coverage-Target-Eintrag** (anders als die Geraete-Wellen 2a-2d).

## 2. Erfolgskriterien (DoD je Sub-Welle)

- ADR-Folge (Status `Accepted`) als Schaerfung von
  [`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md) (kein
  Supersede), mit bilanz-/geraete-spezifischen Akzeptanzkriterien.
- `GridModelConfig`-Erweiterung: neue Felder **additiv** + backward-
  compat-Default (Bestands-Szenarien unveraendert ladbar).
- Bilanz-/TickLoop-Logik erweitert; **`is_islanded=False` /
  Q-frei = heutiges Verhalten bit-genau** (Default-Pfad unberuehrt).
- Tests: Determinismus-Property (`hypothesis`), Boundary-/Negative-Pins;
  bei Schema-Aenderung Snapshot-Roundtrip **inkl. v2-backward-compat-
  Lesepfad**.
- `make gates` gruen (10 A-1-Gates), `coverage-gate-critical` ≥ 90 % auf
  `grid_model` (ohne neuen Target); bei Bilanz-/Config-Aenderung
  `make test-determinism`.
- `EXPECTED_DEMO_*`-Hash-Pins unberuehrt: neue Bilanz-Features sind
  **opt-in im Szenario**, der MVP-Demo bleibt unveraendert.

## 3. Tranchierung (Sub-Slicing)

Drei unabhaengige Bilanz-Schaerfungen ueberschreiten die Sub-Slicing-
Schwelle ([`M8-welle-0.md`](../done/M8-welle-0.md) §2.4: > 2 unabhaengige
Sub-Bereiche) → Split in drei Sub-Wellen, Reihenfolge **3a → 3b → 3c**
(lokale Schaerfungen zuerst, das cross-cutting Q mit Schema-Migration
zuletzt — per Stakeholder-Entscheid 2026-06-15). Jede Sub-Welle aktiviert
ihren `open/`-Trigger und loest ihn bei Closure auf.

- **Welle 3-C0 — Eroeffnung** (dieser Plan): Bestaetigung gegen
  [`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md), Reihenfolge,
  Schema-Strategie. Sensor: `make docs-check`.
- **Welle 3a — Inselnetz — Done 2026-06-16**
  ([`M8-welle-3a.md`](M8-welle-3a.md),
  `GG-GRID-005`, [`020`](../open/020-sollte-island-grid.md),
  [`ADR 0060`](../../adr/0060-island-grid-bilanz-pattern.md) `Accepted`):
  `is_islanded: bool` + `forming_device_id: str | None` in
  `GridModelConfig`; TickLoop-Auto-Close waehlt im Inselnetz **das
  Grid-Forming-Geraet** statt `grid_connection` als Slack (Vorzeichen pro
  Bilanz-Bucket); Frequenz-/Spannungstoleranzen ohne externen Slack;
  deterministische Forming-Election (explizite ID, kein impliziter
  Tie-Break); Existenz-Check im TickLoop-Wiring. Forming-Ueberlast via
  Geraete-Clamp (Constraint-Event deferred → 3b). Black-Start minimal (Init
  ohne Netzanschluss); Multi-Insel-Synchronisation out-of-scope (§5).
- **Welle 3b — Transformatorgrenzen** ([`M8-welle-3b.md`](M8-welle-3b.md),
  `GG-GRID-006`, [`021`](../open/021-sollte-transformer-limits.md)):
  `max_apparent_power_kva` + Ueberlast-Zeit-Strom-Kennlinie + simples
  Thermomodell (Top-Oil/Hot-Spot) auf **Bilanz-Ebene**; Grenz-Check pro
  Tick → `GridConstraintViolationEvent` (pro-Tick-Laufzeit-Event, Pattern
  wie `LoadEvent` / der Event-Domaintyp — **nicht** eine Config-
  Construction-Exception). NEU ADR.
  **Klar abgegrenzt** vom Transformer-**Geraet** (Welle 2b, das nur
  Per-Device-Saettigung clamped) — 3b ist die Netz-Grenze im Bilanzmodell.
- **Welle 3c — Blindleistung** ([`M8-welle-3c.md`](M8-welle-3c.md),
  `GG-GRID-007`, [`022`](../open/022-sollte-reactive-power.md)):
  `reactive_power_kvar`-Telemetry in den Q-emittierenden Geraeten
  (PV-Wechselrichter, GridConnection) mit Q(U)-Kennlinie; `imbalance_kvar`
  parallel zu `imbalance_kw` in `GridModelBilanz`; additive
  **Snapshot-Erweiterung** mit backward-compat-Lesepfad (analog dem
  GridModelSnapshot-v1→v2-Bump,
  [`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md)/[`ADR 0020`](../../adr/0020-load-profile-and-event-pattern.md)).
  Die konkrete Schema-Liste (mehrere beruehrte Snapshots) ist
  3c-Design-Item ([`M8-welle-3c.md`](M8-welle-3c.md) §3). NEU ADR(s) als
  Folge zu 0019 + 0016/0017. **Bewusst zuletzt:** groesste Flaeche (alle
  Q-Geraete) + Schema-Migration mit Replay-/Export-Beruehrung.

**Schwellen-Hinweis:** sollte eine Sub-Welle selbst > 300 Zeilen / > 5
Commits werden (3c ist Kandidat wegen Schema + Multi-Geraete-Q), wird sie
nach demselben Schema weiter getrancht (3c-a Q-Bilanz/Schema, 3c-b
Geraete-Q-Emission).

## 4. Risiken

- **Snapshot-Migration (3c):** der Schema-Bump beruehrt **mehrere**
  Snapshots (GridModelSnapshot v2→v3 + additive Q-Felder in PV-/
  GridConnection-Device-Snapshots) und damit Replay-/Export-Konsumenten +
  die `EXPECTED_DEMO_*`-Hash-Pins; backward-compat-Lesepfade zwingend
  (analog dem v1→v2-Bump,
  [`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md)/[`ADR 0020`](../../adr/0020-load-profile-and-event-pattern.md)).
  Der `SnapshotEnvelope` ([`ADR 0015`](../../adr/0015-snapshot-envelope-v2.md))
  bleibt unveraendert. Beruehrt ggf. `D-1` ([`carveouts.md`](carveouts.md));
  Q-Felder additiv + opt-in.
- **Determinismus:** Q(U)-Kennlinien, Zeit-Strom-Ueberlastkennlinie und
  Thermomodell brauchen `Decimal`-Rundungs-Disziplin (`AC-NO-RAND`,
  kanonische Serialisierung) — kein Float-Drift im Snapshot.
- **Bilanz-Default-Stabilitaet (3a):** der Inselnetz-Fork der Auto-Close-
  Logik darf den Netzanschluss-Pfad nicht veraendern — `is_islanded=False`
  muss bit-genau das heutige Single-Bus-Verhalten liefern (Regressions-Pin).
- **Forming-Election (3a):** die Geraete-Auswahl muss deterministisch sein
  (`forming_device_id` explizit; kein impliziter „erstes Geraet"-Drift).
- **Coverage:** `grid_model` ist bereits coverage-critical, die Q-Emission
  in den Geraete-Modulen (3c) ebenfalls — kein neuer
  `CRITICAL_COV_TARGETS`-Eintrag, aber neue Branches duerfen die
  ≥ 90 %-Schwelle nicht druecken.

## 5. Nicht-Ziele

- Schwarzstart-**Synchronisation** zwischen mehreren Inselnetzen — eigener
  Trigger ([`020`](../open/020-sollte-island-grid.md) Out-of-scope).
- Lastabwurfschemata / Load-Shedding — Multi-Agent-Kontext, separater
  Trigger.
- Schutzgeraete-Logik (Distanz-/Differentialschutz) — M4-Material
  (Protokolladapter zu Schutzrelais), nicht diese Welle.
- Reparatur-Zeiten / Asset-Lifecycle — Domain ist elektrisches Verhalten.
- Detail-Modellierung Synchron-/Asynchronmaschinen (Schenkelpol,
  Polradwinkel) — Power-Systems-Software-Domain.
- Volle Lastflussrechnung (Newton-Raphson) — grid-gym bleibt bei
  vereinfachter Bilanz-Aggregation.

## 6. DoD (Welle 3-C0)

- [x] `M8-welle-3.md` angelegt (dieser Plan).
- [x] Scope fixiert: alle drei (`T-020..022`/`GG-GRID-005..007`) in
      Welle 3, per Stakeholder-Mandat 2026-06-15.
- [x] Reihenfolge fixiert: **3a Inselnetz → 3b Trafo-Grenzen → 3c
      Blindleistung** (lokale Schaerfungen vor cross-cutting Q).
- [x] Schema-Strategie grob fixiert: 3a/3b config-additiv ohne
      Schema-Bump; 3c additiv + backward-compat. **Die konkrete
      Schema-Liste ist 3c-Design-Item** (≥ 3 beruehrte Schemata:
      GridModelSnapshot v2→v3, PV-/GridConnection-Device-Snapshots
      additiv, `SnapshotEnvelope` unveraendert) — siehe
      [`M8-welle-3c.md`](M8-welle-3c.md) §3.
- [x] `make docs-check` gruen.
