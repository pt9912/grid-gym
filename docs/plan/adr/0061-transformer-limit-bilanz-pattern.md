# ADR 0061 — Transformatorgrenzen im Netzbilanzmodell (M8 Welle 3b)

**Status:** Accepted — Validierung mit M8-Welle-3b-Lieferung
(lint/format/typecheck/arch-check/test-unit/`coverage-gate-critical`
≥ 90 % auf `grid_model`/`docs-check`/`accept-pin-check` gruen;
Boundary-/Zeit-Akkumulations-Pins + Determinismus-Property +
Inaktiv-Regressions-Pin). Schaerfung von
[`ADR 0019`](0019-grid-model-bilanz-pattern.md) ohne Supersedes
(Erweiterungs-Pattern [`ADR 0011`](0011-schaerfung-ohne-abloesung.md);
gleiche Familie wie [`ADR 0060`](0060-island-grid-bilanz-pattern.md)).
**Datum:** 2026-06-16
**Bezug:**
[`ADR 0019`](0019-grid-model-bilanz-pattern.md) §2.2/§2.3/§2.5/§2.6
(Bilanz-Kern, Safety-Clamps, Snapshot, Lifecycle — diese ADR ergaenzt
einen **additiven Constraint-Layer**, der den Frequenz-/Spannungs-Kern
nicht beruehrt),
[`ADR 0056`](0056-transformer-device-pattern.md) (Transformer-**Geraet**
aus Welle 2b — **klar abgegrenzt**: das Geraet clamped seine eigene
Per-Device-Saettigung, 3b ist die **Netz-Grenze im Bilanzmodell**),
[`ADR 0020`](0020-load-profile-and-event-pattern.md) (`LoadEvent`-
Domaintyp-Pattern — der `GridConstraintViolationEvent` ist ein analoges
frozen Domain-Event),
[`ADR 0060`](0060-island-grid-bilanz-pattern.md) §2.4 (opt-in Snapshot-/
Scenario-Hash-Serialisierung — 3b uebernimmt dasselbe Muster fuer den
Transformer-Block + Thermo-State),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Erweiterungs-ADR-
Pattern). Slice-Plan
[`M8-welle-3b.md`](../planning/done/M8-welle-3b.md); Container
[`M8-welle-3.md`](../planning/done/M8-welle-3.md). Trigger
[`021`](../planning/open/021-sollte-transformer-limits.md) (`GG-GRID-006`,
Lastenheft §11.5).

---

## 1. Kontext

[`ADR 0019`](0019-grid-model-bilanz-pattern.md) kennt im Netzbilanzmodell
nur Frequenz-/Spannungs-Clamps — **keine Wandlungs-/Belastungsgrenze**.
Lastenheft `GG-GRID-006` (Trigger
[`021`](../planning/open/021-sollte-transformer-limits.md)) verlangt
**Transformatorgrenzen auf Bilanz-Ebene**: eine Scheinleistungs-Grenze
mit Ueberlast-Zeit-Strom-Verhalten und einem vereinfachten Thermomodell
(Top-Oil/Hot-Spot).

**Abgrenzung zum Transformer-Geraet (Welle 2b,
[`ADR 0056`](0056-transformer-device-pattern.md)):** das *Geraet* ist ein
`DeviceModel` mit Per-Device-Saettigungs-Clamp + `winding_fault`. Welle 3b
ist die *Netz-Grenze im Bilanzmodell* — sie misst die Scheinleistung am
Netzanschluss-/Modell-Trafo und emittiert bei thermischer Ueberlast ein
**pro-Tick-`GridConstraintViolationEvent`**. Beide koennen koexistieren,
ueberschneiden sich aber nicht: das Geraet begrenzt seinen eigenen
Durchsatz, 3b bewertet die aggregierte Netzlast.

Welle 3b ist — wie 3a — **reine Bilanz-Schaerfung im Core**, kein neues
Geraet, kein neuer Port/Adapter-Typ. Der Constraint-Layer ist **opt-in**:
ohne Transformer-Block (Default) ist das Verhalten bit-genau wie unter
[`ADR 0019`](0019-grid-model-bilanz-pattern.md).

---

## 2. Entscheidung

### 2.1 Config — `TransformerLimitConfig` (nested, opt-in)

`GridModelConfig` (`hexagon/core/grid_model/config.py`) bekommt **ein
additives, optionales Feld**:

```
transformer_limit: TransformerLimitConfig | None = None
```

