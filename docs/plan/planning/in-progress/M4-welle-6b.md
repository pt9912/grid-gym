# Welle 6b — M4 IEC-61850-Lizenz-und-Smoke-Hardening (Welle-5b-Erbschaft)

**Status:** In Progress — eroeffnet 2026-06-01 nach M4-
Welle-6a-Closure inkl. Slice 034 Review-Folge (Liefer-Stack
`838d904` Sub-Slicing + C0 `9776dd9` + C1 `9312239` + C2
`9d3912f` + Pre-C3 `81140e2` + C3 `0a5e895` + C4 `69b37f1` +
**Slice 034 `bde8fdb`** Review-Folge + Hash-Sync `b6a778d` +
**Self-Close-Move `d1cb65d`** + Pre-C0-Sync `7b0e3e4`).

Welle 6b ist die **achte Code-Welle** in M4 und die zweite
Cross-Adapter-Welle (analog Welle 6a). Sie ist die **erste
reine Welle-Erbschafts-Welle**: keine neuen
`DeviceProtocolPort`-Implementer und keine neuen Cross-
Adapter-Patterns, sondern die geziele Schaerfung der in
Welle 5b bewusst verschobenen Lizenz-/Distribution-/Smoke-
Folge-Pflichten + Slice-034-F13-Vorlauf-Item:

1. **SPDX-Header-Konsistenz-Check** (Welle-5b-Decision-I-f-
   Folge): alle Dateien unter `protocol_iec61850/*` muessen
   den `SPDX-License-Identifier: GPL-3.0-only`-Header
   tragen. Aktuell per Konvention; ohne automatischen Lint
   schleichen Dateien ohne Header rein.
2. **`AC-IEC61850-GPL-BOUNDARY` arch_check-Contract**
   (Welle-5b-Decision-I-f-Folge): kein Code unter
   `src/grid_gym/*` (ausser `protocol_iec61850/*`) darf
   `grid_gym.adapters.driven.protocol_iec61850.*` direkt
   importieren. Schuetzt MIT-Reinheit per Static-Check;
   ergaenzt 19 Contracts auf 20.
3. **CONTRIBUTING.md-Sync mit Dual-License-Policy**: NEUE
   `CONTRIBUTING.md` (oder bestehende Datei erweitern) mit
   Dual-License-Section. Default-Contribs sind MIT;
   `protocol_iec61850/*`-Aenderungen sind GPL-3.0-only und
   brauchen SPDX-Header.
4. **IedServer-Smoke-Reaktivierungs-Probe** (Welle-5b-2c-
   Mock-only-Fallback-Folge): die `IedServer`-In-Process-
   Tests sind via `pytest.mark.skip` deaktiviert wegen
   Python-3.14-SWIG-Segfault im `_pyiec61850.so`-Layer.
   Drei-Pfad-Probe:
   - **Pfad A**: `pyiec61850-ng`-Library-Upgrade pruefen.
   - **Pfad B**: Dockerfile-Python-Downgrade auf 3.12 fuer
     den IEC-Test-Stage (separater `iec61850-test`-Stage).
   - **Pfad C**: Mock-only-Fallback bleibt aktiv (Status
     quo), mit dokumentiertem Defer auf M5/M6.
5. **AC-ADAPTER-LIGHTWEIGHT-Coverage-Schaerfung** (Slice-
   034-F13-Vorlauf-Item): `_is_adapter_lightweight_path`
   in `tools/arch_check.py:1067-1090` erfasst Cross-
   Adapter-Helper-Pfade `src/grid_gym/adapters/driven/_
   protocol_*.py` NICHT (parts[4]-Filter braucht
   `protocol_`/`persistence_`-Praefix; Underscore-Prefix-
   Files fallen aus). Welle 6b zieht den Filter so weiter,
   dass `_protocol_*.py`-Files unter `adapters/driven/`
   ebenfalls unter AC-ADAPTER-LIGHTWEIGHT fallen — oder
   ein dediziertes Contract `AC-CROSS-ADAPTER-LIGHTWEIGHT`
   fuer diese Helper-Gruppe (TBD im Welle-6b-Probe-Run).

