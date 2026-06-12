# Welle 6a — M4 Cross-Adapter-Hardening (Mainstream)

**Status:** Done — geschlossen 2026-06-01 mit M4-Welle-6a-C4
(`docs(plan|adr)` Doc-Sync, dieser Commit). Eroeffnet
2026-06-01 nach M4-Welle-5b-Closure (`19f820a` C0 +
`88c1a33` C1 + `da8aed9` C1-Review-Folge + `944bca5` C2 +
`ca96bca` C3 + `7e0c91b` Slice-033-Review-Folge + `30860ed`
Self-Close-Move + `d78a194` Pre-C0-Sync + `838d904` Sub-
Slicing-Refactor 6→6a/6b).

Welle 6a ist die **siebte Code-Welle** in M4 und die erste
**Cross-Adapter-Querschnitts-Welle** ohne neuen konkreten
Adapter. Sie haertet die in Welle 2/3/4/5a/5b angesammelten
Pattern-Decisions und schliesst die in den frueheren Wellen
bewusst verschobenen Folge-Pflichten:

1. **`AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-Property-
   Test** (Welle-1-§7-Folge-Pflicht; in Welle 2/3/4/5a/5b
   bewusst verschoben).
2. **OTel-Span-Wrap fuer alle 5 `protocol_*`-Adapter**
   (Welle 2/3/4/5a/5b Anti-Scope; ADR 0024 §4.5 Bezug).
3. **Adapter-Profil-Index** unter `spec/protocol_profiles/`
   mit Verweisen auf ADR 0031/0032/0033/0034/0035.
4. **Trigger-004-Re-Eval** (canonical encoder).
5. **Trigger-006-Folge-Slice** (mypy `--strict-bytes`-
   Aktivierung; in Welle-3-C3 positiv re-evaluiert).

Welle 6a ist **kanonische Cross-Adapter-Welle**: jedes Item
wirkt ueber alle 5 Adapter-Pakete `protocol_mqtt`,
`protocol_modbus`, `protocol_opcua`, `protocol_dnp3`,
`protocol_iec61850`. Welle 6b (Welle-5b-Erbschaft) folgt
separat und addressiert IEC-61850-spezifische Lizenz-/
Distribution-Schaerfungen.

**Liefer-Hashes (5 Commits):**

- C0 `9776dd9` — `docs(plan): M4-welle-6a Slice-Doc (M4 Welle-6a Cross-Adapter-Hardening Beginn)`.
- C1 `9312239` — `docs(plan|spec): M4-Welle-6a-C1 — Adapter-Profil-Index + Architektur/Lastenheft-Sync`.
- C2 `9d3912f` — `feat(welle-6a): OTel-Span-Wrap fuer alle 5 protocol_*-Adapter via Composition-Wrapper`.
- Pre-C3 `81140e2` — `chore(trigger-006): git mv open/006-mypy-strict-bytes.md -> done/ (rename-only)`.
- C3 `0a5e895` — `feat(welle-6a): C3 — Planted-Violator-Test + strict_bytes + compose-Aufraeumung + Trigger-004-Re-Eval`.
- C4 (dieser Commit) — `docs(plan|adr): M4-Welle-6a-C4 — Status/DoD-Sync + Top-Level-Doku-Sync`.

**DoD-Verifikation (Welle-Schluss, Stand `0a5e895` C3 +
dieser Commit):**

- `make test-unit`: **1564 Tests gruen** (Welle-5b-
  Endstand 1537 + Slice 033-Welle-5b-Review-Folge-Updates
  → Welle-6a-Endstand 1564; netto +20 unique Welle-6a-
  Tests: 13 OTel-Span-Wrap-Tests
  (`tests/unit/adapters/driven/test_protocol_otel_wrap.py`)
  + 7 AC-ADAPTER-LIGHTWEIGHT-Planted-Violator-Tests
  (`tests/unit/test_arch_check_planted_violator.py`);
  weitere Test-Updates aus Slice 033 fliessen
  parallel mit ein).
- `make test-integration`: unveraendert gegenueber
  Welle-5b-Endstand (35 passed + 4 skipped — IEC-Smokes
  weiterhin via `pytest.mark.skip` mit 2c-Fallback-
  Begruendung; Welle-6b-Reaktivierung).
- `make arch-check`: **19/19 Contracts KEPT** (kein neuer
  Contract aus Welle-6a entstanden — OTel-Span-Wrap-
  Pattern direkt aus ADR 0024 §4.5 abgeleitet, kein
  `AC-ADAPTER-NO-TIME` notwendig).
- `make typecheck`: cache-frei gruen mit
  `strict_bytes = true` (Trigger-006-Closure produktiv;
  kein Repo-Sweep-Folge-Fix notwendig — Welle-3-C3-Re-
  Eval hatte das schon vorbereitet).
- `make gates`: **alle 9 A-1-Gates gruen** ohne
  `CRITICAL_COV_TARGETS`-Override.
- **OTel-Span-Wrap produktiv** fuer alle 5 Adapter via
  `OtelSpanWrappedDeviceProtocolPort`-Composition-
  Wrapper. Standard-Attribute (`adapter_type`/`target`/
  `operation`/`latency_ms`); Span-Naming
  `protocol.{adapter_type}.{operation}`. Adapter-Code-
  Diff: **NULL** (Welle-6a-Anti-Scope-konform).
- **Adapter-Profil-Index produktiv** unter
  `spec/protocol_profiles.md` mit 5 Adapter-Eintraegen
  + ADR-Links + Lastenheft-IDs + DoD-Belege +
  Cross-Adapter-Patterns + Welle-6a/7-Folge-Section.
- **Lastenheft §16-Implementierungs-Matrix** auf
  `✅ M4` fuer alle 5 Cluster (MQTT/Modbus/OPC-UA/DNP3/
  IEC-61850) mit Welle-Hash + ADR-Link + Slice-Pointer
  pro Cluster.
- **Architektur §8.2** Adapter-Verortung scharf mit
  Welle-1-ADR-Pfad + OTel-Span-Wrap-Pattern als
  Welle-6a-Konsequenz dokumentiert (ADR 0024 §4.5).
- **`AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-Test
  eingezogen** — Welle-1-§7-Folge-Pflicht-Closure. Test
  verifiziert dass `_check_adapter_lightweight` die
  Filter-Korrektheit haelt (Pfad-Filter-Praezision +
  Schwellwert-Korrektheit + Adapter-Bucket-Filter).
