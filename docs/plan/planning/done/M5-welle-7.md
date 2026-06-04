# Welle 7 — M5 Closure (1/2 Tag)

**Status:** In Progress — eroeffnet 2026-06-04 mit C0
(dieser Commit). Welle 7 ist die **M5-Closure-Welle**;
Pattern analog M4-Welle-7 (siehe
[`M4-welle-7.md`](../done/M4-welle-7.md) + `M4-results.md`): keine
neuen Code-Diffs, sondern (a) ADR-Status-Wechsel auf
`Accepted`, (b) Closure-Artefakt (`M5-results.md`),
(c) Roadmap-DoD-Sweep + Top-Level-Doku-Sync,
(d) End-to-End-Sweep S-1..S-6, (e) Self-Close-Move der
M5-Slice-Plan-Doku.

**Pre-C0 — bereits erledigt** (Welle-6c-Closure-Stack):

- Welle-6c-C4a `c317200` (Self-Close-Move
  `M5-welle-6c.md → done/`, rename-only).
- Welle-6c-C4b `cfb9626` (Cross-Doc-Refs-Sync nach Move,
  5 Refs).

Welle 7 startet damit direkt mit C0 — der Welle-6c-
Closure-Stack ist der effektive Pre-C0.

**Liefer-Reihenfolge** (geplant, 4 Commits + Self-Close-
Move-Folge analog M4-Welle-7):

- **C0** (dieser Commit) — `docs(plan): M5-welle-7
  Slice-Doc` (Welle-Beginn).
- **C1** — `docs(adr)`: 5 M5-ADRs von `Provisional` auf
  `Accepted` (ADR 0036/0037/0038/0039/0040). Pro-ADR-
  Body-Verifikation: Decisions/Status alle konsistent
  mit Welle-Closure-Stand.
- **C2** — `docs(plan)`: NEU `done/M5-results.md` mit
  Welle-Tabelle + Abnahme-Belegen + Pro-Welle-Reviews
  + S-1..S-6-Sweep-Dokumentation (Pattern analog
  [`M4-results.md`](../done/M4-results.md) +
  [`M3-results.md`](../done/M3-results.md)). Plus
  ADR-0028-Linkpflege.
- **C3** — `docs(plan)`: M5-Closure-Top-Level-Sync —
  `roadmap.md §3 M5` DoD-Checkboxen abhaken + M5 auf
  `Done` + „Naechster aktiver Slice: M6"; `README.md`/
  `README.de.md` Status-Header sync; `in-progress/
  README.md` „Aktive Welle"-Block auf M6 ausrichten;
  ggf. neue Open-Trigger fuer M5-Restposten.
- **C4** — `chore(welle-7)`: Self-Close-Move
  `M5-ui-demo.md` UND `M5-welle-7.md` nach `done/`
  (rename-only). Folge-Commit mit Cross-Doc-Refs.

---

## 1. Context

M5 hat ueber 10 Wellen 0..6c (davon 9 Code-/Doku-Wellen
1..6c; Welle 0 ist Doku-Vorabraeumung analog M4-Welle-7)
**die volle UI- + Demo-Schicht** geliefert plus 9 neue
HTTP-/WS-Endpunkte, 7 UI-Pages, 5 ADRs:

