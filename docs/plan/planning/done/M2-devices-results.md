# M2 — Geraetemodelle — Closure-Ergebnisse

**Status:** Done (2026-05-20). M2-Abschluss-Gate
`make fullbuild` cache-frei gruen **ohne**
`CRITICAL_COV_TARGETS`-Override seit Welle-6c-Feat
(`c31052c`).
**Bezug:** Slice-Plan [`M2-devices.md`](../done-archive/M2-devices.md);
Welle-6c-Slice-Begleit [`welle-6c.md`](../done-archive/welle-6c.md);
Roadmap [`../in-progress/roadmap.md`](../in-progress/roadmap.md)
§3 M2.

---

## 1. Welle-Tabelle

| Welle | Datum       | Lieferung                                                                                                                                            | Commits          |
| ----- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| 0a    | 2026-05-18  | Trigger 014 (generischer Snapshot-Codec) — Vorabraeumung S-1                                                                                          | `3322cb8`, `1f19996` |
| 0b    | 2026-05-18  | Trigger 015 (Runtime-Image-Hardening) — Vorabraeumung S-4                                                                                             | `ee37f36` |
| 0c    | 2026-05-18  | S-6 Lastenheft-Coverage-Sweep                                                                                                                         | `314f853` |
| 0-RF  | 2026-05-18  | Welle-0-Review-Fixes                                                                                                                                  | `d490905`, `51a5f4e`, `6d39c7a`, `df99d97`, `6e108d6` |
| 1     | 2026-05-18  | [`ADR 0013`](../../adr/0013-device-model-protocol.md) `DeviceModel`-Protocol; `core/devices/_protocol.py` + Protocol-Adherence-Test (`NullDevice`)                                                 | `b927e7a` + Review-Folge (`88252f1`, `9a61823`, `129c137`, `a6c912c`, `6e108d6`) |
| 2     | 2026-05-18  | [`ADR 0014`](../../adr/0014-battery-snapshot-schema.md) Battery-Snapshot-Schema; `BatteryDevice` mit SOC/Ramp/Wirkungsgrad; Trigger 013 mechanisch geschlossen                                       | `6247228`, `48f0106`, `5866117`, `9a138c2` + Review-Folge (`4600e79`, `eb09e9b`, `d7bc2d9`, `f4988ff`, `bd13882`) |
| 3a    | 2026-05-18  | [`ADR 0016`](../../adr/0016-pv-load-device-pattern.md) PV-Pattern; `PvDevice` mit konstantem `rated_power_kw`                                                                                       | `2abbd12` + Review-Folge |
| 3b    | 2026-05-18  | [`ADR 0016`](../../adr/0016-pv-load-device-pattern.md) Load-Pattern (gemeinsame ADR); `LoadDevice` mit `set_power_kw`-Command                                                                       | `e5d3c9a` + Review-Folge (`6cad963`, `ea875c3`, `60582e7`, `45a9be6`, `b4e3ce7`) |
| 4a    | 2026-05-19  | [`ADR 0017`](../../adr/0017-grid-connection-device-pattern.md) GridConnection-Pattern; `GridConnectionDevice` stateful `import_kwh`/`export_kwh`                                                            | `b73b44a` + Review-Folge (`579cd5a`, `1ed976a`, `7ad78e4`, `bdce682`) |
| 4b    | 2026-05-19  | [`ADR 0018`](../../adr/0018-smart-meter-device-pattern.md) SmartMeter-Pattern; `SmartMeterDevice` mit `attach_sources`                                                                                  | `94efb2a` + Review-Folge (`1093b2c`, `bc94a8c`, `d3769dc`, `85dced7`) |
| 5a    | 2026-05-19  | [`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md) GridModelBilanz; Frequenz/Spannung-Pfade                                                                                                     | `268a1c0` + Review-Folge (`676f684`, `16f8b9b`, `91e0118`, `1af57b8`) |
| 5b    | 2026-05-19  | [`ADR 0020`](../../adr/0020-load-profile-and-event-pattern.md) LoadProfile + LoadEvent; `CRITICAL_COV_TARGETS` Default um `core/grid_model` erweitert; M2-Default-Gate erstmals ohne Override gruen          | `fa02c0b` + Review-Folge (`5f64f78`, `47c054a`, `12ad8f9`, `e5f8f86`, `29d23bb`) |
| 6a    | 2026-05-19  | [`ADR 0015`](../../adr/0015-snapshot-envelope-v2.md) Snapshot-Envelope-v2 (Provisional); TickLoop iteriert Devices + ruft `grid_model.update`; Sub-Snapshots `devices.<typ>.<id>` + `grid_model`; `TickLoopSnapshotVersionError` | `27a441f` + Review-Folge (`ff45c11`, `e3909f0`, `f7f21a6`, `da8deef`, `779fcea`) + Doc-Sync `765d348` |
| 6b    | 2026-05-19  | [`ADR 0021`](../../adr/0021-scenario-loader-and-tick-loop-event-wiring.md) Scenario-Loader + TickLoop-Event-Wiring (Provisional); `build_devices`/`build_tick_loop`; LoadEvent/LoadProfile-Wiring; GridConnection-Auto-Schluss; 14 Review-Findings in feat-Commit                | `8c26498` (ADR-Proposed), `c58dbc2` (ADR-Round-1), `0f1c597` (feat + Review-Folge), `93f784f` (Doc-Sync) |
| 6c    | 2026-05-20  | MVP-Demo-Szenario `tests/integration/scenarios/mvp_demo.yaml`; Determinismus-Integrationstest + Postgres-Roundtrip; Permutations-Property-Test; [`ADR 0015`](../../adr/0015-snapshot-envelope-v2.md) + 0021 → `Accepted`; 2 Review-Folge-Commits         | `8a3aa2f`, `c31052c`, `6adb041`, `43aabbd`, `7a3c171` |
| 7     | 2026-05-20  | Closure: Slice-Plan + `welle-6c.md` nach `done/`; `M2-devices-results.md`; 9 SOLLTE-Open-Trigger (`016..024`); `roadmap.md` M2 → `Done`, M3 → naechster aktiver Slice                                          | dieser Commit-Stack |

## 2. Abnahme-Belege

- **`make fullbuild`-Gate**: cache-frei gruen **ohne**
  `CRITICAL_COV_TARGETS`-Override am 2026-05-20 nach
  Welle-6c-Feat (`c31052c`). Letzter Lauf in Welle-6c-Review-
  Folge-2 (`7a3c171`) liefert
  `[fullbuild] full closure: ci + runtime image + compose
  smoke green` mit `/health: ok`.
- **Default-`CRITICAL_COV_TARGETS`**:
  ```text
  src/grid_gym/hexagon/core/simulation
  src/grid_gym/hexagon/core/devices/battery
  src/grid_gym/hexagon/core/devices/pv
  src/grid_gym/hexagon/core/devices/load
  src/grid_gym/hexagon/core/devices/grid_connection
  src/grid_gym/hexagon/core/devices/smart_meter
  src/grid_gym/hexagon/core/grid_model
  src/grid_gym/hexagon/core/scenario
  src/grid_gym/hexagon/core/replay
  ```
  Coverage ≥ 90 % Line + Branch auf allen Targets
  (`make coverage-gate-critical`).
- **Unit-Tests**: 762 (Welle-6c-Stand, +519 ggue. M1-Welle-7-
  Stand von 243).
- **Integration-Tests**: 9 (Welle-6c-Stand, +4 ggue. M1-Welle-7-
  Stand von 5). Inkl. `PostgresRunRepository`-Roundtrip (5),
  MVP-Demo Determinismus + Postgres-Roundtrip (2), YAML-Loader-
  Allowlist-Drift (2).
- **A-1-Contracts**: alle 16 gruen (`make arch-check` zeigt
  „Contracts: 16 kept, 0 broken").
- **`make openapi-validate`**: gruen
  (`/src/artifacts/openapi.json: OK`).
- **`make image-audit`**: gruen
  (`trivy --ignore-unfixed` ohne HIGH/CRITICAL).
- **`make dep-audit`**: gruen
  (pip-audit ohne Schwachstellen).

## 3. Pro-Welle-Reviews

Pattern: jede Welle hat eine commit-gebundene Review-Folge,
entweder als separate `*-Review-Folge`-Commits (Wellen 1..5,
6a) oder in den feat-Commit hineinkombiniert (Welle 6b) oder
in mehreren `fix(welle-6c)`-Commits (Welle 6c, zwei
Review-Folgen).

| Welle | Externer Review                           | Review-Fix-Commit(s)                                                  |
| ----- | ----------------------------------------- | --------------------------------------------------------------------- |
| 0a–0c | — (Welle-7-End-to-End-Sweep absorbiert)   | n/a                                                                   |
| 1     | ✓ Welle-1-Review-Folge                    | `88252f1`, `9a61823`, `129c137`, `a6c912c`, `6e108d6`                 |
| 2     | ✓ Welle-2-Review-Folge                    | `4600e79`, `eb09e9b`, `d7bc2d9`, `f4988ff`, `bd13882`                 |
| 3     | ✓ Welle-3-Review-Folge                    | `6cad963`, `ea875c3`, `60582e7`, `45a9be6`, `b4e3ce7`                 |
| 4a    | ✓ Welle-4a-Review-Folge                   | `579cd5a`, `1ed976a`, `7ad78e4`, `bdce682`                            |
| 4b    | ✓ Welle-4b-Review-Folge                   | `1093b2c`, `bc94a8c`, `d3769dc`, `85dced7`                            |
| 5a    | ✓ Welle-5a-Review-Folge                   | `676f684`, `16f8b9b`, `91e0118`, `1af57b8`                            |
| 5b    | ✓ Welle-5b-Review-Folge                   | `5f64f78`, `47c054a`, `12ad8f9`, `e5f8f86`, `29d23bb`                 |
| 6a    | ✓ Welle-6a-Review-Folge                   | `ff45c11`, `e3909f0`, `f7f21a6`, `da8deef`, `779fcea`                 |
| 6b    | ✓ Review-Folge in `0f1c597`-feat (kombiniert; 14 Findings) | `0f1c597`                                                |
| 6c    | ✓ Review-Folge-1 (4 M + 6 L) + Review-Folge-2 (User-Cross-Check; M+L+L) | `43aabbd`, `7a3c171`                                       |
| 7     | ✓ M2-Welle-7-End-to-End-Sweep             | dieser Commit-Stack                                                   |

## 4. S-1..S-6-Verification (M2-Welle-7-End-to-End-Sweep)

Spiegelt das M1-Welle-7-Pattern (siehe
`done/M1-tick-loop-results.md §7`); referenziert
`M2-devices.md §2 Welle-7-S-1..S-6-Items`:

- **S-1 (Trigger 014, generic snapshot codec)** —
  erfuellt in Welle 0a (`3322cb8`); Closure-Notiz in
  [`done/014-generic-snapshot-format-codec.md`](../done-archive/014-generic-snapshot-format-codec.md).
- **S-2 (Sub-Slicing-Heuristik)** — erfuellt in
  `M2-devices.md §3 Sub-Slicing-Schwelle`; aktiv eingesetzt
  fuer Wellen 0 (0a/0b/0c), 3 (3a/3b), 4 (4a/4b),
  5 (5a/5b), 6 (6a/6b/6c).
- **S-3 (Default-Gate ohne Override)** — erfuellt seit
  Welle 5b (`fa02c0b`); Welle 6c (`c31052c`) bestaetigt
  `make fullbuild` cache-frei gruen **ohne** Override.
- **S-4 (Trigger 015, runtime image hardening)** —
  erfuellt in Welle 0b (`ee37f36`); Closure-Notiz in
  [`done/015-runtime-image-hardening.md`](../done-archive/015-runtime-image-hardening.md).
- **S-5 (ADR-Erweiterungs-Pattern, ohne Supersedes)** —
  erfuellt durch 9 neue ADRs (0013..0021), alle als
  Erweiterungen ohne Supersedes ([`ADR 0011`](../../adr/0011-schaerfung-ohne-abloesung.md) Pattern
  konsequent fortgefuehrt). [`ADR 0015`](../../adr/0015-snapshot-envelope-v2.md) (Snapshot-Envelope
  v1→v2) ist der einzige strukturierende Bruch im
  Sub-Snapshot-Vertrag und mit `TickLoopSnapshotVersionError`
  fail-fast erzwungen.
- **S-6 (Lastenheft §6..§25 Coverage-Sweep)** — erfuellt
  in Welle 0c (`314f853`); SOLLTE-Restposten in 9
  Open-Triggers `016..024` aktiviert (siehe §5 unten).

## 5. Welle-7-Erbschaft fuer M3+/M6+

Diese Items sind explizit als M2-Closure-Restposten in
`open/` aktiviert:

**SOLLTE-Geraete** (M3 oder eigene Slices):

- Trigger [`016-sollte-ev-charger-device`](../open/016-sollte-ev-charger-device.md) — `GG-DEV-015` EV-Charger
- Trigger [`017-sollte-transformer-device`](../open/017-sollte-transformer-device.md) — `GG-DEV-016` Transformer
- Trigger [`018-sollte-wind-device`](../open/018-sollte-wind-device.md) — `GG-DEV-017` Wind
- Trigger [`019-sollte-diesel-device`](../open/019-sollte-diesel-device.md) — `GG-DEV-018` Diesel

**SOLLTE-Netz** (M3 oder eigene Slices):

- Trigger [`020-sollte-island-grid`](../open/020-sollte-island-grid.md) — `GG-GRID-005` Inselnetz
- Trigger [`021-sollte-transformer-limits`](../open/021-sollte-transformer-limits.md) — `GG-GRID-006` Transformatorgrenzen
- Trigger [`022-sollte-reactive-power`](../open/022-sollte-reactive-power.md) — `GG-GRID-007` Blindleistung

**SOLLTE-Battery** (M3-Telemetry-Erweiterung):

- Trigger [`023-sollte-battery-temperature`](../open/023-sollte-battery-temperature.md) — `GG-BESS-006` Temperatur
- Trigger [`024-sollte-battery-cell-voltage`](../open/024-sollte-battery-cell-voltage.md) — `GG-BESS-007` Zellspannung

**M3-/M6-Forward-Linked Triggers** (bereits vor M2 vermerkt,
warten auf Aktivierung):

- Trigger 005 / 006 / 007 — Type-Checker-Strategie (M3+)
- Trigger 008 — SBOM-Aktivierung (M6 Release-Slice)
- Trigger 011 — `MLRandomPort` Sub-Seed-Wortbreite
  (M3-Multi-Agent)
- Trigger 012 — Snapshot-Composition (M6 Persistenz)

**Snapshot-Migration v1→v2**: in M2 nur als Fail-Fast
implementiert (`TickLoopSnapshotVersionError` mit M6-
`GG-PERSIST-*`-Pointer in der Message). Ein Lese-Migrations-
Pfad bleibt M6-Material (`GG-PERSIST-*`-Slice).

## 6. M2-Wandert-Nach

- ✓ `in-progress/M2-devices.md` (vollzogen 2026-05-18 mit
  Welle-0a-Start) → ✓ `done/M2-devices.md` (vollzogen
  2026-05-20 mit Welle-7-Closure-Commit-Stack); Forwarder-
  Stub bleibt in `in-progress/` per [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md) §3
  (Accepted-ADRs zeigen weiterhin auf den `in-progress/`-
  Pfad).
- ✓ `in-progress/welle-6c.md` (Slice-Begleit, vollzogen
  Welle-6c-C0 `8a3aa2f`) → ✓ `done/welle-6c.md` (vollzogen
  Welle-7-C1 `git mv`).
- M3 wechselt jetzt von `Vorbelegung` (in
  `roadmap.md §3 M3`) auf `Naechster aktiver Slice` — der
  M3-Slice-Plan wird mit M3-Welle-0-Start eroeffnet.

## 7. Nicht-vollzogene Items (bewusst)

- **M2-Status-Header in `M2-devices.md`**: bleibt
  `In Progress` als historisches Artefakt im Datei-Body
  (§1..§7 sind die Slice-Plan-Inhalte aus der laufenden
  M2-Phase); der `Done`-Status ist im Top-Header (§0
  `**Status:**`-Block) gesetzt. Diese Inkonsistenz ist
  bewusst — der Slice-Plan ist historisch und sollte
  nicht retroaktiv umgeschrieben werden (gleiches Pattern
  wie `done/M1-tick-loop-spine.md`).
- **`tool_version`-Bump**: bleibt auf `0.1.0`
  (`pyproject.toml`); ein Release-Bump kommt mit M6
  (`GG-CICD-007` Release-Workflow).