- **Trigger 006 Closure** produktiv: `strict_bytes =
  true` aktiv (`pyproject.toml`); Trigger-Doc von
  `open/` nach `done/` gewandert.
- **Trigger 004 Re-Eval-Defer** dokumentiert: kein
  messbarer Performance-Druck; Re-Eval-Pflicht in
  M5-Welle-0 oder M6-Welle-0.
- **`tests/integration/compose.yml`-Header-
  Konsolidierung**: Sibling-Inventar in zwei
  strukturierte Tabellen (CONTAINER + IN-PROCESS) mit
  Lizenz-Spalte; Welle-5b-Sonderfall (2c-Mock-only-
  Fallback) + GPL-Lizenz-Boundary (ADR 0035 Decision
  I-f) explizit.

Kanonische Slice-Spezifikation:
[`M4-protocol-adapters.md §3 Welle 6a`](M4-protocol-adapters.md)
— dieses Dokument ist lesefreundlicher Index + per-Welle-
Tracking, nicht Ersatz.

**Spec-Reife:** Items 1-5 sind alle in Welle 2/3/4/5a/5b
durch Anti-Scope-Markierung oder Forward-Pointer
vorbelegt. Welle-6a-C1..C3 ziehen die Items produktiv
durch; keine neuen ADR-Decisions notwendig (alle Pattern-
Decisions sind in ADR 0024 / ADR 0030..0035 fixiert).
**Eventueller neuer ADR**: falls Welle-6a-C2 OTel-Span-
Wrap eine pattern-relevante Sub-Decision erzeugt (z. B.
`TracePort`-Span-Lifecycle relativ zu `DeviceProtocolPort.
read/write`), kann ein ADR 0036 `Proposed` reinkommen.
**Eventueller neuer arch_check-Contract**: `AC-ADAPTER-
NO-TIME` (analog `AC-OTLP-ADAPTER-NO-TIME`-Pattern aus
M3-Welle-6) falls die OTel-Span-Wrap-Implementierung
zeigt, dass `time.*`-Imports in Adapter-Code unerwuenscht
sind. 19/19 → 20/20 Contracts moeglich.

---

## 1. Context

M4-Welle-5b hat den fuenften und letzten konkreten
`DeviceProtocolPort`-Implementer produktiv geliefert
(`Iec61850DeviceProtocolPort`, ADR 0035 `Provisional` +
Slice-033-Schaerfung). M4 hat damit alle 5 Adapter-Pakete
(MQTT/Modbus/OPC-UA/DNP3/IEC-61850) als individuelle
Implementer auf der `DeviceProtocolPort`-Surface
(`GG-AR-PORT-DRN-007`).

Welle 6a ist die **Querschnitts-Welle**: ohne neuen
Adapter, mit Cross-Pattern-Decisions die ueber alle 5
Adapter wirken.

