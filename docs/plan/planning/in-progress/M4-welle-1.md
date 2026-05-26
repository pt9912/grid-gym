# Welle 1 — M4 DeviceProtocolPort-Foundation

**Status:** In Progress — eroeffnet 2026-05-26 nach
M4-Welle-0-Closure (`f832048` C2 + `556ae9f` Self-Close-Move
+ `24b32ca` Pre-C0-Sync). Welle 1 ist die **erste
Code-Welle** in M4; legt die `DeviceProtocolPort`-Surface
(`GG-AR-PORT-DRN-007`) plus ersten M4-ADR an. Welle 1
schreibt **noch keine konkreten Protokoll-Adapter** (das ist
Welle 2: MQTT als erster konkreter Implementer; Welle 3:
Modbus; Welle 4: OPC-UA; Welle 5: DNP3+IEC-Disposition).

Kanonische Slice-Spezifikation:
[`M4-protocol-adapters.md §3 Welle 1`](M4-protocol-adapters.md)
— dieses Dokument ist lesefreundlicher Index + per-Welle-
Tracking, nicht Ersatz.

**Spec-Reife:** Inhaltlich final. Decisions aus
[`../done/M4-welle-0.md`](../done/M4-welle-0.md) §3
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
  [`spec/architecture.md §7`](../../../../spec/architecture.md)
  Z. 249 + [`§8.2`](../../../../spec/architecture.md)
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
     ADR §2 — Default-Vorschlag ist **bei
     `TickLoop.run()`-Start** (Replay-Mode laesst Adapter
     weg; Adapter-Lifetime == Run-Lifetime, nicht
     Service-Lifetime).
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

- [`spec/architecture.md §7`](../../../../spec/architecture.md)
  Z. 249 (`GG-AR-PORT-DRN-007` Tabelle) +
  [`§8.2`](../../../../spec/architecture.md) Z. 510–512
  (Adapter-Interfaces-Driven-Beschreibung).
- [`spec/lastenheft.md §16`](../../../../spec/lastenheft.md)
  Z. 1120–1163 (`GG-MQTT/MODB/OPCUA/DNP3/IEC-001`).
- [`../done/M4-welle-0.md`](../done/M4-welle-0.md) §3
  Decision-Liste (Items 1, 2, 3, 7) als Quelle der
  Decision-Vorbelegung.
- [`M4-protocol-adapters.md`](M4-protocol-adapters.md) §3
  Welle 1 (kanonische Slice-Spezifikation).
- [`ADR 0011`](../../adr/0011-schaerfung-ohne-abloesung.md)
  als Pattern-Anker: ADR 0030 ist neuer Port-Slot, kein
  Supersede; aber ADR 0030 verweist auf
  [`ADR 0015`](../../adr/0015-snapshot-envelope-v2.md) §2
  fuer den Schema-Bump-Pfad (Decision 7
  Reversibilitaet).
- [`ADR 0021`](../../adr/0021-scenario-loader-and-tick-loop-event-wiring.md)
  §2.5 (`TickLoop.run()`-Pre-Tick-Block) als
  Lifecycle-Anker fuer Decision 3.

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

### C0 — `docs(plan)`: M4-welle-1 Slice-Doc (Welle-Beginn)

- Dieses Dokument als Welle-Start-Marker. Status:
  `In Progress`.
- Kein README-Sync noetig: `in-progress/README.md` zeigt
  bereits den Welle-0-Closure-Stand inkl. „Naechster
  aktiver Schritt: M4-Welle-1". Welle-1-Doc-Eintrag in
  `in-progress/README.md` kommt **nicht** als eigener
  Bestand-Tabellen-Zeile (analog M3-Welle-1; Welle-N-Docs
  ab Welle 1 sind Tracking, nicht Roadmap-Bestand).

### C1 — `docs(adr)`: ADR 0030 Proposed — DeviceProtocolPort-Surface

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