`None` (Default) = kein Constraint-Layer = bit-genau heutiges Verhalten.
`TransformerLimitConfig` ist eine eigene Frozen-Dataclass (`slots=True`)
mit `__post_init__`-Validierung (Pattern-Spiegel zu
[`ADR 0019`](0019-grid-model-bilanz-pattern.md) §2.4a; Verstoss →
`GridModelConfigInvalidValueError`):

| Feld | Einheit | Invariante |
|---|---|---|
| `max_apparent_power_kva` | kVA | `> 0` (Nennscheinleistung S_n) |
| `ambient_temp_c` | °C | Decimal (Umgebungstemperatur θ_a) |
| `top_oil_rise_rated_c` | K | `> 0` (Top-Oil-Anstieg bei Nennlast) |
| `hot_spot_rise_rated_c` | K | `> 0` (Hot-Spot-Gradient bei Nennlast) |
| `top_oil_time_constant_s` | s | `> 0` (Oel-Zeitkonstante τ) |
| `hot_spot_limit_c` | °C | `> ambient_temp_c` (Ausloese-Schwelle) |

Alle Felder `Decimal` (`GG-DATA-005` no-float-Pruefung). `hot_spot_limit_c >
ambient_temp_c` schliesst aus, dass das Modell bei Nulllast ausloest.

Eine geometrische Stabilitaets-Bedingung (`τ ≥ tick_ms/1000`) wird **nicht**
in der Config geprueft — `tick_ms` ist erst zur Laufzeit bekannt; ein zu
kleines τ bleibt deterministisch (Euler-Ueberschwingen), wird aber in §4
als Konfigurations-Hinweis dokumentiert.

### 2.2 Thermomodell als Zeit-Strom-Mechanismus

Der Kern: die **thermische Traegheit** (τ) *ist* die Zeit-Strom-Kennlinie.
Kurze Ueberlast erwaermt das Oel nur langsam und loest nicht aus; dauerhafte
Ueberlast treibt Hot-Spot ueber die Grenze. Ein vereinfachtes Single-Zonen-
Modell (kein IEC-Loading-Guide-Detail, §7).

Pro Tick (Decimal-Localcontext `prec=28`, `ROUND_HALF_EVEN`; `dt_s =
tick_ms / 1000`):

```
S          = |grid_connection_kw|              # Scheinleistung am Modell-Trafo
load_pu    = S / max_apparent_power_kva
theta_oil_ss = ambient_temp_c + top_oil_rise_rated_c * load_pu^2
theta_oil   += (theta_oil_ss - theta_oil) * (dt_s / top_oil_time_constant_s)
theta_hs    = theta_oil + hot_spot_rise_rated_c * load_pu^2
```

`theta_oil` (Top-Oil-Temperatur) ist **akkumulierter Bilanz-State**, im
`__init__` auf `ambient_temp_c` initialisiert (nur wenn `transformer_limit`
gesetzt; sonst `None`). Er wird je Tick auf eine feste Dezimalstelle
quantisiert (Snapshot-Lesbarkeit + gebundene Stellenzahl;
Quantisierung deterministisch im Context).

**Ausloese-Bedingung:** `theta_hs > hot_spot_limit_c` →
`GridConstraintViolationEvent` (pro-Tick, solange ueberschritten).

**Scheinleistungs-Basis (C1-Entscheidung):** `S ≈ |grid_connection_kw|` —
die Import/Export-Wirkleistung am Netzanschluss (der Modell-Trafo traegt
den Netzaustausch). **Bis 3c gilt `S ≈ |P|`** (nur Wirkleistung);
[`M8-welle-3c.md`](../planning/done/M8-welle-3c.md) erweitert die
Basis auf `S = sqrt(P² + Q²)` und **re-pinnt die Boundary-Tests dieser
Grenze** (Verhaltenswechsel an der Grenze, §4). Im Inselnetz
([`ADR 0060`](0060-island-grid-bilanz-pattern.md)) ist `grid_connection_kw`
typisch `0` → `load_pu ≈ 0` → keine Ausloesung; der Constraint-Layer ist
netzanschluss-bezogen.

### 2.3 `GridConstraintViolationEvent` (Domain-Event, pro-Tick)

Ein **frozen Domain-Dataclass** in
`hexagon/core/domain/event.py` (neben `Event`; AC-DOMAIN-FROZEN-konform).
**Kein** Config-Construction-Error (die Config-Validierung §2.1 ist davon
getrennt) und **kein** Scheduler-`Event` (nicht eingeplant, sondern
pro-Tick aus der Bilanz emittiert). Felder:

- `constraint: str` — Kennung (`"transformer_hot_spot"`).
- `simulation_time: int` — Sim-Zeit des ausloesenden Ticks.
- `apparent_power_kva: Decimal` / `limit_kva: Decimal` — Last vs. Nennwert.
- `top_oil_temp_c: Decimal` / `hot_spot_temp_c: Decimal` /
  `hot_spot_limit_c: Decimal` — Thermo-Evidenz.