Welle 6b ist **erste echte Welle-Erbschafts-Welle**: alle
fuenf Items sind in Welle 5b bzw. Slice 034 als Folge-
Pflichten markiert worden, ohne neue Architektur-Decisions.
**Eventueller neuer ADR**: nur bei IedServer-Smoke-Pfad-B
(Dockerfile-Python-Downgrade fuer einen Test-Stage), falls
das ein bemerkenswerter Repo-Praezedenzfall ist. Pfad A und
Pfad C sind ohne ADR-Material.

**Liefer-Reihenfolge (geplant, 5 Commits + ggf. Smoke-
Reaktivierungs-Probe-Commit):**

- C0 (dieser Commit) — `docs(plan)`: M4-welle-6b Slice-Doc
  (Welle-Beginn).
- C1 — `feat(welle-6b)` oder `chore(tools)`: SPDX-Header-
  Konsistenz-Check (`tools/check_spdx.py` oder Erweiterung
  von `tools/check_refs.py`) + Lint-Integration in `make
  gates`.
- C2 — `feat(welle-6b)`: NEU `arch_check.py`-Contract
  `AC-IEC61850-GPL-BOUNDARY` (Contracts ergaenzt; 19 → 20).
- C3 — `feat(welle-6b)`: IedServer-Smoke-Reaktivierungs-
  Probe (Pfad A oder B; bei Fehlschlag → Pfad C mit
  dokumentiertem Defer); ggf. neuer Slice falls Probe
  umfangreich. Plus Slice-034-F13-Coverage-Schaerfung
  (`_is_adapter_lightweight_path` ueber `_protocol_*.py`-
  Cross-Adapter-Helper erweitert; Property-Test
  `tests/unit/test_arch_check_planted_violator.py`
  ergaenzt).
- C4 — `docs(plan|adr)`: Status/DoD-Sync + Top-Level-Doku-
  Sync (analog Welle-6a-C4-Pattern). Plus CONTRIBUTING.md-
  Sync mit Dual-License-Policy.

---

## 1. Context

M4-Welle-5b hat den fuenften und letzten konkreten
`DeviceProtocolPort`-Implementer produktiv geliefert
(`Iec61850DeviceProtocolPort`, ADR 0035 `Provisional` +
Slice-033-Schaerfung). Decision I-f (GPL-Boundary) ist
**konzeptionell etabliert** — jede Datei unter
`protocol_iec61850/*` traegt einen
`SPDX-License-Identifier: GPL-3.0-only`-Header; der MIT-
Rest des Repos importiert nicht statisch in das GPL-
Modul. Aber: dieser GPL-Boundary ist aktuell **Konvention**,
nicht **enforced**. Welle 6b haertet ihn auf statische
Pruefung um:

- **SPDX-Header-Check** verifiziert die Konvention pro
  Datei.
- **`AC-IEC61850-GPL-BOUNDARY` arch_check-Contract**
  verifiziert die Konvention pro Import.

M4-Welle-5b hat ausserdem die **2c-Mock-only-Fallback**-
Entscheidung fuer den IedServer-In-Process-Smoke
getroffen, weil Python 3.14 SWIG-Segfault produzierte.
Probe-Run auf Python 3.12 hat MMSClient↔IedServer-
Roundtrip mit der `simpleIO.cfg`-Fixture verifiziert.
Welle 6b versucht die Reaktivierung via Library-Upgrade
oder Dockerfile-Python-Downgrade.

**Slice-034-F13-Vorlauf-Item:**
`_is_adapter_lightweight_path` in `tools/arch_check.py`
(M4-Welle-1) hat einen Pfad-Filter, der die Cross-Adapter-
Helper unter `src/grid_gym/adapters/driven/_protocol_*.py`
(`_protocol_otel_wrap.py` aus Welle 6a) nicht erfasst:
`parts[4]` muss mit `protocol_`/`persistence_` starten,
und Underscore-Prefix-Files fallen aus. Welle 6b zieht
den Filter so weiter, dass Cross-Adapter-Helper unter
`adapters/driven/` auch unter dem AC-ADAPTER-LIGHTWEIGHT-
Komplexitaets-Gate fallen.

## 2. Scope

Welle 6b liefert **fuenf Scope-Items** ueber 4-5 Commits:

1. **SPDX-Header-Konsistenz-Check** — `tools/check_spdx.py`
   (oder Erweiterung von `tools/check_refs.py`)
   verifiziert, dass alle Dateien unter
   `src/grid_gym/adapters/driven/protocol_iec61850/`,
   `tests/unit/adapters/driven/protocol_iec61850/`,
   `tests/integration/test_iec61850_*.py` und
   `tests/integration/fixtures/iec61850/` einen
   `SPDX-License-Identifier: GPL-3.0-only`-Header tragen.
   Lint-Failure bei fehlendem Header; in `make gates`
   eingebunden.