| Welle | Lieferung                                                                                   |
| ----- | ------------------------------------------------------------------------------------------- |
| 0     | Slice-Plan + Open-Trigger-Triage (Welle-Beginn 2026-06-01); ADR 0036 `Proposed`.            |
| 1     | HTTP-API-Surface (5 REST + 1 WS, 4 neue Module mit AC-NO-GOD-UTILS-Split); ADRs 0036+0037 `Provisional`. |
| 2     | UI-Foundation (Layout + 6 Templates + HTMX 2.0.9 + Chart.js 4.5.1 + Jinja2-Factory).        |
| 3     | Live-Telemetry-Dashboard (WS-Subscribe + `TelemetryStreamPort`); ADR 0038 `Provisional`.    |
| 4a    | Replay-Controls + TickLoop-Wiring + RunStatus-Lifecycle; ADR 0039 `Provisional`.            |
| 4b    | Alarm-Aggregation + `AlarmStreamPort` + 6-Spalten-Alarm-Tabelle; ADR 0040 `Provisional`.    |
| 5     | Demo-Pipeline + YAML-Scenario-Loader (`gg-demo.yaml`); `make demo` + Welle-5-Lifespan-Branch. |
| 6a    | Fault-Flow (UI-Form-Validation + YAML-Fault-Demo); Welle-6-Sub-Slicing-Beschluss 6a/6b/6c.  |
| 6b    | UI-Visualization (Devices-Tabelle + System-Dashboard); NEU `routes_visualization.py` + 4 Templates. |
| 6c    | Abnahmedoku (`GG-DEMO-008`); pure Doku-Slice unter `docs/user/gg-demo-008-abnahme.md`.       |

**Endstand vor Welle 7 (2026-06-04):**

- **1722 Unit-Tests** + **80 Integration-Tests** passed +
  4 skipped (IEC-61850-2c-Mock-only-Fallback).
- **20/20 arch_check-Contracts** KEPT (6 import-linter +
  14 arch_check).
- **10/10 A-1-Gates** gruen cache-frei ohne Override.
- **5 M5-ADRs** (0036..0040) alle in Status `Provisional`
  — Welle 7 zieht sie auf `Accepted`.
- **9 HTTP-/WS-Endpunkte produktiv** (`POST /runs`,
  `GET /runs/{id}` + `/status` + `/snapshot` + `/devices/
  state` + `/alarms-history`, `POST /runs/{id}/control` +
  `/faults`, `WS /runs/{id}/telemetry` + `/alarms-stream`).
- **7 UI-Pages produktiv** (`/`, `/ui/health`, `/runs/{id}/
  dashboard` + `/control` + `/alarms` + `/faults` +
  `/devices` + `/system`).

**Lastenheft-Coverage (M5-Scope):**

- `GG-API-001..004` (4 MUSS) ✓.
- `GG-UI-001..005 + 009` (6 MUSS) ✓.
- `GG-UI-006..008` (3 SOLLTE) ✓.
- `GG-DEMO-001..008` (8 IDs; alle erfuellt, davon 5 MUSS
  `001..005` + 3 SOLLTE `006..008`) ✓.

---

## 2. Scope

Welle 7 liefert **fuenf Closure-Items** ueber 4 Commits:

1. **ADR-Status-Wechsel (5 ADRs)** — alle M5-ADRs
   (0036/0037/0038/0039/0040) von `Provisional` auf
   `Accepted`. Pro-ADR Body-Verifikation: Decisions sind
   alle final, Welle-Lieferung deckt sie produktiv, keine
   offenen Sub-Decisions. Plus **Status-Header +
   Status-Pfad-Body-Block** aktualisieren (Datum +
   M5-Welle-7-Closure-Referenz). Pattern analog
   M4-Welle-7-C1.

2. **NEU `done/M5-results.md`** — Closure-Artefakt mit:
   - §1 Welle-Tabelle (10 Wellen 0..6c mit Closure-Hash +
     Lastenheft-Coverage + Status).
   - §2 Pro-Welle-Reviews (Welle-4b 15 Findings + Welle-5
     15 Findings + Welle-6a 15 Findings + Welle-6b 15
     Findings; Welle-6c kein Review noetig).
   - §3 Abnahme-Belege (Lastenheft-Anforderung →
     produzierende Welle + Test/Doku).
   - §4 End-to-End-Sweep S-1..S-6 mit Verifikation.
   - §5 Wandert-Nach (M6-Erbschaft, neue Open-Trigger).
   - §6 ADR-Decision-Sweep (5 ADRs auf `Accepted`).

3. **`roadmap.md §3 M5` DoD-Sweep** — die 4 DoD-Checkboxen
   in `roadmap.md §3 M5` auf `[x]`; M5 auf `Done`;
   „Naechster aktiver Slice: M6".

