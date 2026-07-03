# ADR 0073 — Volle `GG-TERM-002/003`-Equality-Matrix: `RunMetadata`-Vollfelder + 9-Felder-Preflight (Slice 038)

**Status:** Accepted — gezogen 2026-07-03 mit Slice-038-Closure
(C4; Gates + `make fullbuild` cache-frei gruen, Release v0.3.0).
Provisional-Schritt 2026-07-03 (direkter `Proposed → Provisional`-
Sprung mit Slice-038-C0/C1, Muster [`ADR 0049`](0049-replay-lifecycle-finalize-hook.md)).
**Datum:** 2026-07-03
**Status geaendert am:** 2026-07-03 — `Proposed → Provisional`;
2026-07-03 — `Provisional → Accepted` (Slice-038-Closure C4).
**Bezug:**

- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) — Schaerfung-ohne-
  Supersedes-Pattern; diese ADR schaerft [`ADR 0049`](0049-replay-lifecycle-finalize-hook.md)
  §2.3 additiv (der 5-Felder-MVP-Preflight bleibt textlich
  unveraendert; diese ADR erweitert ihn um die 4 Vollfelder).
- [`ADR 0049`](0049-replay-lifecycle-finalize-hook.md) — geschaerfter
  Preflight-Vertrag (§2.3) + Reject-Semantik + `finalize()`-Naht.
- [`ADR 0067`](0067-run-end-seam-and-partial-run.md) — Headless-
  Run-End-Naht; der erweiterte Preflight greift unveraendert auf
  beiden Exit-Pfaden.
- [`ADR 0068`](0068-api-replay-binding-persistence.md) — `replay_of`-
  Spalte + Migration `0003` (Add-Column-Praezedenz fuer `0004`).
- [`ADR 0052`](0052-max-age-stale-quality-stage.md) §2.1 — `max_age_ms`
  ist bewusst **kein** Scenario-Feld (Scenario-Hash-Pin-Schutz);
  genau diese Klasse von Runtime-Konfiguration erfasst der
  `config_hash` (§2.4).
- [`ADR 0054`](0054-composition-asgi-entrypoint-and-scenario-hook.md) — Hook-
  Inversion Composition → Adapter (Injektions-Pfad fuer das
  Adapter-Profil, §2.3).
- [Slice 038](../planning/done/038-gg-term-002-003-full-equality-matrix.md)
  — Slice-Plan (C0-Entscheidungspunkte E-1/E-2, Tranchen, DoD).