Lage in `domain/`, weil `TickResult` (Domain) das Event traegt; die Bilanz
(`grid_model` → `domain`, natuerliche Innen-Richtung) importiert es. Das
Event ist **transientes Tick-Output**, **nicht** Snapshot-State (re-derived
je Tick; daher aus `GridModelBilanz.__eq__`/`__hash__` ausgenommen).

### 2.4 Emission-Pfad (Bilanz → TickResult)

- `GridModelBilanz.update(..., tick_ms, simulation_time)` bekommt zwei
  zusaetzliche, **optionale** Parameter (Default `None`). Ohne
  `transformer_limit` werden sie ignoriert (Bestands-Aufrufer + Inaktiv-
  Pfad byte-identisch). Mit aktivem Layer sind sie Pflicht; fehlen sie →
  `GridModelConfigError`-Subtyp (Wiring-Fehler).
- Nach dem Thermo-Step legt die Bilanz die Verletzungen dieses Ticks in
  `last_constraint_violations: tuple[GridConstraintViolationEvent, ...]`
  ab (leer, wenn keine).
- `TickResult` bekommt ein additives Feld
  `emitted_grid_events: tuple[GridConstraintViolationEvent, ...] = ()`.
  Der TickLoop liest nach `grid_model.update(...)` die
  `last_constraint_violations` und reicht sie in den `TickResult`.

### 2.5 Snapshot — opt-in, kein Versions-Bump (Spiegel 3a)

Schema bleibt **v2**. Wie [`ADR 0060`](0060-island-grid-bilanz-pattern.md)
§2.4:

- **Config-Block opt-in:** `transformer_limit` wird im `config`-Sub-Mapping
  nur emittiert, wenn gesetzt. Default-Pfad → byte-identisch
  (`EXPECTED_DEMO_*` + Scenario-Hash unberuehrt).
- **Thermo-State opt-in:** ein additiver Top-Level-Key `top_oil_temp_c`
  wird nur bei aktivem Layer geschrieben; `from_dict` liest ihn optional
  (Default `None`). Alt-Snapshots ohne Key lesen als „kein Layer".
- Der Scenario-Hash-Opt-in (`_scenario_hash_payload`,
  [`ADR 0060`](0060-island-grid-bilanz-pattern.md) §2.4) entfernt im
  Default auch den `transformer_limit`-Block.

### 2.6 Determinismus + Default-Stabilitaet

- **Inaktiv bit-genau:** der Constraint-Layer aktiviert sich nur bei
  `transformer_limit is not None`; der Frequenz-/Spannungs-Kern
  ([`ADR 0019`](0019-grid-model-bilanz-pattern.md) §2.3) bleibt textlich
  unveraendert (Regressions-Pin Pflicht).
- **Thermo-Determinismus:** Euler-Integration + Quantisierung laufen im
  bestehenden `prec=28`/`ROUND_HALF_EVEN`-Context; gleiche Eingangssequenz
  → byte-identische `theta_oil`-/Event-Spur ueber ≥ 100 Ticks (Hypothesis-
  Property).

---

## 3. Begruendung

**Thermomodell statt separater Hard-Limit-Schwelle:** Eine reine
„S > S_n → Event"-Schwelle wuerde jede kurze Lastspitze (PV-Mittag,
Anlaufstrom) sofort als Verletzung melden — physikalisch falsch und fuer
einen Ueberlast-Schutz unbrauchbar. Die thermische Traegheit τ modelliert
die Zeit-Strom-Kennlinie **physikalisch**: das Integral der Ueberlast zaehlt,
nicht der Momentanwert. Damit ist `max_apparent_power_kva` die
Bemessungsgroesse (Basis fuer `load_pu`), nicht ein Trip-Schwellwert — und
„kurze Ueberlast erlaubt, dauerhafte nicht" faellt ohne separaten
Zeit-Akkumulator heraus.

**`load_pu^2`-Naeherung:** Verluste (und damit Erwaermung) skalieren mit dem
Quadrat des Stroms. Das IEC-Loading-Guide nutzt Exponenten wie `2y`/`1.6`
fuer Oel/Wicklung; 3b vereinfacht beide auf `²` (ehrlich gekennzeichnet,
§7). Ausreichend fuer ein Ersatzmodell, deterministisch, ohne
Wurzel-/Potenz-Sondierung.

