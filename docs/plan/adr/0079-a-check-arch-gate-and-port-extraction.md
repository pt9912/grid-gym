# ADR 0079 — a-check Hexagon-Architektur-Gate + Port-Extraktion (AlarmHistory / FieldFrame)

**Status:** Accepted (2026-07-14) — in [`Slice 079`](../planning/done/079-a-check-hexagon-arch-gate.md)
umgesetzt (T1 `AlarmHistoryPort`, T2 `FieldFramePublishPort`, T3 Composition-Root-
Extraktion, T4 Gate-Verdrahtung); `make gates` + volle Integration-Suite grün, a-check
0 Befunde. Adoptiert das sprachagnostische Hexagon-Gate
[`a-check`](https://github.com/pt9912/a-check) (Schwester-Werkzeug zu d-check) und
schärft als Folge [`ADR 0040`](0040-alarm-aggregation-and-stream-port.md) Decision 17
+ [`ADR 0078`](0078-bess-ems-field-contract-publisher.md) (Muster
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md), Schärfung ohne Ablösung).
**Datum:** 2026-07-14
**Bezug:**

- [`ADR 0002`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) §A-1 — die
  import-linter-/`arch_check.py`-Gate-Politik (`AC-*`-Contracts), die a-check
  **komplementär** ergänzt (nicht ersetzt).
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) — Schärfung-ohne-Ablösung-Muster für
  die beiden Port-Einführungen gegen die bewusst port-losen Vorentscheidungen.
- [`ADR 0040`](0040-alarm-aggregation-and-stream-port.md) §2.3 Decision 17 — `AlarmHistoryBuffer`
  als **„bewusst kein Port"**-Adapter-Helper. Decision A schärft das zu einem interim
  `AlarmHistoryPort`, ohne die Welle-6c-`AlarmRepositoryPort`-Zielrichtung zu berühren.
- [`ADR 0078`](0078-bess-ems-field-contract-publisher.md) — der `BessEmsFieldPublishAdapter`
  mit `publish_tick(TickResult)`-Surface (Tick-Frame-Aggregation), die **nicht** in den
  per-Punkt-`FieldPublishPort` ([`ADR 0075`](0075-field-server-surface-device-endpoint-port.md))
  passt. Decision B abstrahiert sie hinter `FieldFramePublishPort`.
- [`ADR 0054`](0054-composition-asgi-entrypoint-and-scenario-hook.md) — der Composition-Root
  `grid_gym.composition.asgi`, in den Decision C das Default-Demo-Wiring invertiert.