### C2 — `feat(welle-1)`: DeviceProtocolPort + Tests

- NEU `src/grid_gym/hexagon/ports/driven/device_protocol.py`
  mit `DeviceProtocolPort`-`Protocol`-Klasse +
  `*Error`-Subsystem.
- NEU `tests/unit/hexagon/ports/test_device_protocol.py`
  mit Vertragsverhalten (Lifecycle-Reihenfolge,
  `*Error`-Hierarchie, optional Stub-Adapter).
- `make gates` cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override (Default-Liste muss noch
  **nicht** um `ports/driven/device_protocol` erweitert
  werden — neue Port-Datei ist trivial und faellt unter
  bestehende `ports/driven`-Coverage-Sweep, falls
  vorhanden; sonst in C3 nachziehen).

### C3 — `docs(plan|adr)`: Welle-1 Status/DoD-Sync + ADR-Schaerfung

- ADR 0030 `Proposed → Provisional` mit C2-Merge-Beleg.
- `M4-welle-1.md`-Status `In Progress → Done` mit
  C0/C1/C2-Hashes.
- `M4-protocol-adapters.md §3 Welle 1`: Done-Status mit
  Commit-Belegen; Decisions-Vorbelegung-Liste in C3
  durchgehakt.

---

## 5. Critical Files

| Pfad                                                                | Commit | Aktion                                |
| ------------------------------------------------------------------- | ------ | ------------------------------------- |
| `docs/plan/planning/in-progress/M4-welle-1.md`                      | C0     | NEU                                   |
| `docs/plan/adr/0030-device-protocol-port-surface.md`                | C1     | NEU (`Proposed`)                      |
| `src/grid_gym/hexagon/ports/driven/device_protocol.py`              | C2     | NEU (`DeviceProtocolPort`-Protocol)   |
| `tests/unit/hexagon/ports/test_device_protocol.py`                  | C2     | NEU (Protocol-Vertragsverhalten-Tests)|
| `docs/plan/adr/0030-device-protocol-port-surface.md`                | C3     | EDIT (`Proposed → Provisional`)       |
| `docs/plan/planning/in-progress/M4-welle-1.md`                      | C3     | EDIT (Status → Done; Hashes)          |
| `docs/plan/planning/in-progress/M4-protocol-adapters.md`            | C3     | EDIT (§3 Welle 1 Done-Sync)           |

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
3. **C2 (feat)**:
   - `make test-unit` gruen (neue Protocol-Tests + alle
     bestehenden 1138 Unit-Tests bleiben gruen).
   - `make arch-check` gruen (`AC-ADAPTER-LIGHTWEIGHT`-
     Pfad-Filter erfasst weiterhin `protocol_*` —
     Regression-Schutz).
   - `make gates` cache-frei gruen ohne
     `CRITICAL_COV_TARGETS`-Override.
   - `make fullbuild` gruen (Compose-Smoke unveraendert).
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
  TickLoop-Start zu Latenz-Spitzen am ersten Tick fuehrt,
  muss Welle 2 die Lifecycle-Entscheidung in C2-Folge-ADR
  schaerfen. *Mitigation*: Reconnect-Logik im Adapter +
  Lazy-Connect-Pattern als Welle-2-Decision-Folge.
- **`AC-ADAPTER-LIGHTWEIGHT`-Filter Regression durch
  Refactoring**: ein paralleler Welle-2-Commit koennte
  versehentlich den Filter aufweichen (z. B. wenn der
  `bucket.startswith("protocol_")`-Check umgeschrieben
  wird). *Mitigation*: Welle 1 C2 fuegt einen
  Architektur-Test hinzu, der die Filter-Wirksamkeit
  verifiziert (Property-Test: ein
  `protocol_dummy/`-Modul mit hoher Komplexitaet **muss**
  ein `AC-ADAPTER-LIGHTWEIGHT`-Violation triggern).
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