2. **`AC-IEC61850-GPL-BOUNDARY` arch_check-Contract** —
   neuer Contract in `tools/arch_check.py`: kein Code
   unter `src/grid_gym/` (ausser `protocol_iec61850/*`)
   darf `grid_gym.adapters.driven.protocol_iec61850.*`
   direkt importieren. 19/19 → 20/20 Contracts KEPT.

3. **CONTRIBUTING.md-Sync mit Dual-License-Policy** —
   NEU `CONTRIBUTING.md` (oder bestehende Datei erweitert)
   mit Dual-License-Section: Default-Contribs sind MIT;
   Aenderungen unter `protocol_iec61850/*` sind GPL-3.0-
   only und brauchen SPDX-Header. Pattern-Praezedenz:
   ffmpeg-Python-Wrapper, GTK-Bindings.

4. **IedServer-Smoke-Reaktivierungs-Probe** — Drei-Pfad-
   Vorgehen mit Timebox:
   - **Pfad A** (~30 min): `pyiec61850-ng`-Library-Upgrade
     pruefen (PyPI-Stand 2026-XX gegen 1.6.1.2; neuere
     Wheels mit Python-3.14-Support?).
   - **Pfad B** (~60 min): Dockerfile-Python-Downgrade auf
     3.12 fuer den IEC-Test-Stage (separater
     `iec61850-test`-Stage statt Default-3.14).
   - **Pfad C** (Fallback): Mock-only-Fallback bleibt
     aktiv; Welle 6b dokumentiert das als Defer auf M5/M6
     mit konkretem Trigger (z. B. pyiec61850-ng-2.0-
     Release mit Python-3.14-Support).
   - Entscheidung im C3-Probe-Run; `pytest.mark.skip` in
     `test_iec61850_in_process_smoke.py` aufheben bei
     Erfolg.

5. **AC-ADAPTER-LIGHTWEIGHT-Coverage-Schaerfung** (Slice-
   034-F13) — `_is_adapter_lightweight_path` so weiter-
   gezogen, dass Cross-Adapter-Helper-Pfade
   `src/grid_gym/adapters/driven/_protocol_*.py`
   (Underscore-Prefix-Files direkt unter `driven/`,
   keine Subdir) ebenfalls erfasst werden. Plus
   Planted-Violator-Test-Erweiterung
   (`tests/unit/test_arch_check_planted_violator.py`)
   um einen positiven Test fuer einen complexity-high
   `_protocol_*.py`-File. Alternative: dediziertes
   Contract `AC-CROSS-ADAPTER-LIGHTWEIGHT` — Entscheidung
   im Welle-6b-C3-Probe-Run abhaengig von der konkreten
   Implementier-Komplexitaet.

## 3. Anti-Scope

- **Kein neuer `DeviceProtocolPort`-Implementer.** Welle
  6b ist Cross-Adapter-Welle wie Welle 6a.
- **Keine Aenderung der Adapter-Module** `protocol_mqtt`,
  `protocol_modbus`, `protocol_opcua`, `protocol_dnp3`.
  Welle-6b-Schaerfungen sind alle IEC-61850-spezifisch.
- **Keine Aenderung der OTel-Wrap-Implementation** aus
  Welle 6a (`_protocol_otel_wrap.py` bleibt unveraendert).
- **Keine ADR-Status-Wechsel** (ADR 0024 bleibt
  `Accepted`; ADR 0030..0035 bleiben Status quo). Pfad-
  B-Probe (Dockerfile-Python-Downgrade) koennte ggf. ein
  NEUER ADR 0036 oder eine Aktualisierung von ADR 0035
  rechtfertigen — Entscheidung im C3-Probe-Run.
- **Kein Trigger-006-Re-Touch.** `strict_bytes = true`
  bleibt aktiv aus Welle-6a-C3.
- **Kein M4-Welle-7-Closure-Material** (DoD-Checkboxen,
  M4-results.md, ADRs auf `Accepted`).
- **Keine `noqa`-Marker** (Slice 027 Compliance).

## 4. Liefer-Reihenfolge

### C0 — `docs(plan): M4-welle-6b Slice-Doc (Welle-Beginn)`