4. **Top-Level-Doku-Sync** — `README.md` + `README.de.md`
   Status-Header auf „M5 Done"; `in-progress/README.md`
   „Aktive Welle"-Block auf M6 ausrichten;
   `AGENTS.md` Welle-Pointer (falls vorhanden).

5. **Self-Close-Move `M5-ui-demo.md` + `M5-welle-7.md`** —
   beide Doks gehen nach `done/`. C4-Folge mit Cross-Doc-
   Refs-Sync.

---

## 3. Architektur-Entscheidungen

**Keine neuen Decisions in Welle 7.** Welle 7 ist Closure-
Welle; alle architektonischen Entscheidungen sind in
Welle 0..6c verankert. Welle 7 stellt die bestehenden
5 ADRs auf `Accepted` und dokumentiert sie im
`M5-results.md`-Closure-Artefakt; keine Neuanlage, keine
Supersedes.

**ADR-Lifecycle-Wechsel** (C1; pure Status-Header-Edits +
Status-Pfad-Body-Block):

- **ADR 0036** (UI-Stack-Choice; FastAPI + HTMX + Jinja2 +
  Chart.js) — `Provisional → Accepted`. Welle 1..6b
  produktiv-belegt durch 9 HTTP-/WS-Endpunkte + 7 UI-
  Pages.
- **ADR 0037** (HTTP-API-Surface-Pattern; Replay-Controls
  via Action-Body, kein UICommandPort, GG-AR-PORT-DRG-002
  verworfen) — `Provisional → Accepted`. Welle 1+4a
  produktiv.
- **ADR 0038** (TelemetryStreamPort + WebSocket-Subscribe
  + Quality-Marker) — `Provisional → Accepted`. Welle 3
  produktiv (Dashboard + WS-Endpunkt + Demo-Generator).
- **ADR 0039** (Run-Control + Status-Tracking; RunStatus-
  Literal + `request(action)`-Konsolidierung +
  `TickLoopRegistry`) — `Provisional → Accepted`. Welle
  4a produktiv (Pause/Resume/Stop + Status-Polling).
- **ADR 0040** (Alarm-Aggregation + Stream-Port; Unified-
  `Alarm`-Domain-Type + Mapper-Familie + Ring-Buffer-
  History + WS-Stream) — `Provisional → Accepted`. Welle
  4b produktiv.

---

## 4. Liefer-Reihenfolge

Siehe Status-Header oben. Hier nur die C-Commit-Detail-
Specs:

### C0 — `docs(plan)`: M5-welle-7 Slice-Doc

**Dieser Commit.** Enthaelt:

- Slice-Doc [`M5-welle-7.md`](M5-welle-7.md) mit
  §1..§9-Struktur (Pattern analog M4-Welle-7).
- Liefer-Reihenfolge (C0 → C1 → C2 → C3 → C4).
- DoD-Checkliste (initial leer; C3 hakt ab).

Keine ADR-Aenderung in C0. Keine Code-Aenderung.

### C1 — `docs(adr)`: 5 M5-ADRs von `Provisional` auf `Accepted`

Pro-ADR-Edit:

- **Status-Header-Zeile** (Z. 3-ish): `**Status:**
  Provisional ... → **Status:** Accepted — M5-Welle-7-
  Closure 2026-06-XX. Provisional gezogen XYZ mit
  M5-Welle-N-CN.`
- **Status-Pfad-Body-Block** (falls vorhanden in ADR
  0032/0033-Style): vom `Provisional`-Eintrag auf
  `Accepted (M5-Welle-7-Closure)` schließen.
- Pro-ADR-Body-Sanity-Check (keine offenen Decisions, kein
  TBD; Welle-Closure-Stand ist konsistent).

5 ADRs, ein Commit. Keine Inhalts-Aenderung ausser
Status.

### C2 — `docs(plan)`: NEU `done/M5-results.md`

