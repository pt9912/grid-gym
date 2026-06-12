# Welle 1 — M4 DeviceProtocolPort-Foundation

**Status:** Done — geschlossen 2026-05-30 mit M4-Welle-1-C3
(`docs(plan|adr)` Doc-Sync, dieser Commit). Eroeffnet
2026-05-26 nach M4-Welle-0-Closure (`f832048` C2 + `556ae9f`
Self-Close-Move + `24b32ca` Pre-C0-Sync). Welle 1 war die
**erste Code-Welle** in M4 und hat die
`DeviceProtocolPort`-Surface (`GG-AR-PORT-DRN-007`) plus
ersten M4-ADR (0030 `Provisional`) geliefert. Welle 1
schreibt **keine** konkreten Protokoll-Adapter (das ist
Welle 2: MQTT als erster konkreter Implementer; Welle 3:
Modbus; Welle 4: OPC-UA; Welle 5: DNP3+IEC-Disposition).

**Liefer-Hashes:**

- C0 `f8cbe9d` — `docs(plan): M4-welle-1 Slice-Doc (M4 Welle-1 Beginn)`.
- C1 `b840e7a` — `docs(adr): ADR 0030 Proposed — DeviceProtocolPort-Surface (M4 Welle 1)`.
- Review-Folge `ad3dff8` — `fix(welle-1): ADR-0030 Review-Folge — 3H + 4M + 5L Findings`.
- H4-Korrektur `111c464` — `fix(welle-1): ADR-0030 H4 — Decision 3 auf Caller-Scope (TickLoop.run() existiert nicht)`.
- C2 `d09adf3` — `feat(welle-1): DeviceProtocolPort + TickLoop-Lifecycle-Methoden + Tests`.
- EoD-Sync `f8ed791` — `docs: EoD-Sync 2026-05-26 — M4-Welle-1-C2-Stand in 4 Top-Level-Docs`.
- C3 (dieser Commit) — `docs(plan|adr): Welle-1 Status/DoD-Sync + ADR-0030 → Provisional`.

**DoD-Verifikation (Welle-Schluss, Stand `d09adf3` C2 +
`f8ed791` EoD-Sync + dieser Commit):**

- `make test-unit`: **1161 Tests gruen** (Pre-Welle-1-Stand
  1138 → Welle-1-Endstand 1161 = +23 Unit-Tests; davon 12
  fuer `DeviceProtocolPort`-Protocol-Surface
  (`tests/unit/hexagon/ports/driven/test_device_protocol.py`)
  und 11 fuer TickLoop-Lifecycle
  (`tests/unit/hexagon/core/simulation/test_tick_loop_welle_1_protocol_ports.py`:
  FIFO-Start, LIFO-Stop, idempotenter Stop, Partial-Start-
  Failure-LIFO-Cleanup mit `__context__`-Chain)).
- `make test-integration`: **unveraendert gruen** (Welle 1
  ist Unit-Test-only; Integration-Smoke beginnt mit Welle 2
  / Mosquitto-Sibling).
- `make arch-check`: **19/19 Contracts KEPT** (7 via
  `lint-imports` + 12 via `tools/arch_check.py`; finales
  Gates-Echo: `arch-check (19 contracts)`);
  `AC-ADAPTER-LIGHTWEIGHT`-`protocol_*`-Pfad-Filter
  (`tools/arch_check.py:1089`
  `bucket.startswith("protocol_")`) Regression-geprueft.
- `make gates`: **cache-frei gruen** ohne
  `CRITICAL_COV_TARGETS`-Override (Default-Liste
  unveraendert — Adapter-Erweiterung kommt mit
  Welle 2/3/4).
- `make fullbuild`: **Pre-existing Drift** (krb5-CVEs
  `CVE-2026-40356` im Debian-13-Base-Image, seit
  M3-Welle-7 `c61ab0d`; **nicht durch M4-Welle-1-Code
  verursacht**; Base-Image-Bump in separatem Stack).
- ADR 0030: `Proposed → Provisional` (Decisions 2/3/7
  final, Decision 1 provisorisch Verzicht-Default;
  Status-Pfad in
  [`../../adr/0030-device-protocol-port-surface.md`](../../adr/0030-device-protocol-port-surface.md) §5
  mit Hashes belegt).