- [`GG-AR-P-002`](../../../spec/architecture.md#2-architekturprinzipien) (Hexagonale
  Architektur, Ports & Adapters), [`GG-QG-002`](../../../spec/lastenheft.md#gg-qg-002)
  (Container-/Toolchain-Gate).

---

## 1. Kontext

grid-gym setzt hexagonale Grenzen heute mit **zwei** Gates durch
([`ADR 0002`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) §A-1): import-linter
(`forbidden`-Contracts `AC-*` in `pyproject.toml`) + `tools/arch_check.py`
(AST-Heuristiken für `GG-AR-TABU-*`). Beide sind **python-spezifisch** und
contract-listen-basiert.

[`a-check`](https://github.com/pt9912/a-check) ist ein sprachagnostischer
Hexagon-Validator (Schwester-Werkzeug zu d-check, selber Autor, selbe Hermetik:
Docker, `--network none`, read-only, digest-gepinnt). Er prüft Schicht-/Richtungs-
Reinheit **kategorial** aus einer deklarierten `.a-check.yml` statt aus einer
Verbots-Liste. Seine `lateral-adapter`-Regel (Adapter importiert anderen Adapter)
prüft eine Kante, die import-linters `AC-ADAPTER-PURE` **nicht** abdeckt (das verbietet
nur Adapter→`core.{logic}`, nicht Adapter→Adapter).

Der Baseline-Lauf gegen grid-gym (faithful Schicht-Mapping, siehe §2.2) meldet **7
`lateral-adapter`-Befunde**: der `http_api`-Driving-Adapter importiert vier driven-
Adapter — teils als **Typ** (`AlarmHistoryBuffer`, `BessEmsFieldPublishAdapter`; beide
heute bewusst port-los), teils als **Instanz** (`app.py`-env-Demo-Bootstrap). Die
Befunde sind echtes Signal (unvollständige Composition-Root-Extraktion + zwei port-lose
Adapter-Kopplungen), kein Fehlalarm.

---

## 2. Entscheidung

### §2.1 a-check als komplementäres Architektur-Gate adoptieren

a-check wird als **drittes** Architektur-Gate adoptiert (`make a-check`), **additiv** zu
import-linter + `arch_check.py`. Rollenteilung:

- **import-linter** bleibt autoritativ für die **feinkörnigen** Kern-Subpaket-Regeln
  (`AC-PORTS-NO-OUT`/`AC-ADAPTER-PURE`: Ports/Adapter dürfen `core.domain` referenzieren,
  aber nicht `core.{simulation,devices,scenario,replay,faults,agents}`) und die
  Framework-/IO-Tabus (`AC-NO-FW`/`AC-NO-IO-MOD`).
- **a-check** ergänzt die **kategorialen** Schicht-/Richtungs-Regeln, die als
  Contract-Liste umständlich sind: `lateral-adapter` (Adapter→Adapter), `port-direction-mismatch`,
  `core-impurity`/`app-impurity`/`port-impurity` gegen die deklarierten Rollen.

Integration analog d-check: digest-gepinntes Image (`A_CHECK_IMAGE`), `a-check.mk`-Include
(`a-check --print-mk`), Aufruf über `make a-check`. Das Gate hängt am lokalen
`arch-check`-Verbund; ein hermetischer Docker-Lauf ohne Netz macht es CI-tauglich.

### §2.2 Schicht-Mapping (faithful, aus grid-gyms eigener domain/app-Grenze)

`.a-check.yml` mappt grid-gyms Struktur so, dass die Rollen grid-gyms **bestehende**
import-linter-Grenze spiegeln (kein neuer Vertrag, nur eine zweite Formulierung):

- **`domain`** (role domain, port-frei): `core/{domain,commands,grid_model,serialization,errors}`
  — der pure Wert-/Typ-Kernel (importiert per Baseline keinen Port).
- **`app`** (role app, darf driven Ports importieren): `core/{simulation,devices,scenario,replay,faults,agents}`
  — genau die Subpakete, die `AC-PORTS-NO-OUT`/`AC-ADAPTER-PURE` als Import-Ziel verbieten
  (= die Use-Case-/Entitäten-Schicht, die driven Ports konsumiert, DIP).
- **`ports`** (role port): `hexagon/ports/**`; **`adapters`** (role adapter): `adapters/**`;
  **`composition_root`**: `composition/**` (von Schicht-Regeln ausgenommen).

Konsequenz: a-checks Default-`core-impurity` (domain importiert Port) wäre für grid-gyms
DIP-Kern (Kern importiert driven Ports) falsch-positiv — das domain/app-Split löst es
faithful auf. Die neue Regel, die a-check ggü. import-linter **hinzufügt**: der pure
`domain`-Kernel bleibt port-frei (Regressions-Schutz gegen künftige Port-Leaks in
`core/domain`).

### §2.3 Decision A — `AlarmHistoryPort` (Schärfung ADR 0040 Decision 17)

[`ADR 0040`](0040-alarm-aggregation-and-stream-port.md) §2.3 Decision 17 hielt den
`AlarmHistoryBuffer` **bewusst port-los** („Adapter-internes Helper-Konzept"), bis
Welle-6c ihn durch eine Postgres-`AlarmRepositoryPort`-Implementation ersetzt. Das
verursacht die Adapter→Adapter-Typ-Kopplung (`_dependencies.py`/`_alarm_setup.py`/
`_tick_loop_driver.py` importieren den konkreten Buffer-Typ).

**Schärfung (ADR-0011-Muster, keine Ablösung):** Es wird **jetzt** ein interim
`AlarmHistoryPort` (Driven-Port, `hexagon/ports/driven/alarm_history.py`) eingeführt —
`@runtime_checkable Protocol` mit der **heutigen** Buffer-Surface `append(alarm)` +
`get_recent(run_id, *, limit)`. `AlarmHistoryBuffer` erfüllt ihn strukturell (keine
Signatur-Änderung). Die drei Driving-Adapter-Referenzen typisieren gegen den Port statt
den konkreten Adapter.

- **Zielrichtung unberührt:** Der Welle-6c-`AlarmRepositoryPort` (`save`/`get_recent`/`exists`,
  [`ADR 0040`](0040-alarm-aggregation-and-stream-port.md) §3.3) bleibt der produktive
  Persistenz-Vertrag; `AlarmHistoryPort` ist der **interim Lese-/Append-Vertrag** des
  In-Memory-Stubs, den 6c subsumiert/ablöst. Decision 17s „kein Port" wird also nicht
  falsch — es wird von „kein Port" zu „interim Port jetzt, produktiver Port mit 6c"
  präzisiert.
- **Pin-neutral:** rein additive Typ-Umstellung; keine Verhaltens-/Serialisierungs-Änderung.

### §2.4 Decision B — `FieldFramePublishPort` (Schärfung ADR 0078)

Der `BessEmsFieldPublishAdapter` ([`ADR 0078`](0078-bess-ems-field-contract-publisher.md))
publisht einen **Tick-Frame** (`publish_tick(result: TickResult)`) — semantisch verschieden
vom **per-Punkt**-`FieldPublishPort` (`publish(point)`,
[`ADR 0075`](0075-field-server-surface-device-endpoint-port.md) §2.1). Der Driver typisiert
ihn deshalb heute konkret (`BessEmsPublishProvider = Callable[[], BessEmsFieldPublishAdapter | None]`).

**Schärfung:** Es wird ein generischer `FieldFramePublishPort` (Driven-Port,
`hexagon/ports/driven/field_frame_publish.py`) eingeführt — `@runtime_checkable Protocol`
mit `start()` / `publish_tick(result: TickResult)` / `stop()`, **Schwester-Port** zu
`FieldPublishPort` (getrennter Vertrag, ADR-0075-Schwester-Muster: per-Punkt vs.
Tick-Frame). `BessEmsFieldPublishAdapter` erfüllt ihn strukturell; der Driver-Provider
typisiert gegen den Port. `TickResult` ist ein `core.domain`-Typ (Port→domain erlaubt).

### §2.5 Decision C — Default-Demo-Wiring in den Composition-Root invertieren

Der env-getriebene Demo-Bootstrap in `app.py`
(`_configure_scenario_demo_from_env_if_requested`) instanziiert die driven-Adapter
(`InMemoryRunRepository`/`InMemoryTelemetryStream`/`InMemoryAlarmStream`/`AlarmHistoryBuffer`)
**im Adapter**. Das wird — analog der bereits invertierten `_register_scenario_configurator`-
Naht ([`ADR 0054`](0054-composition-asgi-entrypoint-and-scenario-hook.md)) — per Registrier-Hook in den
Composition-Root `grid_gym.composition.asgi` verlagert. `app.py` importiert danach **keinen**
driven-Adapter mehr; der Default-Konfigurator ist fail-closed (kein registrierter
Composition-Root → klare Diagnose, wie schon beim Scenario-Konfigurator).

Die verbliebene `app.py`-Kopplung an `telemetry_stream_inmemory` stammte aus dem
**toten** Welle-3-`DemoTelemetryGenerator`-Producer-Wiring (`isinstance`-Lifespan-Guards
+ optionaler `configure_telemetry_stream(demo_generator=…)`-Pfad). Seit Welle 5 publisht
der `DemoTickLoopDriver` reale Telemetrie; **kein Aufrufer** setzte je `demo_generator`,
der Guard war immer False. Statt diesen toten Pfad zu invertieren, wird er **entfernt**
(die `DemoTelemetryGenerator`-Adapterklasse + ihr Unit-Test bleiben; nur das app.py-Wiring
entfaellt). Der Verhaltensvertrag ist damit identisch (der Guard lief nie); die
Welle-5-Review-Guards F5/F9/F11 (Pfad-Validierung vor Setup, Sentinel-Skip-Guard,
Leerstring-env) bleiben unveraendert.

---

## 3. Konsequenzen

- **Positiv:** `http_api`-Adapter ist frei von driven-Adapter-Imports; a-check läuft
  clean (0 Befunde) und wird ein hartes, sprachagnostisches Gate. Zwei bisher implizite
  Adapter-Kopplungen sind jetzt explizite Port-Verträge. Der pure `domain`-Kernel ist
  regressionsgeschützt gegen Port-Leaks.
- **Kosten:** zwei zusätzliche Driven-Ports (interim für Alarm-History) + ein drittes
  Architektur-Gate (Docker-Lauf ~Sekunden). `AlarmHistoryPort` ist bewusst interim und
  wird mit Welle-6c re-bewertet.
- **Grenze:** a-checks Schicht-Modell ist gröber als import-linters Subpaket-Regeln —
  die feinkörnigen `AC-PORTS-NO-OUT`-Grenzen bleiben bei import-linter. a-check ist
  **komplementär**, kein Ersatz (§2.1).
- **Offen (Trigger-Kandidat):** a-checks Richtungs-Regeln (`port-direction-mismatch` via
  explizite `direction: driving/driven`) sind in diesem Slice **nicht** aktiviert
  (Schichten ohne `direction`); eine spätere Tranche kann sie scharf schalten.