**Diff:** dieses Dokument.

### C1 — `feat(welle-6b)`: SPDX-Header-Konsistenz-Check

**Diff:**
- NEU `tools/check_spdx.py` (oder Erweiterung von
  `tools/check_refs.py`) mit Pattern-Match auf
  `SPDX-License-Identifier:`-Marker.
- `Makefile` — neue `spdx-check`-Stage oder Integration in
  bestehende `docs-check`/`arch-check`.
- `make gates` — Aufnahme des Checks.

### C2 — `feat(welle-6b)`: `AC-IEC61850-GPL-BOUNDARY`-Contract

**Diff:**
- `tools/arch_check.py` — NEU Contract-Implementation
  `_check_iec61850_gpl_boundary`; AST-Import-Scan ueber
  `src/grid_gym/**/*.py` (ausser `protocol_iec61850/*`).
- Tests in `tests/unit/test_arch_check_planted_violator.py`
  oder eigene Test-Datei.

### C3 — `feat(welle-6b)`: IedServer-Smoke-Probe + F13-Coverage

**Diff (Smoke-Pfad):**
- **Pfad A:** `pyproject.toml` — `pyiec61850-ng`-Pin-Update.
- **Pfad B:** `Dockerfile` — neuer `iec61850-test`-Stage
  mit Python 3.12. Plus `tests/integration/compose.yml`-
  Anpassungen falls noetig.
- **Pfad C:** Reine Doku-Aenderung in
  `tests/integration/test_iec61850_in_process_smoke.py`-
  Skip-Begruendung + `M4-welle-6b.md`-Defer-Section.

**Diff (F13-Pfad):**
- `tools/arch_check.py` — `_is_adapter_lightweight_path`-
  Erweiterung um `_protocol_*.py`-Pfade unter
  `adapters/driven/`.
- `tests/unit/test_arch_check_planted_violator.py` — neuer
  positiver Test fuer `_protocol_*`-Cross-Adapter-Helper.

### C4 — `docs(plan|adr)`: Status/DoD-Sync + Top-Level-Doku-Sync

**Diff:**
- `M4-welle-6b.md` Status `In Progress` → `Done` mit
  Liefer-Hashes.
- `M4-protocol-adapters.md §3 Welle 6b` — DoD-Checkboxen
  abgehakt.
- `docs/plan/planning/in-progress/README.md` —
  Welle-6b-Bestand-Eintrag aktualisiert (Done) +
  Naechster-aktiver-Schritt auf M4-Welle-7.
- `docs/plan/planning/in-progress/roadmap.md` —
  Welle-6b-Bullet + Tests-Count + Naechster-Schritt.
- `README.md` + `README.de.md` — Wave-6b-Tabellen-Zeilen
  auf Done.
- NEU oder erweiterte `CONTRIBUTING.md` mit Dual-License-
  Policy.

## 5. Critical Files

| Datei                                                                              | Phase  | Aktion                                                |
| ---------------------------------------------------------------------------------- | ------ | ----------------------------------------------------- |
| `docs/plan/planning/in-progress/M4-welle-6b.md`                                    | C0     | CREATE (dieses Dokument)                              |
| `tools/check_spdx.py` (neu) oder `tools/check_refs.py`                             | C1     | CREATE / EXTEND (SPDX-Header-Lint)                    |
| `Makefile`                                                                         | C1     | EDIT (`spdx-check`-Stage)                             |
| `tools/arch_check.py`                                                              | C2     | EDIT (`AC-IEC61850-GPL-BOUNDARY`-Contract)            |
| `tests/unit/test_arch_check_*.py`                                                  | C2/C3  | EDIT (neue Property-Tests)                            |
| `pyproject.toml` (Pfad A) **oder** `Dockerfile` (Pfad B) **oder** test-skip (Pfad C) | C3   | EDIT (IedServer-Smoke-Reaktivierungs-Pfad)            |
| `tools/arch_check.py`                                                              | C3     | EDIT (Slice-034-F13 `_is_adapter_lightweight_path`)   |
| `CONTRIBUTING.md`                                                                  | C4     | CREATE / EDIT (Dual-License-Policy)                   |
| `docs/plan/planning/in-progress/M4-protocol-adapters.md`                           | C4     | EDIT (§3 Welle 6b DoD-Checkboxen)                     |
| `docs/plan/planning/in-progress/README.md`                                         | C4     | EDIT (Welle-6b-Status + Naechster-Schritt)            |
| `docs/plan/planning/in-progress/roadmap.md`                                        | C4     | EDIT (Welle-6b-Bullet + Tests-Count)                  |
| `README.md` + `README.de.md`                                                       | C4     | EDIT (Wave-6b-Status)                                 |