Kanonische Slice-Spezifikation:
[`../done/M4-protocol-adapters.md §3 Welle 1`](../done/M4-protocol-adapters.md)
— dieses Dokument ist lesefreundlicher Index + per-Welle-
Tracking, nicht Ersatz.

**Spec-Reife:** Inhaltlich final. Decisions aus
[`M4-welle-0.md`](M4-welle-0.md) §3
Decision-Liste werden in C1 (ADR 0030 Proposed) konkret
gewaehlt; C2 (feat) implementiert die gewaehlte Variante.

---

## 1. Context

M4-Welle-0 (`d0bb16e` Slice-Doc + `4451c60` Slice-Plan +
`9f4ee74` Review-Folge + `f832048` Trigger-Triage +
`556ae9f` Self-Close-Move + `24b32ca` Pre-C0-Sync) hat die
M4-Doc-Foundation gelegt:

- M4-Slice-Plan mit Welle 0..7-Vorbelegung.
- Welle-0-Decision-Liste mit 7 offenen Fragen.
- Trigger-Triage gegen 17 Open-Trigger (2× M4-Drift, 2× M4-
  nicht-blockend, 13× M4-fremd).
- Sub-Slicing-Schwelle scharf formuliert (max. ein Adapter
  + ein ADR + ein Integration-Smoke pro Commit).

Welle 1 ist die **Port-Foundation**:

- Neuer Driven-Port
  `src/grid_gym/hexagon/ports/driven/device_protocol.py`
  als Python-`Protocol` (`GG-AR-PORT-DRN-007`,
  [`spec/architecture.md §7`](../../../../spec/architecture.md#7-domain-modell-skizze)
  Z. 249 + [`§8.2`](../../../../spec/architecture.md#82-adapter-interfaces-driven)
  Z. 510–512).
- ADR 0030 (Proposed in C1, Provisional mit C2-Merge,
  Accepted mit M4-Welle-7-Closure) schliesst Decisions
  2 (Sync/Async), 3 (Lifecycle), 7 (Snapshot-Pflicht)
  **final** und Decision 1 (DNP3/IEC) **provisorisch
  Verzicht-Default**.
- `AC-ADAPTER-LIGHTWEIGHT`-Regression-Schutz via
  `make arch-check` (Pfad-Filter ist bereits aktiv —
  `tools/arch_check.py:1089`).
- Unit-Tests fuer das Protocol-Vertragsverhalten (Pattern
  aus `tests/unit/hexagon/ports/`).

Welle 1 schreibt **keine** konkreten Adapter-Module unter
`src/grid_gym/adapters/driven/protocol_*/`. Diese kommen
ab Welle 2 (MQTT).

---

## 2. Scope

**In Scope:**

1. NEU `src/grid_gym/hexagon/ports/driven/device_protocol.py`:
   `DeviceProtocolPort`-`Protocol` mit Read-/Write-Methode(n)
   + Lifecycle-Hooks (`start`/`stop`) + `*Error`-Subsystem.
   Konkrete Methoden-Signaturen ergeben sich aus
   ADR-0030-Decision (Sync/Async-Vertrag).
2. NEU `docs/plan/adr/0030-device-protocol-port-surface.md`
   in C1 als `Proposed`. Entscheidungen:
   - **Decision 2 (Sync vs. async, final)**: konkrete Wahl
     in ADR §2 — Default-Vorschlag des Initial-Entwurfs ist
     **sync-`Protocol` mit Adapter-internem Event-Loop-
     Thread + Queue** (Pattern-Praezedenz pruefen:
     [`telemetry_otlp/`](../../../../src/grid_gym/adapters/driven/telemetry_otlp/)).
   - **Decision 3 (Lifecycle, final)**: konkrete Wahl in
     ADR §2 — Review-Folge-Wahl ist **expliziter
     Caller-Scope**:
     `start_protocol_ports()`/`stop_protocol_ports()`
     wrappen die bestehende Caller-getriebene Tick-
     Schleife (Replay-Mode laesst Adapter weg;
     Adapter-Lifetime == Run-Scope, nicht Service-
     Lifetime).
   - **Decision 7 (Snapshot-Pflicht, final)**:
     **stateless aus Replay-Sicht**; Reconnect-State ist
     volatile. Reversibilitaet via ADR-0015-Pattern
     (Schema-Bump, falls Welle 3+ Persistenz-Bedarf zeigt).
   - **Decision 1 (DNP3 + IEC-61850 Disposition,
     provisorisch)**: ADR schreibt den Verzicht-Default
     provisorisch fest. Finale Disposition in Welle 5
     informiert durch asyncua-Erfahrung aus Welle 4.
3. Unit-Tests unter `tests/unit/hexagon/ports/` fuer das
   Protocol-Vertragsverhalten (Lifecycle-Aufruf-Reihenfolge,
   `*Error`-Hierarchie, optional ein In-Memory-Stub-Adapter
   zur Vertrags-Verifikation).
4. `tools/arch_check.py`-Sanity: `make arch-check` cache-
   frei gruen; verifiziert, dass die `protocol_*`-
   Erfassung (`bucket.startswith("protocol_")`,
   `tools/arch_check.py:1089`) noch greift. Keine
   Code-Aenderung an `arch_check.py` noetig.
5. C3-Doc-Sync zieht `M4-welle-1.md`-Status auf `Done`
   und schaerft den ADR 0030 von `Proposed` auf
   `Provisional`. (Endgueltige Akzeptanz erst mit
   M4-Welle-7-Closure.)

**Anti-Scope:**

- **Keine konkreten Adapter-Module** unter
  `src/grid_gym/adapters/driven/protocol_*/`. MQTT-,
  Modbus-, OPC-UA-, DNP3-, IEC-Implementer kommen ab
  Welle 2.
- **Keine Integration-Tests via testcontainers**. Welle 1
  ist Unit-Test-only; Integration-Smoke beginnt mit
  Welle 2 (Mosquitto-Sibling).
- **Keine Scenario-Schema-Erweiterung** fuer Protokoll-
  Profile. Decision 4 (Profile-Deklaration) wandert in
  Welle 2 mit dem ersten konkreten Adapter (MQTT setzt
  das Pattern: inline im YAML, separat oder hybrid).
- **Keine Bewegung der 17 Open-Trigger**. 004 (canonical
  encoder) und 006 (`--strict-bytes`) bleiben in `open/`
  bis Welle 6 (Re-Eval-Notiz).
- **Kein M4-DoD-Checkbox-Abhaken** in `roadmap.md`. Welle 1
  liefert noch keinen der 7 Checkbox-Items (alle 5
  Adapter + AC-ADAPTER-LIGHTWEIGHT + Integration-Tests
  kommen ab Welle 2).

---

## 3. Architektur-Entscheidungen

Welle 1 bringt **eine** neue ADR: **ADR 0030**
(`docs/plan/adr/0030-device-protocol-port-surface.md`),
Status-Pfad `Proposed → Provisional → Accepted`:

- **`Proposed`** mit C1 (dieser Welle): Initial-Entwurf mit
  Decision-Vorschlaegen + Begruendung + Alternativen +
  Konsequenzen. Pattern analog ADR 0022 (M3-Welle-1).
- **`Provisional`** mit C2-Merge (feat-Commit, der die
  Decision-Variante implementiert + Tests gruen).
- **`Accepted`** mit M4-Welle-7-Closure (analog
  ADR 0022..0027).

**Bezug:**

- [`spec/architecture.md §7`](../../../../spec/architecture.md#7-domain-modell-skizze)
  Z. 249 (`GG-AR-PORT-DRN-007` Tabelle) +
  [`§8.2`](../../../../spec/architecture.md#82-adapter-interfaces-driven) Z. 510–512
  (Adapter-Interfaces-Driven-Beschreibung).
- [`spec/lastenheft.md §16`](../../../../spec/lastenheft.md#16-kommunikationsschnittstellen)
  Z. 1120–1163 (`GG-MQTT/MODB/OPCUA/DNP3/IEC-001`).
- [`M4-welle-0.md`](M4-welle-0.md) §3
  Decision-Liste (Items 1, 2, 3, 7) als Quelle der
  Decision-Vorbelegung.
- [`../done/M4-protocol-adapters.md`](../done/M4-protocol-adapters.md) §3
  Welle 1 (kanonische Slice-Spezifikation).
- [`ADR 0011`](../../adr/0011-schaerfung-ohne-abloesung.md)
  als Pattern-Anker: ADR 0030 ist neuer Port-Slot, kein
  Supersede; aber ADR 0030 verweist auf
  [`ADR 0015`](../../adr/0015-snapshot-envelope-v2.md) §2
  fuer den Schema-Bump-Pfad (Decision 7
  Reversibilitaet).
- [`ADR 0021`](../../adr/0021-scenario-loader-and-tick-loop-event-wiring.md)
  §2.8 (Tick-Reihenfolge / Vor-Tick-Block) als
  Praezedenz-Anker fuer Decision 3.

**Vorbelegungs-Liste fuer M4-Folge-ADRs** (kommen ab
Welle 2; werden nicht in Welle 1 angelegt):

- Welle 2: ADR fuer MQTT-Adapter-Profil (Decision 4).
- Welle 3: ADR fuer Modbus-TCP-Adapter-Profil.
- Welle 4: ADR fuer OPC-UA-Adapter-Profil.
- Welle 5: optional ADR fuer DNP3/IEC-Spike (oder
  Anhang-Verzicht-Notiz zu ADR 0030, falls Decision 1a
  endgueltig gewinnt).

---

## 4. Liefer-Reihenfolge (4 Commits)

### Pre-C0 — `chore(welle-1)`: `git mv M4-welle-0.md → done/` (bereits erledigt)

- Reiner Move-Commit `556ae9f` (rename-only;
  Memory-Konvention `feedback_git_mv`).
- Folge-Sync-Commit `24b32ca` (Link-/README-Pfade).

### C0 — `docs(plan)`: M4-welle-1 Slice-Doc (Welle-Beginn) — **Done `f8cbe9d`**

- Dieses Dokument als Welle-Start-Marker. Status:
  `In Progress` → (in C3) `Done`.
- Kein README-Sync noetig: `in-progress/README.md` zeigt
  bereits den Welle-0-Closure-Stand inkl. „Naechster
  aktiver Schritt: M4-Welle-1". Welle-1-Doc-Eintrag in
  `in-progress/README.md` kommt **nicht** als eigener
  Bestand-Tabellen-Zeile (analog M3-Welle-1; Welle-N-Docs
  ab Welle 1 sind Tracking, nicht Roadmap-Bestand).

### C1 — `docs(adr)`: ADR 0030 Proposed — DeviceProtocolPort-Surface — **Done `b840e7a`** (+ Review-Folge `ad3dff8` + H4-Korrektur `111c464`)

- NEU `docs/plan/adr/0030-device-protocol-port-surface.md`
  als `Proposed`. Inhalts-Skizze:
  - §1 Kontext (DRN-007, M4-Welle-0-Decision-Liste,
    Lastenheft §16 SOLLTE-Cluster).
  - §2 Entscheidung mit Sub-Sections:
    - §2.1 Decision 2 (Sync/Async) + Konsequenzen.
    - §2.2 Decision 3 (Lifecycle) + Konsequenzen.
    - §2.3 Decision 7 (Snapshot-Pflicht) + Konsequenzen.
    - §2.4 Decision 1 (DNP3/IEC) — provisorisch
      Verzicht-Default; finale Disposition in Welle 5.
  - §3 Alternativen (jeweils 1–2 Varianten je Decision).
  - §4 Konsequenzen (`AC-ADAPTER-LIGHTWEIGHT`-Pflicht,
    Welle-2+-Implementer-Auflagen, Schema-Bump-Pfad).
  - §5 Status-Pfad (`Proposed → Provisional → Accepted`).
- Kein Code-Pfad-Touch.
- Review-Folge `ad3dff8`: 3 High + 4 Medium + 5 Low
  Findings adressiert.
- H4-Korrektur `111c464`: Decision 3 auf expliziten
  Caller-Scope gezogen (`TickLoop.run()` existiert nicht).

### C2 — `feat(welle-1)`: DeviceProtocolPort + TickLoop-Lifecycle-Methoden + Tests — **Done `d09adf3`**

- NEU `src/grid_gym/hexagon/ports/driven/device_protocol.py`
  mit `DeviceProtocolPort`-`Protocol`-Klasse +
  `*Error`-Subsystem (`DeviceProtocolPortError` Root +
  `Start/Stop/Read/Write/UnknownTarget`-Sub-Errors).
- EDIT `src/grid_gym/hexagon/core/simulation/tick_loop.py`:
  `protocol_ports`-Konstruktor-Kwarg (Tuple, keyword-only,
  `None`-Default) + `start_protocol_ports()` (FIFO) +
  `stop_protocol_ports()` (LIFO, idempotent, Best-Effort-
  Partial-Cleanup mit `__context__`-Chain).
- NEU `tests/unit/hexagon/ports/driven/test_device_protocol.py`
  (12 Tests: Protocol-Adherence, Lifecycle-Aufzeichnung,
  Read/Write, `*Error`-Subsystem inkl. parametrize-5).
- NEU `tests/unit/hexagon/core/simulation/test_tick_loop_welle_1_protocol_ports.py`
  (11 Tests: FIFO/LIFO/Idempotenz/Partial-Cleanup/Context-
  Chain).
- `make gates` cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override (Adapter-Erweiterung
  kommt mit Welle 2/3/4).
- EoD-Sync `f8ed791` zog Top-Level-Doku
  (`README.md`/`README.de.md`/`roadmap.md`/
  `spec/architecture.md`) auf den C2-Stand.

### C3 — `docs(plan|adr)`: Welle-1 Status/DoD-Sync + ADR-Schaerfung — **Done (dieser Commit)**

- ADR 0030 `Proposed → Provisional` mit C2-Merge-Beleg
  `d09adf3` (Status-Header + §5 Status-Pfad mit Hashes).
- `M4-welle-1.md`-Status `In Progress → Done` mit
  C0/C1/C2-Hashes + DoD-Verifikation-Block (oben) +
  DoD-Checkliste (§9 unten).
- `M4-protocol-adapters.md §3 Welle 1`: Done-Status mit
  Commit-Belegen; Welle-1-Gate als erfuellt markiert.

---

## 5. Critical Files

Stand: ex-post nach Welle-1-Closure (C0..C3 + Review-Folge
`ad3dff8` + H4-Korrektur `111c464` + Linter-Folge `82f947c` +
Self-Close-Move `81b5cba` + Pre-C0-Sync `f1f9db1`). Tabelle
ist um die in C2 tatsaechlich gelandeten 5 Dateien erweitert
und auf die Closure-Pfade umgestellt.

| Pfad                                                                       | Commit | Aktion                                                          |
| -------------------------------------------------------------------------- | ------ | --------------------------------------------------------------- |
| `docs/plan/planning/done/M4-welle-1.md`                                    | C0     | NEU (eroeffnet in `in-progress/`; mit `81b5cba` nach `done/`)   |
| `docs/plan/adr/0030-device-protocol-port-surface.md`                       | C1     | NEU (`Proposed`)                                                |
| `src/grid_gym/hexagon/ports/driven/device_protocol.py`                     | C2     | NEU (`DeviceProtocolPort`-Protocol + `*Error`-Hierarchie)       |
| `src/grid_gym/hexagon/core/simulation/tick_loop.py`                        | C2     | EDIT (`protocol_ports`-Kwarg + `start_/stop_protocol_ports()`)  |
| `src/grid_gym/hexagon/core/scenario/loader.py`                             | C2     | EDIT (Builder-Symmetrie: `protocol_ports` in `TickLoopWiring` + `build_tick_loop`-Threading; +8 Zeilen, kein Schema-/Validator-Touch) |
| `tests/unit/hexagon/ports/driven/test_device_protocol.py`                  | C2     | NEU (12 Protocol-Vertragsverhalten-Tests)                       |
| `tests/unit/hexagon/core/simulation/test_tick_loop_welle_1_protocol_ports.py` | C2  | NEU (11 TickLoop-Lifecycle-Tests: FIFO/LIFO/Idempotenz/Cleanup) |
| `docs/plan/adr/0030-device-protocol-port-surface.md`                       | C3     | EDIT (`Proposed → Provisional`)                                 |
| `docs/plan/planning/done/M4-welle-1.md`                                    | C3     | EDIT (Status → Done; Hashes; DoD-Verifikation; §9 DoD-Checkliste) |
| `docs/plan/planning/done/M4-protocol-adapters.md`                   | C3     | EDIT (§3 Welle 1 Done-Sync)                                     |
| `docs/plan/adr/0030-device-protocol-port-surface.md`                       | Linter-Folge `82f947c` | EDIT (arch-check 16/16 → 19/19 = 7 lint-imports + 12 `tools/arch_check.py`) |
| `docs/plan/planning/done/M4-welle-1.md`                                    | Linter-Folge `82f947c` | EDIT (gleiche Korrektur in §0 + §9)                            |
| `docs/plan/planning/done/M4-protocol-adapters.md`                   | Linter-Folge `82f947c` | EDIT (gleiche Korrektur in §3 Welle 1)                         |
| `docs/plan/planning/done/README.md`                                        | Pre-C0-Sync `f1f9db1`  | EDIT (Bestand-Tabelle-Zeile + Closure-Stack)                   |
| `docs/plan/planning/in-progress/README.md`                                 | Pre-C0-Sync `f1f9db1`  | EDIT (Naechster-aktiver-Schritt → M4-Welle-2)                  |
| `docs/plan/planning/done/M4-protocol-adapters.md`                   | Pre-C0-Sync `f1f9db1`  | EDIT (§3 Welle 1 Slice-Doc-Ref auf `../done/`)                 |

---

## 6. Verifikationspfad

1. **C0 (Slice-Doc)**: `make docs-check` cache-frei gruen
   (alle Link-Targets aufgeloest, insbesondere
   `../done/M4-welle-0.md`,
   `../../../../spec/{architecture,lastenheft}.md`,
   `../../adr/{0011,0015,0021}-*.md`,
   `../../../../src/grid_gym/adapters/driven/telemetry_otlp/`).
2. **C1 (ADR Proposed)**: `make docs-check` gruen (neuer
   ADR-Pfad existiert, `docs/plan/adr/README.md` ggf.
   syncen).
3. **C2 (feat) — ex-post belegt**:
   - `make test-unit` gruen (1138 → **1161 Tests**: 12 neue
     Protocol-Surface-Tests + 11 neue TickLoop-Lifecycle-
     Tests).
   - `make arch-check` gruen — **19/19 Contracts KEPT**
     (7 lint-imports + 12 `tools/arch_check.py`);
     `AC-ADAPTER-LIGHTWEIGHT`-Pfad-Filter erfasst weiterhin
     `protocol_*` (Regression-Schutz, kein neuer Test).
   - `make gates` cache-frei gruen ohne
     `CRITICAL_COV_TARGETS`-Override.
   - `make fullbuild` **rot** aus Pre-existing-Grund
     (`image-audit`: krb5-CVE `CVE-2026-40356` in
     Debian-13-Base seit M3-Welle-7 `c61ab0d`; **nicht
     durch M4-Welle-1-Code verursacht**; Base-Image-Bump
     in separatem Stack). Compose-Smoke selbst unveraendert.
4. **C3 (Doc-Sync)**: `make docs-check` gruen mit
   geupdateten Status-Headern.

---

## 7. Risiken

- **Decision 2-Wahl bricht Welle 4 (OPC-UA)**: falls die
  in C1 gewaehlte Sync-Variante (Adapter-internem Event-
  Loop-Thread) sich in Welle 4 mit `asyncua` als zu
  schmerzhaft herausstellt, muss ADR 0030 in Welle 4 per
  Folge-ADR geschaerft werden (Pattern ADR 0011 ohne
  Supersedes). *Mitigation*: C1 dokumentiert die Wahl als
  `Provisional` (nach C2-Merge), nicht `Accepted` — der
  Schaerfungspfad ist offen, bis Welle 4 die Bridge real
  baut.
- **Decision 3-Wahl bricht Welle 2 (MQTT)**: `paho-mqtt`
  hat eigene Threading-Annahmen. Falls Connect-im-
  expliziten Caller-Scope zu Latenz-Spitzen am ersten
  Tick fuehrt oder Caller `try/finally`-Disziplin
  uneinheitlich wird, muss Welle 2 die Lifecycle-
  Entscheidung in C2-Folge-ADR schaerfen. *Mitigation*:
  Reconnect-Logik im Adapter + Lazy-Connect-Pattern als
  Welle-2-Decision-Folge; C2-Tests pinnen FIFO/LIFO,
  Partial-Cleanup und idempotenten Stop.
- **`AC-ADAPTER-LIGHTWEIGHT`-Filter Regression durch
  Refactoring**: ein paralleler Welle-2-Commit koennte
  versehentlich den Filter aufweichen (z. B. wenn der
  `bucket.startswith("protocol_")`-Check umgeschrieben
  wird). *Mitigation (Welle-1-Stand)*: nur
  Smoke-Regression-Schutz durch `make arch-check` (der
  bestehende `protocol_*`-Filter bleibt gruen) — **der in
  C0 vorgeschlagene Property-Test mit `protocol_dummy/`-
  Planted-Violator wurde in C2 NICHT geliefert**, da er
  ueber die Welle-1-Sub-Slicing-Schwelle geschoben haette
  (Port-Surface + Lifecycle + Tests fuellten die Welle
  bereits). *Folge-Mitigation*: Welle 2 (MQTT-Adapter)
  muss vor dem ersten produktiven `protocol_mqtt/`-Push
  entweder den Property-Test nachziehen ODER explizit auf
  Welle 6 (Cross-Adapter-Hardening) verschieben — und
  bis dahin mit Code-Review allein gegen Filter-
  Aufweichungen schuetzen.
- **Decision 7 (stateless) bricht Welle 3 (Modbus)**:
  Modbus-Read-Cursor (falls produktiv-noetig) braucht
  evtl. Persistenz ueber TickLoop-Restarts. *Mitigation*:
  Welle 1 dokumentiert den stateless-Default als
  reversibel (`ADR-0015`-Schema-Bump-Pfad); Welle 3 kann
  den Bump tragen, falls noetig.
- **C2 ueberschreitet Sub-Slicing-Schwelle**: Wenn der
  feat-Commit zusaetzlich zur Port-Surface auch erste
  Adapter-Boilerplate oder Adapter-Tests einsammelt,
  bricht die Sub-Slicing-Schwelle (max. ein Adapter pro
  Commit). *Mitigation*: C2 enthaelt **ausschliesslich**
  `device_protocol.py` + Unit-Tests; jeder Adapter-
  Boilerplate-Bedarf wandert in Welle 2.

---

## 8. Wandert nach

- `done/M4-welle-1.md` mit M4-Welle-2-Pre-C0-Move (Pattern
  aus M3: `welle-1.md` wurde mit M3-Welle-2-Pre-C0 nach
  `done/` gemoved).
- ADR 0030 bleibt in `docs/plan/adr/` (kein Move; nur
  Status-Updates).
- `M4-protocol-adapters.md` bleibt in `in-progress/` bis
  M4-Welle-7-Closure.

---

## 9. DoD-Checkliste (Welle-Schluss, mit C3 abgehakt)

Diese Liste spiegelt die §2 Scope-Items als
Checkbox-Sicht. Belege siehe **DoD-Verifikation**-Block
im Status-Header oben + §4 Liefer-Reihenfolge fuer die
per-Commit-Aktion.

**In-Scope-Items (alle abgehakt mit C3):**

- [x] **Port-Surface produktiv** — `DeviceProtocolPort`-
  `Protocol` mit `start`/`stop`/`read`/`write` + `*Error`-
  Subsystem (`DeviceProtocolPortError`-Wurzel + 5 typed
  Sub-Errors). Code:
  [`src/grid_gym/hexagon/ports/driven/device_protocol.py`](../../../../src/grid_gym/hexagon/ports/driven/device_protocol.py)
  (NEU mit C2 `d09adf3`).
- [x] **ADR 0030 angelegt** — `Proposed` (C1 `b840e7a`) →
  `Provisional` (dieser Commit), mit Decisions 2/3/7
  final und Decision 1 provisorisch Verzicht-Default.
  Code:
  [`docs/plan/adr/0030-device-protocol-port-surface.md`](../../adr/0030-device-protocol-port-surface.md).
- [x] **Unit-Tests fuer Protocol-Vertragsverhalten** —
  12 Tests (Protocol-Adherence, Lifecycle-Reihenfolge,
  Read/Write-Vertrag, `*Error`-Hierarchie inkl.
  parametrize-5). Code:
  [`tests/unit/hexagon/ports/driven/test_device_protocol.py`](../../../../tests/unit/hexagon/ports/driven/test_device_protocol.py)
  (NEU mit C2).
- [x] **`tools/arch_check.py`-Sanity** — `make arch-check`
  cache-frei gruen; 19/19 Contracts KEPT (7 lint-imports +
  12 `tools/arch_check.py`; finales Gates-Echo:
  `arch-check (19 contracts)`);
  `AC-ADAPTER-LIGHTWEIGHT`-`protocol_*`-Pfad-Filter
  (`tools/arch_check.py:1089`
  `bucket.startswith("protocol_")`) Regression-geprueft.
- [x] **C3-Doc-Sync** — `M4-welle-1.md` Status
  `In Progress → Done` (dieser Commit), ADR 0030
  `Proposed → Provisional` (dieser Commit),
  `M4-protocol-adapters.md §3 Welle 1` Done-Markierung
  (dieser Commit).

**Welle-1-Boni (ueber §2 Scope hinaus, in C2 mitgeliefert):**

- [x] **`TickLoop`-Lifecycle-Methoden** —
  `start_protocol_ports()` (FIFO) +
  `stop_protocol_ports()` (LIFO, idempotent,
  Best-Effort-Partial-Cleanup mit `__context__`-Chain).
  Code:
  [`src/grid_gym/hexagon/core/simulation/tick_loop.py`](../../../../src/grid_gym/hexagon/core/simulation/tick_loop.py)
  (EDIT mit C2).
- [x] **TickLoop-Lifecycle-Unit-Tests** — 11 Tests
  (FIFO/LIFO/Idempotenz/Partial-Cleanup/Context-Chain).
  Code:
  [`tests/unit/hexagon/core/simulation/test_tick_loop_welle_1_protocol_ports.py`](../../../../tests/unit/hexagon/core/simulation/test_tick_loop_welle_1_protocol_ports.py)
  (NEU mit C2).

**Anti-Scope-Items (alle gehalten):**

- [x] **Keine konkreten Adapter-Module** unter
  `src/grid_gym/adapters/driven/protocol_*/` —
  verifiziert: keine neue Datei unter dem Pfad in C2.
- [x] **Keine Integration-Tests via testcontainers** —
  verifiziert: `make test-integration` Test-Zahl
  unveraendert.
- [x] **Keine Scenario-Schema-Erweiterung** fuer
  Protokoll-Profile — verifiziert: kein Touch an
  `scenario/validator.py` und kein YAML-Schema-Feld in
  C2. `scenario/loader.py` wurde **mit Bedacht** um
  Builder-Symmetrie erweitert (+8 Zeilen:
  `DeviceProtocolPort`-Import + `protocol_ports`-Feld in
  `TickLoopWiring` + Threading durch `build_tick_loop`)
  — Pattern analog ADR 0021/0022/0023/0024-Kwarg-
  Symmetrie. Decision 4 (Topic/Register/Node-Profil-
  Deklaration) als YAML-Schema-Sache bleibt unangetastet
  und wandert in Welle 2 (MQTT-Adapter-ADR).
- [x] **Keine Bewegung der 17 Open-Trigger** —
  verifiziert: `docs/plan/planning/open/` unveraendert.
- [x] **Kein M4-DoD-Checkbox-Abhaken in `roadmap.md`** —
  verifiziert: `roadmap.md` §3 M4 Checkboxen weiterhin
  alle ungehakt (Welle 2..5 liefert die 5 Adapter,
  Welle 6 liefert Integration-Tests +
  `AC-ADAPTER-LIGHTWEIGHT`-Sweep-Beleg).