- [`spec/lastenheft.md`](../../../spec/lastenheft.md) —
  [`GG-TERM-002`](../../../spec/lastenheft.md#gg-term-002)/[`GG-TERM-003`](../../../spec/lastenheft.md#gg-term-003)
  normative Feld-Definitionen.

---

## 1. Kontext

[`ADR 0049`](0049-replay-lifecycle-finalize-hook.md) §2.3 operationalisiert
[`GG-TERM-002`](../../../spec/lastenheft.md#gg-term-002)/003 bewusst nur
**teilweise**: der `finalize()`-Preflight vergleicht die 5 bereits
strukturierten `RunMetadata`-Felder (`scenario_hash`,
`schema_version`, `seed`, `tick_ms`, `tool_version`). Die
Lastenheft-Pflichtfelder **Plattformarchitektur**, **aktivierte
Adapter**, **Startzeit im Simulationszeitmodell** und
**Konfiguration** blieben als dokumentierter Carveout offen
([Slice 038](../planning/done/038-gg-term-002-003-full-equality-matrix.md),
1b-a-D-6).

**Code-Ist-Stand (verifiziert 2026-07-03):**

- `RunMetadata` (frozen) traegt `run_id`, `scenario_hash`,
  `schema_version`, `seed`, `tick_ms`, `started_at`, `ended_at`,
  `tool_version`, `replay_of` — keine der 4 Vollfelder.
- **`sim_start_time` hat keine Quelle:** `TelemetryPoint.simulation_time`
  ist definiert als „Simulationszeit in **ms ab Lauf-Start**";
  das Szenario-Schema (`ScenarioSimulation`: `tick_ms`/`duration_s`/
  `seed`) kennt keine Run-Level-Startzeit. Die Simulationszeit
  beginnt strukturell bei 0.
- **`enabled_adapters` hat keine Quelle:** es gibt keinen
  Adapter-Registry-/Profil-Begriff. `RunMetadata` wird an drei
  Stellen konstruiert (Composition-Demo-Setups + `POST /runs` im
  HTTP-Adapter); API-Laeufe erhalten ihr Wiring erst **spaeter**
  bei `POST /runs/{id}/start` ueber die per Hook-Inversion
  ([`ADR 0054`](0054-composition-asgi-entrypoint-and-scenario-hook.md)) registrierte
  Composition-Bridge — die Bridge ist **pro Composition-Entrypoint
  statisch**.
- **Konfiguration ausserhalb des Szenarios:** einziges
  determinismus-relevantes Runtime-Knob heute ist `max_age_ms`
  ([`ADR 0052`](0052-max-age-stale-quality-stage.md); bewusst kein
  Scenario-Feld). Wall-Clock-Pacing (`tick_interval_s`) ist
  **nicht** determinismus-relevant (reine Ablauf-Geschwindigkeit).
- `scenario_hash` liefert das Hash-Praezedenzmuster:
  `sha256(canonical_json(payload)).hexdigest()`
  (`core/serialization/canonical.py`).
- Alembic-Head ist `0003_add_replay_of.py`
  ([`ADR 0068`](0068-api-replay-binding-persistence.md)) — Add-Column-
  Praezedenz.

---

## 2. Entscheidung

### §2.1 Speicherort: `RunMetadata`-Erweiterung, kein Envelope (E-0)

Die 4 Vollfelder werden **direkt in `RunMetadata`** ergaenzt
(Praezedenz `replay_of`, [`ADR 0068`](0068-api-replay-binding-persistence.md));
**kein** separates `ReplayComparisonMetadata`-Envelope (zweite
Persistenz-Surface + Join-Pfad ohne fachlichen Mehrwert):

```python
platform_arch: str = ""            # "" = fehlend (§2.6)
enabled_adapters: tuple[str, ...] = ()  # () = fehlend (§2.6)
sim_start_time: int = 0            # ms im Simulationszeitmodell (§2.2)
config_hash: str = ""              # "" = fehlend (§2.4/§2.6)
```

Defaults halten bestehende Konstruktionen kompilierbar; die
**Reject-Semantik** (§2.6) macht fehlende Werte fail-closed
sichtbar statt still-gruen.

### §2.2 `sim_start_time` := Konstante 0 des Zeitmodells (E-1)

`sim_start_time` ist die **Startzeit im Simulationszeitmodell**
in ms — und die ist im heutigen Modell **strukturell 0**:
`simulation_time` ist als „ms ab Lauf-Start" definiert, einen
Kalenderzeit-Anker gibt es nicht.

- Entscheidung: `sim_start_time: int = 0` als **dokumentierte
  Konstante** des tick-indizierten Zeitmodells. **Kein** neues
  Scenario-Schema-Feld.
- Begruendung: ein Scenario-Feld waere ein `schema_version`-Bump —
  und `schema_version` ist selbst Preflight-Feld; der Bump wuerde
  alle bestehenden Referenzlaeufe/Preflight-Pins kaskadierend
  invalidieren, ohne dass es heute ein Kalenderzeit-Modell gibt,
  das den Wert traegt (dieselbe Abwaegung wie
  [`ADR 0052`](0052-max-age-stale-quality-stage.md) §2.1 fuer
  `max_age_ms`).
- Legacy-Backfill mit `0` ist **fachlich wahr** (alle bisherigen
  Laeufe starteten bei Simulationszeit 0) — `sim_start_time`
  braucht darum keine Fehlend-Semantik (§2.6).
- Ein spaeteres Kalenderzeit-Modell macht den Wert variabel:
  eigene Folge-ADR + bewusster Scenario-Schema-Bump.

### §2.3 `enabled_adapters` := Composition-Root-Deklaration (E-2)

Quelle ist das **statisch deklarierte Adapter-Profil des
Composition Root** — nicht Wiring-Introspection:

- `RunMetadata` wird bei `POST /runs` persistiert, **bevor** ein
  Wiring existiert; das Wiring entsteht erst bei
  `POST /runs/{id}/start` ueber die pro Entrypoint **statische**
  Composition-Bridge. Das Profil ist damit eine Eigenschaft des
  Composition Root, nicht des einzelnen Laufs.
- Jeder Composition Root deklariert sein Profil als Tupel
  kanonischer Adapter-Namen und injiziert es (Hook-Inversions-
  Pfad, [`ADR 0054`](0054-composition-asgi-entrypoint-and-scenario-hook.md)) in die
  konstruierenden Stellen; der reine Adapter-Entrypoint ohne
  Composition liefert das **leere Profil** → dessen Laeufe werden
  im Vollfeld-Preflight rejected (fail-closed, konsistent zum
  fail-closed Driver-Builder-Default in `_run_start_router`).
- **Namens-Kanonik:** Adapter-Package-Namen unter
  `adapters/driven/` bzw. `adapters/driving/` (z. B.
  `persistence_inmemory`, `http_api`), Regex `[a-z0-9_]+`;
  Kanonisierung = validieren, deduplizieren, lexikografisch
  sortieren. Persistenz-Form: **komma-separierter String** der
  kanonischen Namen (eindeutig, da Kommata im Namensraum
  ausgeschlossen sind; SQL-lesbar ohne JSON-Parsing).
- Die Kanonisierung lebt als **pure Funktion im Core**
  (`hexagon/core/domain/run.py`-Nachbarschaft); der Core liest
  **keine** Umgebung ([`GG-AR-P-004`](../../../spec/architecture.md#2-architekturprinzipien)-
  Reinheit): Werte kommen als Konstruktions-Parameter herein.

### §2.4 `config_hash` := versionierte ConfigView (E-3)

`config_hash` erfasst die **determinismus-relevante Runtime-
Konfiguration ausserhalb des Szenarios** — exakt die Klasse, die
[`ADR 0052`](0052-max-age-stale-quality-stage.md) §2.1 bewusst aus dem
Scenario-Schema herausgehalten hat:

```python
config_hash = sha256(canonical_json(config_view)).hexdigest()
# ConfigView v1:
config_view = {"config_view": 1, "max_age_ms": max_age_ms}  # int | None
```

- Verfahren identisch zum `scenario_hash`-Praezedenzmuster
  (`canonical_json` + SHA-256 hexdigest).
- Die ConfigView ist **explizit und versioniert** (`config_view`-
  Schluessel): jedes kuenftige determinismus-relevante Runtime-
  Knob ausserhalb des Szenarios MUSS in die ConfigView
  aufgenommen werden (ConfigView-Versions-Bump; additive
  ADR-0011-Schaerfung dieser ADR). Nicht-determinismus-relevante
  Knobs (Wall-Clock-Pacing, Ports, DSNs, Log-Level) bleiben
  draussen.
- Der Composition Root berechnet den Hash aus seinem statischen
  Profil (heute: `max_age_ms=None` in allen produktiven Pfaden)
  und injiziert ihn analog §2.3.

### §2.5 `platform_arch`-Normalform

- Quelle: `platform.machine()` des ausfuehrenden Prozesses,
  geliefert von Composition Root bzw. HTTP-Adapter (der Lauf
  fuehrt im selben Server-Prozess aus).
- Normalform (pure Core-Funktion): trim + lowercase (z. B.
  `x86_64`, `aarch64`). Leerer String nach Normalisierung =
  fehlend (§2.6).
- Der **Core** ruft `platform.machine()` **nicht** selbst auf
  (keine Umgebungs-Lese im Spine; Testbarkeit + Determinismus).

### §2.6 Preflight-Erweiterung: 9 Felder + Fehlend-Reject

`_REPLAY_PREFLIGHT_FIELDS` waechst von 5 auf **9** Felder:
`scenario_hash`, `schema_version`, `seed`, `tick_ms`,
`tool_version`, `platform_arch`, `enabled_adapters`,
`sim_start_time`, `config_hash`.

- **Gleichheits-Reject** (bestehende [`ADR 0049`](0049-replay-lifecycle-finalize-hook.md)-§2.3-
  Semantik, unveraendert): Ungleichheit eines Felds → Reject vor
  dem Diff, kein `replay_diff_status`, strukturierter
  `log_port`-Record.
- **NEU Fehlend-Reject** fuer `platform_arch`,
  `enabled_adapters`, `config_hash`: ist der Wert auf einer der
  beiden Seiten leer (`""` bzw. `()`), wird **vor** der
  Gleichheitspruefung rejected — Log-Detail `missing` (getrennt
  von `mismatch`). Leer==leer ist damit **kein** valider
  Vergleich: Laeufe ohne Voll-Metadaten (Legacy-Bestand vor
  Migration `0004`, Bare-Adapter-Entrypoint) sind als
  Replay-Referenz unzulaessig — das ist die normative
  [`GG-TERM-003`](../../../spec/lastenheft.md#gg-term-003)-Konsequenz
  („speichert **alle** zur Wiederholung notwendigen Metadaten").
- `sim_start_time` hat keine Fehlend-Semantik (§2.2) und wird
  rein auf Gleichheit geprueft.
- Per-Feld-Boundary-Tests (parametrisiert) fuer alle 4 Vollfelder
  in beiden Reject-Klassen (`missing` + `mismatch`) — Verlaengerung
  des [`ADR 0049`](0049-replay-lifecycle-finalize-hook.md)-C2-Pins.

### §2.7 Persistenz: Migration `0004` + differenzierter Backfill

NEU `0004_add_gg_term_full_fields.py` auf der `runs`-Tabelle:

| Spalte | Typ | Server-Default (Backfill) |
| ------ | --- | ------------------------- |
| `platform_arch` | `TEXT NOT NULL` | `''` (fehlend — ehrlich: unbekannt) |
| `enabled_adapters` | `TEXT NOT NULL` | `''` (fehlend — ehrlich: unbekannt) |
| `sim_start_time` | `BIGINT NOT NULL` | `0` (fachlich wahr, §2.2) |
| `config_hash` | `TEXT NOT NULL` | `''` (fehlend — ehrlich: unbekannt) |

`downgrade()` droppt die vier Spalten. Beide Repository-Adapter
(`persistence_inmemory`, `persistence_postgres`) mappen die
Felder bidirektional; `enabled_adapters` round-tript
Tupel ↔ komma-separierter String (§2.3).

---

## 3. Begruendung

- **Normative Luecke schliessen.** [`GG-TERM-003`](../../../spec/lastenheft.md#gg-term-003)
  fordert die Voll-Metadaten „mindestens"; der MVP-Preflight war
  eine dokumentierte Teil-Operationalisierung. Diese ADR liefert
  den vollen Feldsatz mit ehrlicher Fehlend-Semantik statt
  stillschweigender Leer-Gleichheit.
- **Kaskaden vermeiden.** Konstante 0 (§2.2) und ConfigView
  (§2.4) halten das Scenario-Schema stabil — kein
  `schema_version`-Bump, keine Pin-Invalidierung; dieselbe
  Abwaegung, die [`ADR 0052`](0052-max-age-stale-quality-stage.md)
  bereits getroffen hat.
- **Statisch statt introspektiv (§2.3).** Das Adapter-Profil als
  Composition-Root-Deklaration funktioniert an allen drei
  Konstruktionsstellen (auch `POST /runs` **vor** dem Wiring)
  und bleibt auditierbar; Wiring-Introspection braeuchte einen
  Metadaten-Update-Pfad auf der frozen/insert-only
  `RunMetadata`-Persistenz.
- **Schaerfung ohne Supersedes ([`ADR 0011`](0011-schaerfung-ohne-abloesung.md)).**
  [`ADR 0049`](0049-replay-lifecycle-finalize-hook.md) §2.3 bleibt textlich
  unveraendert; diese ADR erweitert Feldsatz + Reject-Klassen
  additiv.

---

## 4. Reichweite

- `RunMetadata` + Kanonik-Funktionen
  (`hexagon/core/domain/run.py`); ConfigView-Helper
  (`hexagon/core/serialization/`-Nachbarschaft) (C1).
- Alembic `0004` + beide Repository-Adapter (C1).
- Konstruktionsstellen: `composition/_demo_setup.py`,
  `composition/_demo_scenario_setup.py`,
  `adapters/driving/http_api/app.py` (`POST /runs`) +
  Profil-Injektion (C1).
- `_REPLAY_PREFLIGHT_FIELDS` + Fehlend-Reject in
  `TickLoop.finalize()`-Preflight
  (`hexagon/core/simulation/tick_loop.py`) + parametrisierte
  Boundary-Tests (C2).
- **Unberuehrt:** `diff_replay()`, `ReplaySample`/`ReplayDelta`,
  `control_state`-Matrix, Scenario-Schema (`schema_version`
  bleibt `grid-gym.scenario.v1`), [`ADR 0049`](0049-replay-lifecycle-finalize-hook.md)-Text.

---

## 5. Lieferung

Lieferplan, Commit-Hashes + Verifikations-Gates leben im
Slice-Plan
[`038-gg-term-002-003-full-equality-matrix.md`](../planning/done/038-gg-term-002-003-full-equality-matrix.md)
(§T Tranchen C0..C4). Status-Pfad: `Proposed → Provisional`
(C0 `0b01132`) → `Accepted` (Slice-038-Closure C4, 2026-07-03;
Release v0.3.0 `6b3a212`).

---

## 6. Konsequenzen

- **Positiv:** [`GG-TERM-002`](../../../spec/lastenheft.md#gg-term-002)/003
  voll operationalisiert; der M7-Carveout 1b-a-D-6 schliesst.
- **Positiv:** Cross-Plattform-/Cross-Konfigurations-Replays
  werden sauber rejected statt bedeutungslos gediffed.
- **Neutral:** Legacy-Laeufe (vor Migration `0004`) sind als
  Replay-Referenz unzulaessig (Fehlend-Reject §2.6) — bewusste
  fail-closed-Entscheidung; neue Laeufe tragen die Vollfelder
  automatisch.
- **Neutral:** `RunMetadata` waechst um 4 Felder mit
  Back-Compat-Defaults; direkte Test-Konstruktionen bleiben
  kompilierbar.
- **Risiko (mitigiert):** vergisst ein neuer Composition Root die
  Profil-Injektion, laufen seine Laeufe mit leerem Profil — der
  Preflight rejected sie sichtbar (`missing`-Log) statt
  falsch-gruen zu vergleichen.

---

## 7. Nicht Gegenstand dieser ADR

- **Kalenderzeit-Modell** (variables `sim_start_time`) — eigene
  Folge-ADR + bewusster Scenario-Schema-Bump (§2.2).
- **Adapter-Parameter-Hashing** (Adapter-Konfiguration jenseits
  der Namensliste, z. B. Protokoll-Profile) — additive
  Schaerfung, wenn ein Adapter-Parameter determinismus-relevant
  wird (dann via ConfigView §2.4).
- **`started_at`/`ended_at`-Setzen** + Auto-`completed` —
  unveraendert [`ADR 0049`](0049-replay-lifecycle-finalize-hook.md) §7.
- **Preflight-Policy-Konfiguration** (z. B. Feld-Whitelist fuer
  bewusste Cross-Plattform-Vergleiche) — additive Schaerfung bei
  konkretem Bedarf.
- **Severity-/Detail-Ausbau des Reject-Logs** — additive
  Schaerfung.