## 6. Verifikationspfad

**Welle-6b-DoD:**

1. `make spdx-check` (NEU oder Teil von `docs-check`/
   `arch-check`) gruen mit allen IEC-61850-Dateien mit
   SPDX-Header.
2. `make arch-check` 20/20 Contracts KEPT (neu:
   `AC-IEC61850-GPL-BOUNDARY`; plus ggf.
   Erweiterung von `AC-ADAPTER-LIGHTWEIGHT` fuer
   Cross-Adapter-Helper).
3. `make test-unit` gruen mit neuen Property-Tests fuer
   `AC-IEC61850-GPL-BOUNDARY` + ggf. Slice-034-F13-Test.
4. `make test-integration` — entweder mit reaktivierten
   IedServer-Smokes (Pfad A oder B) oder mit
   unveraendertem Skip-Count + dokumentiertem Defer
   (Pfad C).
5. `make gates` cache-frei gruen ohne `CRITICAL_COV_
   TARGETS`-Override (alle A-1-Gates plus neuer
   `spdx-check`).
6. `CONTRIBUTING.md` mit Dual-License-Section produktiv.
7. `M4-welle-6b.md` Status `Done` + Liefer-Hashes.

**Welle-6b-Gate:** `make gates` cache-frei gruen mit
20/20 Contracts + SPDX-Header-Lint integriert + entweder
Integration-Smoke reaktiviert oder Mock-only-Fallback
explizit als M5/M6-Defer dokumentiert.

## 7. Risiken

- **Pfad-B-Probe-Komplexitaet:** Dockerfile-Python-
  Downgrade fuer einen einzelnen Test-Stage kann komplex
  werden (zweite Python-Version im Build-Layer, separates
  uv-Lockfile-Handling). Falls C3 zu gross wird, Slice-
  Out in einen separaten `035-iec61850-smoke-pfadb-...`-
  Slice (Pattern wie Welle-5b-C1-Review-Folge `da8aed9`).
- **Library-Upgrade-Pfad-A-Stale:** PyPI-`pyiec61850-ng`
  hat seit Welle 5b ggf. keine neue Version mit Python-
  3.14-Support gepublished. Wahrscheinlich landen wir
  bei Pfad C — dann muss der Defer-Trigger sauber
  dokumentiert sein (M5/M6-Trigger-Doc unter `open/`).
- **SPDX-Header-Lint-Coverage:** falls Welle 5b
  versehentlich Dateien ohne Header committet hat,
  produziert C1 ein Lint-Failure beim ersten Lauf.
  Pre-C1-Check: `grep -rL "SPDX-License-Identifier"
  src/grid_gym/adapters/driven/protocol_iec61850/`
  vor C1-Implementation.
- **`AC-IEC61850-GPL-BOUNDARY`-Contract-Implementation:**
  AST-Import-Scan ueber gesamten Repo (ausser dem
  GPL-Modul) ist potenziell teuer. Falls C2 zu langsam
  wird (>1s on CI), Cache-Mechanismus oder selektive
  Iteration noetig.
- **Slice-034-F13-Implementation:** entweder
  `_is_adapter_lightweight_path`-Erweiterung (einfacher,
  reuse existierender Logik) oder neues
  `AC-CROSS-ADAPTER-LIGHTWEIGHT`-Contract (saubere
  Trennung). Entscheidung im C3-Probe-Run.

## 8. Wandert nach

- Bei C4-Closure: Welle-6b-Doc bleibt vorerst in
  `in-progress/`; Self-Close-Move nach `done/` folgt im
  Pre-C0-Sync vor Welle 7 (Pattern Welle 1..5b/6a).
- M4-Welle-7 (Closure): ADR 0030..0035 → `Accepted`;
  M4-results.md unter `done/`; Roadmap-M4-DoD-Checkboxen-
  Sweep.

## 9. DoD-Checkliste (mit C4 abzuhaken)

- [ ] **SPDX-Header-Konsistenz-Check produktiv** —
  `tools/check_spdx.py` oder Erweiterung; in `make gates`
  integriert; alle IEC-61850-Dateien Lint-clean.