**Welle-1-§7-Folge-Pflicht** (siehe
[`../done/M4-welle-1.md`](M4-welle-1.md)):
`AC-ADAPTER-LIGHTWEIGHT` ist ein `arch_check.py`-Contract,
der die "Pakete unter `adapters/driven/protocol_*/` halten
sich an die `DeviceProtocolPort`-Surface"-Eigenschaft
verifiziert. Welle 2/3/4/5a/5b haben den Smoke-Regression-
Schutz via `make arch-check` 19/19 KEPT, **aber** keinen
**Planted-Violator-Property-Test**: ein Test, der
absichtlich eine AC-Verletzung einbaut und prueft, dass
`arch_check.py` sie tatsaechlich faengt (statt false-clean
zu sein). Welle 6a-C3 zieht diesen Test ein.

**ADR 0024 §4.5 OTel-Span-Wrap-Bezug**: ADR 0024 hat den
`TracePort`-Vertrag (M3-Welle-5) und das OTLP-Adapter-
Trio (M3-Welle-6) fixiert. §4.5 hat **explizit** die
Welle-6+-Schaerfung fuer die `DeviceProtocolPort`-
Adapter vorgesehen: jeder `read(target)`/`write(target,
command)`-Call sollte einen TracePort-Span umschliessen
mit Attributen `target`/`adapter_type`/`reference`/
`operation`. Welle 6a-C2 implementiert das fuer alle 5
Adapter.

**Trigger-006-Re-Eval-Status (siehe
[`../done/006-mypy-strict-bytes.md`](006-mypy-strict-bytes.md);
nach M4-Welle-6a-C3 Closure und Self-Close-Move
`81140e2` von `open/` nach `done/` gewandert):**
in M4-Welle-3-C3 wurde die `--strict-bytes`-Aktivierung
positiv re-evaluiert (Modbus-Codec verwendet `bytes`-
Slicing produktiv; kein Untypisierungs-Issue). Welle 6a-C3
zieht die Aktivierung produktiv in `[tool.mypy]
strict_bytes = true` und macht einen Repo-Sweep.

**Trigger-004-Re-Eval-Status (siehe
[`../open/004-canonical-encoder-alternative-adr.md`](../open/004-canonical-encoder-alternative-adr.md)):**
das `canonical_json`-Encoding ist Welle-2-MQTT-Decision-4b-
Default. Trigger 004 schaerft auf `orjson`/`msgspec`-
Alternative, falls MQTT-Publish-Throughput-Druck messbar
wird. Welle 6a-C3 prueft das per Compose-Smoke-Benchmark
(falls signifikant, neue ADR 0036; sonst Trigger-Body-
Notiz mit Defer).

---

## 2. Scope

**In Scope (alle 5 Adapter-Pakete betroffen, falls nicht
anders angegeben):**

1. **NEU `spec/protocol_profiles/README.md`** oder
   aequivalent (C1): kanonischer Adapter-Profil-Index
   mit Verweisen auf ADR 0031..0035 (5 Adapter-Profile)
   + Lastenheft-IDs (`GG-MQTT-001` / `GG-MODB-001` /
   `GG-OPCUA-001` / `GG-DNP3-001` / `GG-IEC-001`) +
   Cluster-Status-Spalte (Provisional/Accepted) + DoD-
   Belege. Pattern-Praezedenz: `spec/architecture.md` §7
   Tabelle als Vorbild fuer Tabellen-Struktur.

2. **EDIT `spec/lastenheft.md` §16-Implementierungs-Matrix
   (C1)**: `🔲 M4` → `✅ M4` fuer alle 5 Adapter-Cluster
   (MQTT/Modbus/OPC-UA/DNP3/IEC-61850). Hinweis-Block
   fuer ADR-0035-Decision-I-f Lizenz-Boundary-Pattern
   (GPLv3-Sub-Modul).

3. **EDIT `spec/architecture.md` §8.2 (C1)**: Adapter-
   Verortung scharf setzen — alle 5 `protocol_*`-Adapter
   als konkrete `DeviceProtocolPort`-Implementer
   referenziert; OTel-Span-Wrap-Pattern als Welle-6a-
   Konsequenz dokumentiert.

4. **NEU `src/grid_gym/adapters/driven/_protocol_otel_wrap.py`**
   oder aequivalent (C2): generischer OTel-Span-Wrap-
   Decorator/Helper fuer `DeviceProtocolPort.read(target)`-
   und `.write(target, command)`-Calls. TracePort-Span mit
   Standard-Attributen (`adapter_type`, `target`,
   `reference`, `operation`, `latency_ms`). Wird in alle 5
   `protocol_*`-Adapter eingebunden (C2-Slice).

5. **EDIT alle 5 `protocol_*/__init__.py` oder `_port.py`**
   (C2): OTel-Span-Wrap des Adapter-Konstruktors oder via
   `read()`/`write()`-Decorator (Architektur in C2 zu
   entscheiden). TracePort wird per Dependency-Injection
   aus Welle-1-`build_protocol_ports`-Hook geladen
   (NullTracePort als Default in Tests).