Closure-Artefakt mit den 6 Sektionen aus §2 oben. Pattern
analog `done/M4-results.md` + `done/M3-results.md`.
Optional Sub-Welle-Detail-Reviews-Referenzen (Welle-4b/5/
6a/6b Review-Folgen).

Plus ADR-0028-Linkpflege: wenn das `M5-results.md` neue
„Erbschafts"-Referenzen anlegt (z. B. Welle-6b
URL-Realization als M6-Forward-Pointer), sind die ADR-
Bezuege analog M4-Welle-7-Pattern zu pflegen.

### C3 — `docs(plan)`: M5-Closure-Top-Level-Sync

- `roadmap.md §3 M5` DoD-Checkboxen alle auf `[x]` setzen.
- `roadmap.md §3 M5` Status auf `Done`.
- `roadmap.md` Header-Zeile + §3 Block: „Aktiver Slice:
  M6 (Performance + Security + CI/CD)".
- `README.md` + `README.de.md` Status-Bullet `M5: Done`;
  Test-Counts + Test-Bilanz aktualisieren (sollte
  unveraendert bleiben — Welle 7 ist nur Doku).
- `in-progress/README.md` „Aktive Welle"-Block auf M6
  ausrichten; M5-Welle-Block in den Closure-Erbschafts-
  Block verschieben.
- `AGENTS.md` Welle-Pointer pruefen (falls existiert).

### C4 — `chore(welle-7)`: Self-Close-Move + Cross-Doc-Refs

Pflicht-Closure-Sequenz per
[`../README.md`](../README.md) Wave-Self-Close-Commit-
Konvention:

- **C4a** — `chore: git mv in-progress/M5-ui-demo.md →
  done/` UND `in-progress/M5-welle-7.md → done/`
  (rename-only, beide in einem Commit oder zwei separaten
  je nach Welle-7-Realisierungs-Note; Pattern analog
  M4-Welle-7-C4a `e745f10`).
- **C4b** — Cross-Doc-Refs-Sync nach Move; alle externen
  Refs auf `M5-ui-demo.md` und `M5-welle-7.md` umstellen.
  Pattern analog M4-Welle-7-C4b `72e8357`.

---

## 5. Critical Files

**Welle-7-NEU (geschrieben in C2):**

- `docs/plan/planning/done/M5-results.md`.

**Welle-7-MODIFY (in C1 + C3):**

- `docs/plan/adr/0036-ui-stack-choice.md` — Status auf
  Accepted (C1).
- `docs/plan/adr/0037-http-api-surface-pattern.md` —
  Status auf Accepted (C1).
- `docs/plan/adr/0038-telemetry-stream-port.md` — Status
  auf Accepted (C1).
- `docs/plan/adr/0039-run-control-and-status-tracking.md`
  — Status auf Accepted (C1).
- `docs/plan/adr/0040-alarm-aggregation-and-stream-port.md`
  — Status auf Accepted (C1).
- `docs/plan/planning/in-progress/roadmap.md` §3 M5
  DoD-Sweep + Active-Slice-Pointer (C3).
- `docs/plan/planning/in-progress/README.md` — Aktive-
  Welle-Block + Bestand-Tabelle (C3).
- `README.md` + `README.de.md` — Status-Header (C3).

**Welle-7-RENAME (in C4):**

- `M5-ui-demo.md` und `M5-welle-7.md` nach `done/`.

**Welle-7-UNBERUEHRT (kein Edit):**

- Aller Code (`src/`, `tests/`).
- `docs/user/*.md` (inkl. die Welle-6c-Abnahmedoku).
- Bestehende `done/M5-welle-*.md` Slice-Docs.

---

## 6. Verifikationspfad

**Welle-7-Gate:**

- `make gates` cache-frei gruen ohne Override (10 A-1-
  Gates am Welle-7-Closure-Hash). Test-Counts bleiben
  1722/80 (keine Test-Aenderung).
- `make docs-check` cache-frei gruen.
- `make fullbuild` cache-frei gruen ODER dokumentierter
  Defer-Pfad (krb5-CVE-Drift bleibt M4-Welle-7-Erbschaft;
  M5 macht keinen Base-Image-Bump).

