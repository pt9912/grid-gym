# Welle 7 — M4 Closure (1/2 Tag)

**Status:** In Progress — eroeffnet 2026-06-01 nach M4-
Welle-6b-Closure (Liefer-Stack `14d1bcb` C0 + `8947c62` C1
+ `9e2bf39` C2 + `2539574` C3 + `314ccae` C4 + Self-Close-
Move `bf23458` + Pre-C0-Sync `5b2dc24`).

Welle 7 ist die **neunte und letzte Welle** in M4 und die
**M4-Closure-Welle**. Pattern analog M3-Welle-7 (siehe
[`../done/M3-results.md`](../done/M3-results.md)): keine
neuen Code-Diffs, sondern (a) ADR-Status-Wechsel auf
`Accepted`, (b) Closure-Artefakte (`M4-results.md`),
(c) Roadmap-DoD-Sweep, (d) End-to-End-Sweep S-1..S-6,
(e) Self-Close-Moves der M4-Slice-Plan-Doku.

**Liefer-Reihenfolge (geplant, 4 Commits + Self-Close-
Moves):**

- C0 (dieser Commit) — `docs(plan): M4-welle-7 Slice-Doc`
  (Welle-Beginn).
- C1 — `docs(adr)`: 6 M4-ADRs von `Provisional` auf
  `Accepted` (ADR 0030/0031/0032/0033/0034/0035). Pro-ADR-
  Body-Verifikation: Decisions/Status alle konsistent mit
  Welle-Closure-Stand.
- C2 — `docs(plan)`: NEU `done/M4-results.md` mit Welle-
  Tabelle + Abnahme-Belegen + Pro-Welle-Reviews + S-1..S-6-
  Sweep-Dokumentation (Pattern analog
  [`../done/M3-results.md`](../done/M3-results.md)). Plus
  ADR-0028-Linkpflege.
- C3 — `docs(plan)`: M4-Closure-Top-Level-Sync —
  `roadmap.md §3 M4` DoD-Checkboxen abhaken, M4 auf
  `Done`, „Naechster aktiver Slice: M5" setzen; `README.md`/
  `README.de.md` Status-Header sync; `in-progress/README.md`
  „Aktive Welle"-Block auf M5 ausrichten; ggf. neue
  Open-Trigger fuer M4-Restposten.
- C4 — `chore(welle-7)`: Self-Close-Move
  `M4-protocol-adapters.md` und `M4-welle-7.md` nach
  `done/` (rename-only). Folge-Commit mit Cross-Doc-Refs.

---

## 1. Context

M4 hat ueber 9 Code-Wellen (0..6b) **alle 5
`DeviceProtocolPort`-Implementer** geliefert plus Cross-
Adapter-Hardening:

| Welle | Lieferung                                                                                   |
| ----- | ------------------------------------------------------------------------------------------- |
| 0     | Slice-Plan + Open-Trigger-Triage (Welle-Beginn).                                            |
| 1     | `DeviceProtocolPort`-Surface-Foundation (ADR 0030 Proposed → Provisional).                  |
| 2     | MQTT-Adapter (ADR 0031 Provisional; QoS-0/1, Mosquitto-Smoke).                              |
| 3     | Modbus-TCP-Adapter (ADR 0032 Provisional; 5 Datatypes, FC03/FC10).                          |
| 4     | OPC-UA-Adapter (ADR 0033 Provisional; **erster rein-async-Stack** im Repo).                 |
| 5a    | DNP3-Adapter (ADR 0034 Provisional; **Zwei-Library-Setup** `nfm-dnp3` + `dnp3-outstation`). |
| 5b    | IEC-61850-Adapter (ADR 0035 Provisional; **erstmaliger GPL-isolierter Sub-Module-Praezedenzfall** im Repo). |
| 6a    | Cross-Adapter-Hardening Mainstream (OTel-Span-Wrap fuer alle 5 Adapter via Composition-Wrapper; Adapter-Profil-Index; `AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-Test; `strict_bytes`-Aktivierung; Slice 034 Review-Folge mit 15 Findings). |
| 6b    | IEC-61850-Lizenz-und-Smoke-Hardening (Welle-5b-Erbschaft): SPDX-Header-Lint (`tools/check_spdx.py` + 10. A-1-Gate `make spdx-check`); `AC-IEC61850-GPL-BOUNDARY`-arch_check-Contract (14. Contract; 19 → 20); NEU `CONTRIBUTING.md` mit Dual-License-Policy; IedServer-Smoke-Reaktivierungs-Probe mit Pfad-C-Defer (Trigger 009); Slice-034-F13-Coverage-Schaerfung. |

**Endstand vor Welle 7:**

- 1584 Unit-Tests + 35 Integration passed + 4 skipped.
- 20/20 arch_check-Contracts KEPT (6 import-linter + 14
  arch_check).
- 10/10 A-1-Gates gruen ohne Override (`spdx-check` als
  neuer 10. Gate aus Welle 6b).
- `strict_bytes = true` produktiv (Trigger 006 closed).
- 6 M4-ADRs (0030..0035) alle in Status `Provisional` —
  Welle 7 zieht sie auf `Accepted`.

## 2. Scope

Welle 7 liefert **fuenf Closure-Items** ueber 4 Commits:

1. **ADR-Status-Wechsel (6 ADRs)** — alle M4-ADRs
   (0030/0031/0032/0033/0034/0035) von `Provisional` auf
   `Accepted`. Pro-ADR Body-Verifikation: Decisions sind
   alle final, Welle-Lieferung deckt sie produktiv,
   keine offenen Sub-Decisions. Plus Status-Header-Update
   im ADR-Header-Block. Pattern analog M3-Welle-7-
   C1.1..C1.6.

2. **NEU `done/M4-results.md`** — Closure-Artefakt mit:
   - Welle-Tabelle (9 Wellen 0..6b mit Liefer-Hashes +
     Test-Counts).
   - Abnahme-Belege (`make fullbuild`-Lauf, A-1-Gates,
     Contracts, Lastenheft-Coverage).
   - Pro-Welle-Reviews (zusammenfassende Bewertung pro
     Welle).
   - S-1..S-6-End-to-End-Sweep-Dokumentation.
   - M4-Wandert-Nach-Section (Welle-7-Erbschaft fuer M5+/
     M6+).
   - Pattern analog [`../done/M3-results.md`](../done/M3-results.md)
     §1-§7.

3. **Roadmap-M4-DoD-Sweep** — `roadmap.md §3 M4` DoD-
   Checkboxen-Sweep (7 Items abhaken); M4-Status-Header
   auf `Done`; „Naechster aktiver Slice: M5"-Setzung.

4. **Top-Level-Doku-Sync** — `README.md` / `README.de.md`
   / `in-progress/README.md` / Status-Headers auf
   M4-Done-Stand syncen.

5. **Self-Close-Moves + ADR-0028-Linkpflege** —
   `M4-protocol-adapters.md` nach `done/` (rename-only),
   plus Content-Sync (Cross-Doc-Refs). ADR-0028 (TickLoop-
   Private-Resume-Errors)-Bezug aktualisieren auf
   `planning/done/M4-protocol-adapters.md` falls noetig.

## 3. Anti-Scope (Welle 7 NICHT)

- **Kein Code-Diff** (keine Aenderungen in `src/grid_gym/`,
  `tools/`, `tests/`). Welle 7 ist reine Doku-/ADR-Welle.
- **Kein neuer Trigger** (Slice-034-F13-Vorlauf-Item wurde
  in Welle-6b-C3 produktiv eingezogen; weitere M4-Folge-
  Pflichten gibt es nicht).
- **Keine ADR-Status-Rueckwaertswechsel** (kein ADR von
  `Accepted` zurueck auf `Provisional`).
- **Kein M5-Slice-Plan-Material** (M5 ist Welle-0
  M5-Slice-Plan-Material; Welle 7 oeffnet das nicht).
- **Keine `noqa`-Marker** (Slice 027 Compliance).
- **Kein neues Contract** (`AC-IEC61850-GPL-BOUNDARY` aus
  Welle 6b ist das letzte arch_check-Contract dieser
  Welle).

## 4. Liefer-Reihenfolge

### C0 — `docs(plan): M4-welle-7 Slice-Doc` (Welle-Beginn)

**Diff:** dieses Dokument + `in-progress/README.md`-
Bestand-Eintrag.

### C1 — `docs(adr)`: 6 M4-ADRs auf `Accepted`

**Diff:**
- `docs/plan/adr/0030-device-protocol-port-surface.md` —
  Status `Provisional` → `Accepted`.
- `docs/plan/adr/0031-mqtt-adapter-profile.md` — Status
  `Provisional` → `Accepted`.
- `docs/plan/adr/0032-modbus-adapter-profile.md` — Status
  `Provisional` → `Accepted`.
- `docs/plan/adr/0033-opcua-adapter-profile.md` — Status
  `Provisional` → `Accepted`.
- `docs/plan/adr/0034-dnp3-adapter-profile.md` — Status
  `Provisional` → `Accepted`.
- `docs/plan/adr/0035-iec61850-adapter-profile.md` — Status
  `Provisional` → `Accepted`.

### C2 — `docs(plan)`: NEU `done/M4-results.md` + ADR-0028-Linkpflege

**Diff:**
- NEU `docs/plan/planning/done/M4-results.md` mit §1-§7
  analog `M3-results.md`.
- ADR 0028 (`tick-loop-private-error-import-contract.md`)
  „Bezug"-Section: Verweis auf
  `planning/in-progress/M4-protocol-adapters.md` ggf.
  nachziehen auf `planning/done/M4-protocol-adapters.md`
  (falls noetig nach C4-Self-Close-Move; alternativ in C4
  zusammen).

### C3 — `docs(plan)`: M4-Closure-Top-Level-Sync

**Diff:**
- `docs/plan/planning/in-progress/roadmap.md §3 M4`-
  DoD-Checkboxen-Sweep (alle 7 Items abhaken); M4-
  Status `Done`; „Naechster aktiver Slice: M5" setzen.
- `docs/plan/planning/in-progress/README.md` „Aktive
  Welle"-Block auf M5 ausrichten; M4-Bestand-Bereich
  abschliessend dokumentieren.
- `README.md` / `README.de.md` Status-Header + Wave-Welle-
  6b-Done-Confirmation; M4-Bestand-Liste abschliessend.

### C4 — `chore(welle-7)`: Self-Close-Move M4-protocol-adapters.md

**Diff:**
- `git mv docs/plan/planning/in-progress/M4-protocol-
  adapters.md docs/plan/planning/done/M4-protocol-
  adapters.md` (rename-only).
- Folge-Commit: Cross-Doc-Refs nach Move
  (alle Verweise in ADRs / Welle-Docs / READMEs / etc. auf
  `done/M4-protocol-adapters.md` umgelinkt).
- ggf. `M4-welle-7.md` selbst nach `done/` (oder bleibt
  in `in-progress/` analog Welle-6b-Pattern — Self-Close-
  Move folgt erst als M5-Welle-0-Pre-C0).

## 5. Critical Files

| Datei                                                       | Phase | Aktion                                                              |
| ----------------------------------------------------------- | ----- | ------------------------------------------------------------------- |
| `docs/plan/planning/in-progress/M4-welle-7.md`              | C0    | CREATE (dieses Dokument)                                            |
| `docs/plan/adr/0030-device-protocol-port-surface.md`        | C1    | EDIT (Status `Provisional → Accepted`)                              |
| `docs/plan/adr/0031-mqtt-adapter-profile.md`                | C1    | EDIT (Status `Provisional → Accepted`)                              |
| `docs/plan/adr/0032-modbus-adapter-profile.md`              | C1    | EDIT (Status `Provisional → Accepted`)                              |
| `docs/plan/adr/0033-opcua-adapter-profile.md`               | C1    | EDIT (Status `Provisional → Accepted`)                              |
| `docs/plan/adr/0034-dnp3-adapter-profile.md`                | C1    | EDIT (Status `Provisional → Accepted`)                              |
| `docs/plan/adr/0035-iec61850-adapter-profile.md`            | C1    | EDIT (Status `Provisional → Accepted`)                              |
| `docs/plan/planning/done/M4-results.md`                     | C2    | CREATE (analog `M3-results.md`)                                     |
| `docs/plan/adr/0028-tick-loop-private-error-import-contract.md` | C2/C4 | EDIT (Bezug-Linkpflege auf done/M4-protocol-adapters.md)        |
| `docs/plan/planning/in-progress/roadmap.md`                 | C3    | EDIT (M4-DoD-Checkboxen abgehakt; M4-Status `Done`)                 |
| `docs/plan/planning/in-progress/README.md`                  | C3    | EDIT (M5-Naechster-Schritt; M4-Bestand abschliessend)               |
| `README.md` + `README.de.md`                                | C3    | EDIT (Status-Header + Wave-Tabelle abschliessend)                   |
| `docs/plan/planning/in-progress/M4-protocol-adapters.md`    | C4    | MOVE → `done/` (rename-only, separater Commit)                      |

## 6. Verifikationspfad

**Welle-7-DoD:**

1. Alle 6 M4-ADRs (0030..0035) in Status `Accepted`.
2. `done/M4-results.md` produktiv mit Welle-Tabelle +
   Abnahme-Belegen + S-1..S-6-Sweep.
3. `roadmap.md §3 M4`-DoD-Checkboxen alle abgehakt; M4
   auf `Done`; M5 als naechster Slice gesetzt.
4. `make gates` cache-frei gruen am Welle-7-Closure-Hash.
5. `make fullbuild` cache-frei gruen am Welle-7-Closure-
   Hash (Welle-7-Closure-Gate; geht ueber `make gates`
   hinaus mit `image-audit` + `test-integration` +
   `openapi-validate`).
6. `make docs-check` cache-frei gruen.
7. `M4-protocol-adapters.md` nach `done/` gewandert
   (Self-Close-Move-Hash dokumentiert).

**Welle-7-End-to-End-Sweep (S-1..S-6, dokumentiert in
`done/M4-results.md §4`):**

- **S-1** — M4-Vorabraeumungs-Item: Welle-0-Trigger-
  Triage hat alle Open-Trigger geprueft; Welle-7-Sweep
  prueft die in M4 dazu-gekommenen Triggers (Trigger 009).
- **S-2** — Sub-Slicing-Schwelle eingehalten: alle Wellen
  haben ihren scope-Anti-Scope-Block gehalten;
  Welle 5 wurde sub-geslict in 5a/5b, Welle 6 in 6a/6b.
- **S-3** — Default-`make gates` ohne `CRITICAL_COV_
  TARGETS`-Override am Welle-7-Closure-Hash gruen
  (10 A-1-Gates).
- **S-4** — `make image-audit` cache-frei gruen
  (oder dokumentierter Defer-Pfad). Pruefung der Runtime-
  Image-Size nach M4-Adapter-Deps (`paho-mqtt`,
  `pymodbus`, `asyncua`, `nfm-dnp3`, `dnp3-outstation`,
  `pyiec61850-ng` als Optional-Extra).
- **S-5** — ADR-Erweiterungs-Pattern fortgefuehrt: 6 neue
  ADRs (0030/0031/0032/0033/0034/0035) ohne Supersedes-
  Pflicht (Schaerfung-ohne-Supersedes per ADR 0011-
  Pattern wo anwendbar).
- **S-6** — Lastenheft-Coverage-Sweep: alle 5 GG-*-001-
  Cluster-Items (`GG-MQTT-001`/`GG-MODB-001`/`GG-OPCUA-
  001`/`GG-DNP3-001`/`GG-IEC-001`) auf `✅ M4` (mit
  Slice-034-F15-Audit-Trail-Note). M5-Trigger fuer
  UI-Anbindung (`GG-UI-001..009`) existieren bereits.

**Welle-7-Closure-Gate:** `make fullbuild` cache-frei
gruen ohne `CRITICAL_COV_TARGETS`-Override am Welle-7-
Closure-Hash. Test-Bilanz: 1584 Unit + 35 Integration
passed + 4 skipped (IEC-Smokes weiterhin via 2c-Mock-
only-Fallback mit Trigger 009).

## 7. Risiken

- **`make fullbuild`-Lauf moeglicherweise rot:**
  `image-audit` ist die unbekannte Komponente — kann
  failen wenn Runtime-Image-Size durch Adapter-Deps die
  Schwelle ueberschreitet. Mitigation: falls rot →
  Trigger-Doc fuer Image-Pin-Optimierung + `make
  fullbuild`-Bypass mit dokumentierter Begruendung.
- **ADR-Body-Verifikation:** vor Status-Wechsel auf
  `Accepted` muss jedes ADR-Body konsistent mit Welle-
  Stand sein. Wenn ein ADR noch eine offene Decision-
  Markierung hat, muss die zuerst auf final gezogen
  werden (idealerweise war das in der jeweiligen Welle
  schon gemacht; sonst Welle-7-Folge-Slice).
- **`done/M4-results.md`-Skala:** das Dokument wird ca.
  300-500 Zeilen analog `M3-results.md`. Realistischer
  Aufwand C2-Commit.

## 8. Wandert nach

- Bei C4-Closure: `M4-protocol-adapters.md` nach `done/`
  (analog Welle-1..6b-Pattern). `M4-welle-7.md` selbst
  bleibt vorerst in `in-progress/` (Self-Close-Move
  folgt als M5-Welle-0-Pre-C0).
- M5 (UI + Demo): Welle 0 (Slice-Plan + Trigger-Triage)
  als naechster aktiver Slice.

## 9. DoD-Checkliste (mit C3/C4 abzuhaken)

- [ ] **6 M4-ADRs auf `Accepted`** — 0030/0031/0032/
  0033/0034/0035 (jedes ADR Body-verifiziert + Status-
  Header aktualisiert).
- [ ] **`done/M4-results.md` produktiv** mit Welle-
  Tabelle + Abnahme-Belegen + Pro-Welle-Reviews + S-1..
  S-6-Sweep + Wandert-Nach-Section.
- [ ] **`roadmap.md §3 M4`-DoD** alle 7 Checkboxen
  abgehakt; M4 auf `Done`; M5 als naechster aktiver
  Slice.
- [ ] **Top-Level-Doku-Sync produktiv** — `README.md`,
  `README.de.md`, `in-progress/README.md`,
  Status-Header.
- [ ] **`M4-protocol-adapters.md` nach `done/`
  gewandert** (Self-Close-Move-Hash dokumentiert in
  done/README.md + Pre-C0-Sync fuer Cross-Doc-Refs).
- [ ] **ADR-0028-Linkpflege** falls noetig.
- [ ] **`make gates` cache-frei gruen** am Welle-7-
  Closure-Hash.
- [ ] **`make fullbuild` cache-frei gruen** (Welle-7-
  Closure-Gate) oder dokumentierter Defer mit Trigger.
- [ ] **`make docs-check` cache-frei gruen**.
- [ ] **S-1..S-6-Sweep** in `M4-results.md §4` voll-
  staendig dokumentiert.

**Anti-Scope-Verifikation (Welle 7 NICHT):**

- [ ] Kein Code-Diff (kein `src/`, `tools/`, `tests/`-
  Touch).
- [ ] Keine ADR-Status-Rueckwaertswechsel.
- [ ] Keine `noqa`-Marker.
- [ ] Kein neues arch_check-Contract.
- [ ] Kein M5-Slice-Plan-Material in Welle-7-Closure.

---

## References

- [`../done/M3-results.md`](../done/M3-results.md) —
  M3-Closure-Pattern (Welle-Tabelle, Abnahme-Belege,
  S-1..S-6, Wandert-Nach).
- [`M4-protocol-adapters.md`](M4-protocol-adapters.md) §3
  Welle 7 (kanonische Slice-Spezifikation).
- [`../done/M4-welle-6b.md`](../done/M4-welle-6b.md) —
  Welle-6b-Closure (letzte Pre-Welle-7).
- [`../../adr/0030-device-protocol-port-surface.md`](../../adr/0030-device-protocol-port-surface.md)
  bis 0035 — 6 M4-ADRs.
- [`../../adr/0011-schaerfung-ohne-abloesung.md`](../../adr/0011-schaerfung-ohne-abloesung.md)
  — Pattern fuer ADR-Erweiterung ohne Supersedes (S-5).