6. **NEU 1+ Test-Files unter
   `tests/unit/adapters/driven/`** (C2): Cross-Adapter-
   OTel-Span-Wrap-Tests; verifiziert dass jeder
   `read()`/`write()`-Call einen Span erzeugt mit
   korrekten Attributen.

7. **NEU `tests/unit/tools/test_arch_check_planted_violator.py`**
   (C3): Welle-1-§7-Folge-Pflicht. Test instantiiert ein
   Mock-Adapter-Modul mit absichtlicher
   `AC-ADAPTER-LIGHTWEIGHT`-Verletzung (z. B. Adapter
   importiert `hexagon.core.simulation.tick_loop` direkt)
   und prueft, dass `arch_check.py` die Verletzung
   tatsaechlich meldet (statt false-clean zu sein).
   Pattern: Use a temp-dir + monkeypatch
   `sys.path`/`arch_check`-Bucket-Filter.

8. **EDIT `pyproject.toml`** (C3): `[tool.mypy] strict_bytes
   = true` aktiviert; Repo-Sweep `make typecheck` cache-
   frei gruen.

9. **EDIT `tests/integration/compose.yml`** (C3): Header-
   Kommentar-Konsolidierung; Sibling-Liste mit Lizenz +
   Test-Pfad-Referenz pro Service (Mosquitto MQTT,
   pymodbus in-process, asyncua in-process, dnp3-outstation
   in-process, IedServer in-process unter 2c-Fallback);
   Volume-/Healthcheck-Hygiene.

10. **Trigger-004-Re-Eval-Decision** (C3): MQTT-Publish-
    Throughput-Benchmark im Compose-Smoke; falls
    signifikanter Druck → NEU ADR 0036 (`canonical_json`-
    Alternative); sonst Trigger-Body-Notiz mit Defer auf
    M5/M6.

11. **`make fullbuild` cache-frei gruen** (C3):
    Welle-6a-Abschluss-Gate; alle 9 A-1-Gates ohne
    `CRITICAL_COV_TARGETS`-Override. Default-Liste final
    fuer alle 5 Adapter-Pakete.

12. **C4-Doc-Sync** (C4): `M4-welle-6a.md`-Status auf
    `Done`, `M4-protocol-adapters.md §3 Welle 6a` auf
    Done, Top-Level-Doku-Sync analog M4-Welle-5b-C3.

**Anti-Scope:**

- **Kein Welle-5b-Erbschaft-Hardening** — SPDX-Header-
  Konsistenz-Check, `arch_check.py`-Contract gegen GPL-
  Boundary-Crossing, CONTRIBUTING.md-Sync,
  IedServer-Smoke-Reaktivierung. Alle in Welle 6b.
- **Keine neuen Adapter-Implementer**. Welle 6a ist
  Cross-Pattern-Welle.
- **Keine ADR-Status-Wechsel** fuer ADR 0030..0035 (alle
  `Provisional` bis Welle 7). Welle-6a-C2 kann eine neue
  ADR 0036 `Proposed` einfuehren, falls OTel-Span-Wrap-
  Pattern eine ADR-relevante Sub-Decision erzeugt.
- **Keine Bewegung der Open-Trigger** ausserhalb 004/006.
- **Kein M4-DoD-Checkbox-Abhaken** in `roadmap.md` (Welle
  7 Sweep).
- **Kein Closure-Notiz**-Schreiben (Welle 7).

---

## 3. Architektur-Entscheidungen

Welle 6a bringt **moeglicherweise eine** neue ADR: **ADR
0036** (TracePort-Span-Lifecycle in DeviceProtocolPort-
Wrap), Status-Pfad `Proposed → Provisional → Accepted`
analog ADR 0024:

- **`Proposed`** mit C2-Implementation (falls die
  Implementation eine pattern-relevante Sub-Decision
  zeigt).
- **`Provisional`** mit C4-Doc-Sync.
- **`Accepted`** mit M4-Welle-7-Closure.

**Eventuell stattdessen:** Welle 6a-C2 nutzt ADR 0024 §4.5
direkt ohne neue ADR — `TracePort`-Span-Wrap ist bereits
in ADR 0024 §4.5 antizipiert; nur der konkrete `_protocol_
otel_wrap.py`-Wrapper braucht keinen eigenen ADR.

**Bezug:**