**End-to-End-Sweep S-1..S-6** (in C2 dokumentiert):

- **S-1** M5-Vorabraeumungs-Item: Welle-0-Trigger-Triage
  + Welle-7-Sweep der in M5 dazu-gekommenen Trigger.
  Beleg: Welle-0-C2 `112efd3` + ggf. neue M5-Trigger.
- **S-2** Sub-Slicing-Schwelle eingehalten ueber Welle
  1..6c. Beleg: Welle-4 → 4a/4b + Welle-6 → 6a/6b/6c
  Tabelle.
- **S-3** Default-`make gates` ohne
  `CRITICAL_COV_TARGETS`-Override cache-frei gruen am
  Welle-7-Closure-Hash.
- **S-4** `make image-audit` cache-frei gruen ODER
  dokumentierter Defer-Pfad (krb5-CVE-Drift; M4-Welle-7-
  Erbschaft).
- **S-5** ADR-Erweiterungs-Pattern fortgefuehrt
  (5 neue M5-ADRs ohne Supersedes per ADR 0011; Soll-
  Wert war 1-3, Ist-Wert ist 5 — Begruendung im
  Closure-Artefakt: HTTP-API-Surface + Telemetry-Stream
  + Run-Control + Alarm-Aggregation sind alle separate
  Decision-Konzerne).
- **S-6** Lastenheft-Coverage-Sweep nach M5-Closure;
  M6-Trigger erstellen falls relevant.

**Abnahme-Verifikation (Lastenheft):**

- M5 erfuellt `GG-API-001..004` (4 MUSS) +
  `GG-UI-001..009` (6 MUSS + 3 SOLLTE) +
  `GG-DEMO-001..008` (8 IDs) ✓.

---

## 7. Risiken

**R1 — ADR-Status-Pfad-Konsistenz.** Beim Status-
Wechsel `Provisional → Accepted` muss der Status-Pfad-
Body-Block (falls vorhanden) konsistent sein. M3-/M4-
Pattern hat das pro ADR unterschiedlich gehandhabt; M5-
ADRs sind alle Welle-1+-Vorlagen mit demselben Pattern.
**Mitigation:** C1 macht pro ADR einen einzelnen
sauberen Edit; pre-flight grep ueber Status-Header +
Body-Block.

**R2 — `done/M5-results.md`-Drift gegen Sub-Welle-Docs.**
Closure-Artefakt referenziert konkrete Hashes + Test-
Counts aus 10 Wellen. Wenn ein Hash sich verschiebt
(z. B. Rebase), driftet die Tabelle.
**Mitigation:** Hashes werden zum Welle-7-C2-Zeitpunkt
gepinned; `done/`-Slice-Docs sind eingefroren (per
Self-Close-Move-Vertrag), Drift ist begrenzt.

**R3 — `make fullbuild`-krb5-CVE-Drift.** Pre-existing
M4-Erbschaft; bleibt rot bis Base-Image-Bump
(Trigger 010). M5 zieht keinen Bump.
**Mitigation:** C2-Doku verankert den Defer-Pfad analog
M4-Welle-7; M6/Welle-X erbt den Trigger.

**R4 — Welle-7-Self-Close-Move kollidiert mit anderen
Refs.** `M5-ui-demo.md` ist intensiv verlinkt (von 7
Sub-Welle-Slice-Docs + roadmap.md + in-progress/
README.md + README.md/de.md + AGENTS.md). C4b muss alle
Refs sauber umstellen.
**Mitigation:** `grep -rn M5-ui-demo.md docs/ *.md` als
C4a-Vorbereitung; sed-basierter Mass-Edit + docs-check.

---

## 8. Wandert nach

- Bei C3-Closure: `M5-welle-7.md` + `M5-ui-demo.md`
  bleiben in `in-progress/` bis C4a Self-Close-Move.
- Nach C4a: beide unter `done/`.
- `done/M5-results.md` lebt unter `done/` als
  M5-Closure-Erbschafts-Artefakt.