- [ ] **`AC-IEC61850-GPL-BOUNDARY`-Contract produktiv** —
  20/20 Contracts KEPT; Property-Test fuer Negativ-Pfad
  (file outside `protocol_iec61850/*` importiert es) und
  Positiv-Pfad (file in `protocol_iec61850/*` darf
  importieren).
- [ ] **CONTRIBUTING.md mit Dual-License-Policy
  produktiv** — Default-MIT + GPL-3.0-only-Subset
  `protocol_iec61850/*` + SPDX-Header-Pflicht.
- [ ] **IedServer-Smoke-Reaktivierungs-Decision** — eine
  von drei Optionen verfolgt (Pfad A oder B
  produktiviert; Pfad C als dokumentierter Defer auf
  M5/M6 mit konkretem Trigger).
- [ ] **Slice-034-F13-Coverage-Schaerfung** —
  `_is_adapter_lightweight_path` (oder NEU
  `AC-CROSS-ADAPTER-LIGHTWEIGHT`) deckt Cross-Adapter-
  Helper unter `_protocol_*.py` ab; Planted-Violator-
  Test erweitert.
- [ ] **`make test-unit` gruen** — Welle-6b-Endstand,
  Test-Count festgehalten.
- [ ] **`make test-integration` gruen** mit reaktivierten
  Smokes ODER unveraendertem Skip-Count + dokumentiertem
  Defer.
- [ ] **`make arch-check` 20/20 KEPT** (Welle-6b-neuer
  Contract).
- [ ] **`make gates` cache-frei gruen** ohne
  `CRITICAL_COV_TARGETS`-Override.
- [ ] **`make docs-check` cache-frei gruen**.
- [ ] **C4-Doc-Sync produktiv** — `M4-welle-6b.md`
  Status `Done`, `M4-protocol-adapters.md §3 Welle 6b`
  DoD-Checkboxen abgehakt, Top-Level-Doku-Sync
  (in-progress/README.md, roadmap.md, README(s)).
- [ ] **Welle-7-Naechster-Schritt verankert** — M4-Welle-
  7-Closure-Pflichten in `in-progress/README.md` als
  naechster aktiver Schritt sichtbar.

**Anti-Scope-Verifikation (Welle-6b NICHT):**

- [ ] Keine Aenderungen in `protocol_mqtt`/`protocol_
  modbus`/`protocol_opcua`/`protocol_dnp3`.
- [ ] Keine Aenderung der OTel-Wrap-Implementation aus
  Welle 6a.
- [ ] Keine ADR-Status-Wechsel (es sei denn Pfad-B-Probe
  rechtfertigt ein neues ADR — Entscheidung im C3-
  Probe-Run dokumentiert).
- [ ] Kein `make fullbuild`-Lauf als C4-Pflicht (analog
  Welle-6a-Pattern: `make gates` reicht; `fullbuild`
  ist Welle-7-Closure-Pflicht).

---

## References

- [`../done/M4-welle-5b.md`](../done/M4-welle-5b.md) —
  Welle-5b-Closure mit Decision-I-f-Lizenz-Boundary und
  2c-Mock-only-Fallback-Defer.
- [`../done/033-iec61850-adapter-review-folge.md`](../done/033-iec61850-adapter-review-folge.md)
  — Welle-5b-Review-Folge (15 Findings), Pattern fuer
  Slice-Doc-Struktur.
- [`../done/M4-welle-6a.md`](../done/M4-welle-6a.md) —
  Welle-6a-Closure (Cross-Adapter-Mainstream).
- [`../done/034-iec61850-otel-wrap-review-folge.md`](../done/034-iec61850-otel-wrap-review-folge.md)
  — Welle-6a-Review-Folge mit F13-Vorlauf-Item.
- [`M4-protocol-adapters.md`](M4-protocol-adapters.md) §3
  Welle 6b (kanonische Slice-Spezifikation).
- [`../../adr/0035-iec61850-adapter-profile.md`](../../adr/0035-iec61850-adapter-profile.md)
  — IEC-61850-Adapter-Profile mit Decision I-f
  Lizenz-Boundary.
- [`../../adr/0030-device-protocol-port-surface.md`](../../adr/0030-device-protocol-port-surface.md)
  §2.4 — DeviceProtocolPort-Surface-Vertrag (wird in
  Welle 7 auf `Accepted` geschaerft).