**Event in `domain/`, nicht `grid_model/`:** `TickResult` (Domain) traegt
das Event; laege es in `grid_model`, muesste die Domain auf einen
hoeheren Core-Layer importieren (Schichtungs-Smell). In `domain/` ist die
Richtung sauber (`grid_model` → `domain`).

**Opt-in statt Schema-Bump:** identische Begruendung wie
[`ADR 0060`](0060-island-grid-bilanz-pattern.md) §3 — der additive Layer
darf den netzgekoppelten MVP-Demo (Hash-Pins, Replay-Baselines) nicht
verschieben; nur ein Szenario mit Transformer-Block traegt die neuen Keys.

**Pro-Tick-Event statt Config-Exception:** die Verletzung ist ein
**Laufzeit**-Zustand (lastabhaengig, ueber Ticks akkumuliert), kein
Konstruktions-Fehler. Sie gehoert in den `TickResult`-Output-Strom (wie
Telemetry/Alarme), nicht in eine Exception. Die Config-*Validierung* (§2.1)
bleibt davon getrennt und folgt dem Config-Error-Pattern.

---

## 4. Risiken / offene Design-Fragen

- **Scheinleistungs-Basis vor 3c:** solange `S ≈ |P|`, ist die Grenze eine
  Wirkleistungs-Naeherung. 3c wechselt auf `S = sqrt(P² + Q²)` und
  **re-pinnt** die Boundary-Tests (dokumentierter Pin-Wechsel).
- **Euler-Stabilitaet:** `dt_s / τ` sollte `< 1` bleiben (τ ≫ tick_ms);
  ein zu kleines τ ueberschwingt, bleibt aber deterministisch. Szenario-
  Konfigurations-Hinweis, keine Config-Hard-Invariante (tick_ms erst zur
  Laufzeit bekannt).
- **Doppeldeutigkeit „Transformer":** Geraet (2b,
  [`ADR 0056`](0056-transformer-device-pattern.md)) vs. Netz-Grenze (3b)
  bleibt in Docstrings/ADR klar getrennt.

---

## 5. Reichweite

Gilt fuer: `hexagon/core/grid_model/config.py` (`TransformerLimitConfig` +
Feld), `hexagon/core/grid_model/bilanz.py` (Thermo-Step + State + Emission),
`hexagon/core/grid_model/snapshot.py` (opt-in Config-/State-Serialisierung),
`hexagon/core/domain/event.py` (`GridConstraintViolationEvent`),
`hexagon/core/domain/tick_result.py` (`emitted_grid_events`),
`hexagon/core/simulation/tick_loop.py` (Drain → TickResult),
`hexagon/core/scenario/loader.py` + `validator.py` (YAML-`transformer_limit`-
Block, optional), `tests/unit/hexagon/core/grid_model|simulation|scenario/`.

Gilt NICHT fuer: Blindleistung / `S = sqrt(P²+Q²)`
([`M8-welle-3c.md`](../planning/done/M8-welle-3c.md), `GG-GRID-007`),
Schutzgeraete-Logik (M4), Asset-Lifecycle/Reparatur, IEC-Loading-Guide-
Mehrzonen-Thermik (§7).

---

## 6. Akzeptanzkriterien (Trigger 021)

- [ ] `TransformerLimitConfig` additiv + validiert; YAML-`transformer_limit`-
      Block optional ladbar.
- [ ] Pro-Tick-Grenz-Check → `GridConstraintViolationEvent` in `TickResult`;
      Boundary-Pins (knapp unter/ueber + Zeit-Akkumulation ueber Ticks).
- [ ] ≥ 100-Tick-Determinismus-Property; `transformer_limit=None` bit-genau
      wie heute (Regressions-Pin).
- [ ] `make gates` gruen (`coverage-gate-critical` ≥ 90 % `grid_model`);
      NEU ADR `Accepted`; Trigger 021 aufgeloest.

---

## 7. Nicht Gegenstand dieser ADR

- **Blindleistungs-Scheinleistung** (`S = sqrt(P²+Q²)`) — 3c.
- **IEC-60076-7-Loading-Guide-Detailthermik** (Mehrzonen, Exponenten
  `2y`/`1.6`, Wickungs-Zeitkonstante) — das vereinfachte Single-Zonen-
  `load_pu²`-Modell genuegt fuer das Ersatzmodell.
- **Schutzgeraete-Logik** (Distanz-/Differentialschutz) — M4-Material.
- **Asset-Lifecycle / Reparatur-Zeiten** — Domain ist elektrisches
  Verhalten.
- **Per-Device-Saettigung** — das ist das Transformer-*Geraet*
  ([`ADR 0056`](0056-transformer-device-pattern.md)), nicht die Netz-Grenze.