- **M6 (Performance + Security + CI/CD)** als naechster
  aktiver Slice nach M5-Closure.

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [ ] **C1 — 5 M5-ADRs auf `Accepted`** (ADR 0036/0037/
  0038/0039/0040; Status-Header + Status-Pfad-Body-Block
  konsistent).
- [ ] **C2 — NEU `done/M5-results.md`** mit Welle-Tabelle
  + Pro-Welle-Reviews + Abnahme-Belege + S-1..S-6-Sweep
  + Wandert-Nach + ADR-Decision-Sweep.
- [ ] **C3 — `roadmap.md §3 M5` DoD-Checkboxen alle
  `[x]`** + M5 auf `Done` + „Aktiver Slice: M6".
- [ ] **C3 — `README.md` + `README.de.md` Status-Sync**
  (M5 Done; Test-Bilanz unveraendert 1722/80).
- [ ] **C3 — `in-progress/README.md` Aktive-Welle-Block**
  auf M6 ausgerichtet.
- [ ] **C4a — Self-Close-Move** `M5-ui-demo.md` +
  `M5-welle-7.md` nach `done/`.
- [ ] **C4b — Cross-Doc-Refs-Sync** nach Move
  (`M5-ui-demo.md` → `../done/M5-ui-demo.md` ueberall).
- [ ] **`make gates`** cache-frei gruen ohne Override.
- [ ] **`make docs-check`** cache-frei gruen.
- [ ] **`make fullbuild`** cache-frei gruen ODER
  dokumentierter Defer-Pfad (krb5-CVE).

**Anti-Scope-Verifikation (Welle 7 NICHT):**

- [ ] Keine neuen Code-Diffs.
- [ ] Keine neuen Tests.
- [ ] Keine neuen ADRs (nur Status-Flips).
- [ ] Kein Base-Image-Bump (Trigger 010 bleibt offen).
- [ ] Kein M6-Substanz-Vorgriff.

---

## References

- [`M5-ui-demo.md`](M5-ui-demo.md) §3.2 Welle 7 Plan-
  Items (kanonische Welle-7-Vorbelegung; S-1..S-6-Sweep-
  Liste).
- [`M4-welle-7.md`](../done/M4-welle-7.md) — M4-Closure-Welle-
  Pattern; direkter Vorbild-Slice fuer Struktur,
  Liefer-Reihenfolge, S-1..S-6-Sweep, ADR-Status-Flip-
  Block.
- [`M4-results.md`](../done/M4-results.md) — M4-Closure-
  Artefakt-Pattern (Welle-Tabelle + Abnahme-Belege +
  S-1..S-6-Sweep + Wandert-Nach).
- [`M3-results.md`](../done/M3-results.md) — M3-Closure-Artefakt
  als Zweit-Vorbild.
- [`../in-progress/roadmap.md §3 M5`](../in-progress/roadmap.md)
  — DoD-Checkboxen-Quelle.
- M5-ADRs:
  [`../../adr/0036-ui-stack-choice.md`](../../adr/0036-ui-stack-choice.md),
  [`../../adr/0037-http-api-surface-pattern.md`](../../adr/0037-http-api-surface-pattern.md),
  [`../../adr/0038-telemetry-stream-port.md`](../../adr/0038-telemetry-stream-port.md),
  [`../../adr/0039-run-control-and-status-tracking.md`](../../adr/0039-run-control-and-status-tracking.md),
  [`../../adr/0040-alarm-aggregation-and-stream-port.md`](../../adr/0040-alarm-aggregation-and-stream-port.md).
- Pattern-Vorbild **Welle-ohne-C1-mit-ADR-Status-Flip**:
  M4-Welle-7-C1 `d2071f0` (6 M4-ADRs `Provisional →
  Accepted`); M3-Welle-7-C1.1..C1.6 als Granular-
  Variante.
- Welle-6c-Closure-Stack (Pre-C0): `c317200` (Self-
  Close-Move) + `cfb9626` (Cross-Doc-Refs-Sync).