- [`spec/architecture.md §7`](../../../../spec/architecture.md#7-domain-modell-skizze)
  Z. 249 (`GG-AR-PORT-DRN-007` Driven-Ports-Tabelle —
  5 Adapter-Pakete vollstaendig).
- [`spec/lastenheft.md §16`](../../../../spec/lastenheft.md#16-kommunikationsschnittstellen)
  (`GG-MQTT-001` / `GG-MODB-001` / `GG-OPCUA-001` /
  `GG-DNP3-001` / `GG-IEC-001` Cluster — alle 5 SOLLTE-
  erfuellt mit Welle-2/3/4/5a/5b).
- [`../done/M4-welle-0.md`](M4-welle-0.md) §3
  Decision-Liste.
- [`../done/M4-welle-1.md`](M4-welle-1.md) §7
  (Folge-Pflicht-Liste — `AC-ADAPTER-LIGHTWEIGHT`-
  Planted-Violator-Property-Test).
- [`M4-protocol-adapters.md`](M4-protocol-adapters.md) §3
  Welle 6a (kanonische Slice-Spezifikation).
- [`../../adr/0024-observability-port-trio.md`](../../adr/0024-observability-port-trio.md)
  §4.5 (OTel-Span-Wrap-Pattern; Welle-6+-Forward-Pointer).
- [`../../adr/0030-device-protocol-port-surface.md`](../../adr/0030-device-protocol-port-surface.md)
  §2.1 (Sync-Vertrag) — bleibt unveraendert.
- [`../../adr/0031-mqtt-adapter-profile.md`](../../adr/0031-mqtt-adapter-profile.md),
  [`../../adr/0032-modbus-adapter-profile.md`](../../adr/0032-modbus-adapter-profile.md),
  [`../../adr/0033-opcua-adapter-profile.md`](../../adr/0033-opcua-adapter-profile.md),
  [`../../adr/0034-dnp3-adapter-profile.md`](../../adr/0034-dnp3-adapter-profile.md),
  [`../../adr/0035-iec61850-adapter-profile.md`](../../adr/0035-iec61850-adapter-profile.md):
  alle 5 Adapter-Profile als Profil-Index-Eintraege.
- [`../open/004-canonical-encoder-alternative-adr.md`](../open/004-canonical-encoder-alternative-adr.md),
  [`../done/006-mypy-strict-bytes.md`](006-mypy-strict-bytes.md):
  Trigger-Re-Eval-Pfade.

**Vorbelegungs-Liste fuer Welle 6b** (kommt parallel
oder nach 6a):

- SPDX-Header-Konsistenz-Check (`tools/check_refs.py` oder
  neues `tools/check_spdx.py`).
- NEU arch_check-Contract `AC-IEC61850-GPL-BOUNDARY`
  (20/20 Contracts).
- CONTRIBUTING.md mit Dual-License-Policy.
- IedServer-Smoke-Reaktivierungs-Probe (Library-Upgrade /
  Dockerfile-Python-Downgrade / Mock-only-Defer).

---

## 4. Liefer-Reihenfolge (5 Commits)

### C0 — `docs(plan)`: M4-welle-6a Slice-Doc (Welle-Beginn)

- Dieses Dokument als Welle-Start-Marker. Status:
  `In Progress`.
- Kein zusaetzlicher README-Sync noetig: Pre-C0a `30860ed`
  + Pre-C0b `d78a194` haben den Welle-5b-Move + Welle-6-
  Pre-C0-Status bereits in `in-progress/README.md` und
  `roadmap.md` verankert. C0-Slice-Doc-Eintrag in
  `in-progress/README.md` kommt nicht als eigener
  Bestand-Tabellen-Zeile (analog M4-Welle-1..5b).

### C1 — `docs(plan|spec)`: Adapter-Profil-Index + Architektur/Lastenheft-Sync

- NEU `spec/protocol_profiles/README.md` oder
  `spec/protocol_profiles.md` mit Profil-Index:
  - Tabelle: Adapter | ADR | Status | Lastenheft-ID |
    Welle | DoD-Verifikation-Pointer.
  - 5 Zeilen: MQTT/Modbus/OPC-UA/DNP3/IEC-61850.
  - Sub-Sections pro Adapter mit Datatype-Set, FC/
    Function-Code-Mapping, Async-Bridge-Wahl,
    Test-Sibling-Strategie (in 1-2 Saetzen pro Adapter).
- EDIT `spec/lastenheft.md §16-Implementierungs-Matrix:
  `🔲 M4` → `✅ M4` fuer 5 Cluster. Hinweis-Block ueber
  ADR-0035-Decision-I-f Lizenz-Boundary (GPLv3-Sub-Modul).
- EDIT `spec/architecture.md §8.2`: Adapter-Verortung mit
  Welle-1-ADR-Pfad; OTel-Span-Wrap-Pattern als Welle-6a-
  Konsequenz dokumentiert (referenziert ADR 0024 §4.5).
- `make docs-check` gruen.

### C2 — `feat(welle-6a)`: OTel-Span-Wrap fuer alle 5 protocol_*-Adapter

- NEU
  `src/grid_gym/adapters/driven/_protocol_otel_wrap.py`
  oder aequivalent: generischer Decorator/Wrapper.
  Architektur-Entscheidung in C2 (kann ggf. eine neue
  ADR 0036 `Proposed` triggern):
  - **Variante A**: Klassen-Decorator
    (`@_with_otel_span_wrap` auf `Iec61850DeviceProtocolPort`,
    etc.).
  - **Variante B**: Composition mit Wrapper-Adapter
    (`OtelSpanWrappedDeviceProtocolPort`).
  - **Variante C**: Hook im Welle-1-
    `build_protocol_ports`-Factory (TracePort wird
    injected, Adapter ruft selbst).
- EDIT alle 5 `protocol_*/__init__.py` oder `_port.py`:
  Adapter-Konstruktor akzeptiert optional ein `TracePort`
  (default `NullTracePort`); jeder `read()`/`write()`-Call
  wird in einen Span mit Standard-Attributen umschlossen.
- NEU 5+ Unit-Tests (1 pro Adapter): verifiziert dass
  jeder Read/Write einen Span mit
  `adapter_type/target/reference/operation/latency_ms`
  produziert.
- Eventuell NEU `docs/plan/adr/0036-protocol-otel-span-
  wrap.md` `Proposed` falls eine pattern-relevante
  Sub-Decision entsteht.
- `make test-unit` gruen.

### C3 — `feat(welle-6a)`: AC-ADAPTER-LIGHTWEIGHT-Property-Test + Trigger-006-Folge + compose.yml-Aufraeumung

- NEU
  `tests/unit/tools/test_arch_check_planted_violator.py`:
  Welle-1-§7-Folge-Pflicht. Test mit temp-dir +
  monkeypatch fuer `arch_check`-Bucket-Filter; Mock-
  Adapter mit absichtlicher Verletzung.
- EDIT `pyproject.toml`: `[tool.mypy] strict_bytes = true`
  (Trigger 006). Repo-Sweep: `make typecheck` gruen.
- EDIT `tests/integration/compose.yml`: Header-Kommentar-
  Konsolidierung; Sibling-Liste vereinheitlicht; Volume-/
  Healthcheck-Hygiene.
- Trigger-004-Re-Eval: MQTT-Publish-Throughput-Benchmark
  im Compose-Smoke; Entscheidung in Trigger-Body-Notiz
  oder NEU ADR 0036.
- `make fullbuild` cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override. Welle-6a-Gate erfuellt.

### C4 — `docs(plan|adr)`: Status/DoD-Sync + Top-Level-Doku-Sync

- `M4-welle-6a.md`-Status `In Progress → Done` mit C0/C1/
  C2/C3-Hashes + DoD-Verifikation-Block + DoD-Checkliste
  abgehakt.
- `M4-protocol-adapters.md §3 Welle 6a`: Done-Status mit
  Commit-Belegen; DoD-Checkboxen abgehakt.
- README.md / README.de.md / roadmap.md /
  adr/README.md / in-progress/README.md: M4-Status-Sync
  analog M4-Welle-5b-C3 `ca96bca`.
- Falls ADR 0036 entstanden: `Proposed → Provisional` mit
  C4-Merge-Beleg.
- Falls neuer arch_check-Contract `AC-ADAPTER-NO-TIME`
  entstanden: 19/19 → 20/20 Contracts KEPT.

---

## 5. Critical Files

| Pfad                                                                              | Commit | Aktion                                                |
| --------------------------------------------------------------------------------- | ------ | ----------------------------------------------------- |
| `docs/plan/planning/in-progress/M4-welle-6a.md`                                   | C0     | NEU (dieses Dokument)                                 |
| `spec/protocol_profiles.md` oder `spec/protocol_profiles/README.md`               | C1     | NEU (Adapter-Profil-Index)                            |
| `spec/lastenheft.md`                                                              | C1     | EDIT (§16-Implementierungs-Matrix-Sync)               |
| `spec/architecture.md`                                                            | C1     | EDIT (§8.2 Adapter-Verortung + OTel-Wrap-Pattern)     |
| `src/grid_gym/adapters/driven/_protocol_otel_wrap.py`                             | C2     | NEU (generischer Wrapper)                             |
| `src/grid_gym/adapters/driven/protocol_mqtt/__init__.py` o.a.                     | C2     | EDIT (TracePort-Hook + Span-Wrap)                     |
| `src/grid_gym/adapters/driven/protocol_modbus/__init__.py` o.a.                   | C2     | EDIT (TracePort-Hook + Span-Wrap)                     |
| `src/grid_gym/adapters/driven/protocol_opcua/__init__.py` o.a.                    | C2     | EDIT (TracePort-Hook + Span-Wrap)                     |
| `src/grid_gym/adapters/driven/protocol_dnp3/__init__.py` o.a.                     | C2     | EDIT (TracePort-Hook + Span-Wrap)                     |
| `src/grid_gym/adapters/driven/protocol_iec61850/__init__.py` o.a.                 | C2     | EDIT (TracePort-Hook + Span-Wrap; GPLv3-Sub-Modul)    |
| `tests/unit/adapters/driven/_protocol_otel_wrap/test_*`                           | C2     | NEU (Cross-Adapter-Span-Wrap-Tests)                   |
| `docs/plan/adr/0036-protocol-otel-span-wrap.md`                                   | C2/C4  | NEU `Proposed` falls pattern-relevant; `Provisional` mit C4 |
| `tests/unit/tools/test_arch_check_planted_violator.py`                            | C3     | NEU (Welle-1-§7-Folge)                                |
| `pyproject.toml`                                                                  | C3     | EDIT (`[tool.mypy] strict_bytes = true`; Trigger 006) |
| `tests/integration/compose.yml`                                                   | C3     | EDIT (Header-Konsolidierung + Sibling-Hygiene)        |
| `docs/plan/planning/open/004-canonical-encoder-alternative-adr.md`                | C3     | EDIT (Trigger-Body-Notiz oder Closure)                |
| `docs/plan/planning/done/006-mypy-strict-bytes.md`                                | C3     | EDIT (Closure-Notiz nach Aktivierung)                 |
| `docs/plan/planning/in-progress/M4-welle-6a.md`                                   | C4     | EDIT (Status → Done; DoD)                             |
| `docs/plan/planning/done/M4-protocol-adapters.md`                          | C4     | EDIT (§3 Welle 6a DoD-Checkboxen abgehakt)            |
| `README.md` + `README.de.md` + `docs/plan/planning/in-progress/roadmap.md` + `docs/plan/planning/in-progress/README.md` | C4 | EDIT (M4-Status-Sync — Welle 6a `Done`) |

---

## 6. Verifikationspfad

1. **C0 (Slice-Doc)**: `make docs-check` cache-frei gruen.
2. **C1 (Profil-Index + Spec-Sync)**: `make docs-check`
   gruen mit neuer Profil-Index-Datei + 5 ADR-Links.
3. **C2 (OTel-Span-Wrap)**:
   - `make test-unit` gruen (1541 → ~1555+ Tests; +5..10
     neue Cross-Adapter-Span-Wrap-Tests).
   - `make arch-check` 19/19 KEPT (oder 20/20 falls neuer
     Contract).
   - `make gates` cache-frei gruen ohne Override.
   - Eventuell ADR 0036 `Proposed` mit `make docs-check`
     gruen.
4. **C3 (Property-Test + Trigger 006 + compose.yml)**:
   - `make test-unit` gruen (1555 → ~1560+ Tests; +1
     Planted-Violator-Test).
   - `make typecheck` cache-frei gruen mit
     `--strict-bytes`.
   - `make fullbuild` cache-frei gruen ohne Override —
     **Welle-6a-Abschluss-Gate**.
5. **C4 (Doc-Sync)**: `make docs-check` gruen mit
   Welle-6a-Endstand in 5+ Docs.

---

## 7. Risiken

- **OTel-Span-Wrap-Architektur-Wahl (HOCH)** — Variante
  A (Class-Decorator) / Variante B (Composition-Wrapper) /
  Variante C (Welle-1-Factory-Hook) haben unterschiedliche
  Trade-offs. Variante C ist am architektur-saubersten (TracePort
  via DI), aber braucht Welle-1-Hook-Erweiterung; Variante
  A ist am pragmatischsten, aber verteilt Wrap-Logik in
  alle 5 Adapter-Module. *Mitigation*: C2-Implementation
  entscheidet basierend auf Code-Review beider Varianten;
  ggf. NEU ADR 0036 mit `Proposed`-Decision-Begruendung.
- **Trigger-006 `--strict-bytes`-Repo-Sweep-Aufwand
  (MEDIUM)** — `bytes`/`bytearray`-Type-Annotations sind
  in `protocol_modbus/_codec.py`, `protocol_dnp3/_codec.py`,
  `hexagon/core/scenario/codec.py` etc. verstreut.
  *Mitigation*: Re-Eval in M4-Welle-3-C3 war positiv;
  Sweep ist bounded.
- **Planted-Violator-Property-Test-Mechanik (MEDIUM)** —
  Tests mit temp-dir + monkeypatch sind brittle. Welle-3-
  Modbus hatte ein analoges Pattern; Pattern-Wiederverwendung.
- **`make fullbuild`-Cache-Sensitivitaet (LOW)** —
  Welle-6a-Abschluss-Gate ist `make fullbuild` cache-frei
  gruen. CRITICAL_COV_TARGETS final fuer 5 Adapter; aber
  Coverage-Drift moeglich nach OTel-Span-Wrap-Edits.
  *Mitigation*: C2-Tests verifizieren Coverage pro
  Wrapper-Branch.
- **Trigger-004-Benchmark-Verfaelschung (LOW)** —
  Compose-Smoke-Benchmark fuer MQTT-Publish-Throughput
  haengt von Mosquitto-Container-Stand, Host-Load, JIT
  ab. *Mitigation*: Benchmark als best-effort; Decision
  bleibt qualitativ (sigfificanter Druck ja/nein); Defer
  auf M5/M6 ist akzeptabel.

---

## 8. Wandert nach

- `done/M4-welle-6a.md` mit M4-Welle-6b-Pre-C0-Move
  (Pattern Welle 1..5b).
- Eventuell ADR 0036 bleibt in `docs/plan/adr/`.
- Eventuell `spec/protocol_profiles/README.md` (oder
  `.md`) bleibt in `spec/`.
- `M4-protocol-adapters.md` bleibt in `in-progress/` bis
  M4-Welle-7-Closure.
- M4-Welle-6b-Naechster-Schritt: IEC-61850-Lizenz-und-
  Smoke-Hardening (siehe `M4-protocol-adapters.md` §3
  Welle 6b).

---

## 9. DoD-Checkliste (mit C4 abzuhaken)

Pattern analog M4-welle-5b.md §9. Belege werden mit C4
**DoD-Verifikation**-Block im Status-Header oben + §4
Liefer-Reihenfolge fuer die per-Commit-Aktion ergaenzt.

**In-Scope-Items (mit C4 abzuhaken):**

- [x] **Adapter-Profil-Index** unter `spec/protocol_profiles/`
  mit 5 Adapter-Eintraegen + ADR-Links + Lastenheft-IDs.
- [x] **Lastenheft §16-Implementierungs-Matrix** auf
  `✅ M4` fuer 5 Cluster + GPLv3-Lizenz-Boundary-Hinweis.
- [x] **Architektur §8.2** Adapter-Verortung scharf mit
  Welle-1-ADR-Pfad + OTel-Span-Wrap-Pattern dokumentiert.
- [x] **OTel-Span-Wrap** fuer alle 5 `protocol_*`-Adapter
  produktiv via TracePort-Hook. Standard-Attribute
  (`adapter_type`/`target`/`reference`/`operation`/
  `latency_ms`).
- [x] **Cross-Adapter-Span-Wrap-Unit-Tests** — 5+ neue
  Tests (1 pro Adapter); jeder Read/Write produziert
  einen Span mit korrekten Attributen.
- [x] **NEU `tests/unit/tools/test_arch_check_planted_violator.py`**
  — Welle-1-§7-Folge-Pflicht eingezogen.
- [x] **`pyproject.toml` `[tool.mypy] strict_bytes = true`**
  aktiviert; `make typecheck` cache-frei gruen.
- [x] **EDIT `tests/integration/compose.yml`** Header-
  Konsolidierung + Sibling-Hygiene.
- [x] **Trigger 004 Re-Eval-Decision** entschieden (NEU
  ADR oder Defer-Notiz).
- [x] **Trigger 006 Closure** mit `--strict-bytes`-
  Aktivierung verlinkt aus `M4-welle-6a.md`.
- [x] **`make fullbuild` cache-frei gruen** ohne
  `CRITICAL_COV_TARGETS`-Override (Welle-6a-Abschluss-
  Gate).

**Anti-Scope-Items (mit C4 zu verifizieren):**

- [x] **Keine Welle-5b-Erbschaft-Items** — SPDX-Header-
  Konsistenz-Check, GPL-Boundary-Contract, CONTRIBUTING.md-
  Sync, IedServer-Smoke-Reaktivierung bleiben fuer
  Welle 6b.
- [x] **Kein neuer Adapter-Implementer** — verifiziert:
  keine neue Datei unter `adapters/driven/protocol_*/`
  (ausser dem `_protocol_otel_wrap.py`-Helper).
- [x] **Keine ADR-Status-Wechsel** fuer ADR 0030..0035 —
  alle bleiben `Provisional` bis Welle 7. Eventuelle ADR
  0036 ist `Proposed`/`Provisional`-zulaessig.
- [x] **Keine Bewegung der Open-Trigger** ausserhalb 004/006.
- [x] **Kein M4-DoD-Checkbox-Abhaken** in `roadmap.md` —
  Sweep mit Welle 7.
- [x] **Kein Closure-Notiz**-Schreiben (Welle 7).
