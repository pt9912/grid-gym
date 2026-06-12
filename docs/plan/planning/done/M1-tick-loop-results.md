# M1 — Tick-Loop-Spine — Closure-Ergebnisse

**Status:** Done (2026-05-17). M1-Abschluss-Gate
`make fullbuild` mit explizitem
`CRITICAL_COV_TARGETS`-Override gruen.
**Bezug:** Slice-Plan [`M1-tick-loop-spine.md`](../done-archive/M1-tick-loop-spine.md);
Roadmap [`../in-progress/roadmap.md`](../in-progress/roadmap.md)
§3 M1.

---

## 1. Welle-Tabelle

| Welle | Datum       | Lieferung                                                                                           | Commits          |
| ----- | ----------- | --------------------------------------------------------------------------------------------------- | ---------------- |
| 0     | 2026-05-15  | [`ADR 0007`](../../adr/0007-random-port.md) `Provisional`, Trigger 001 (Code-Review-Doku + PR-Template), Lock-Refresh                  | siehe Trigger 001 |
| 1     | 2026-05-17  | Domain-Modelle: `Quality`/`CommandResult` (StrEnum), `RunMetadata`/`TelemetryPoint`/`Command`/`Event` (Frozen-Dataclasses), `SnapshotEnvelope` mit `version:int`-Konvention | `7d4cee5`, `97dad24` |
| 2     | 2026-05-17  | Driven-Ports `ClockPort`/`RandomPort`; `MersenneTwisterRandomPort`-Adapter; [`ADR 0007`](../../adr/0007-random-port.md) `Accepted` + Trigger 003 done | `33d6ec8`, `72ebaa1`, `efe6f60` |
| 3     | 2026-05-17  | Deterministischer `Scheduler` mit Tie-Breaking `(time, priority, source, sequence, event_id)`       | `75b0940`, `ae20b4f` |
| 4     | 2026-05-17  | `TickLoop` + `TickResult`; Snapshot-Composition via `RandomPort.snapshot_as_mapping` ([`ADR 0010`](../../adr/0010-randomport-snapshot-as-mapping.md)); Trigger 012 done; [`ADR 0011`](../../adr/0011-schaerfung-ohne-abloesung.md) (Schaerfung ohne Supersedes) | `75804e6`, `28adab0`, `9f595e7`, `d08b5a9` |
| 5     | 2026-05-17  | Scenario-Loader + Validator + Hash (`GG-SCN-001..008`); Replay-Mapper + Diff (`GG-REPLAY-001..003`/`007`); Triggers 013 + 014 (open) | `d4029e3`, `b2e1517`, `04ce698`, `51bf108`, `b18f3f1` |
| 6a    | 2026-05-17  | FastAPI-Adapter `adapters/driving/http_api/`; `make openapi-validate` gruen                          | `ffbca2c` |
| 6b    | 2026-05-17  | `RunRepositoryPort` + `InMemoryRunRepository`; FastAPI-Wiring via `configure_run_repository`        | `395634f` |
| 6c    | 2026-05-17  | `PostgresRunRepository` + alembic + Integration-Tests via testcontainers; Triggers 009 + 010 done   | `f7b699d` |
| 6d    | 2026-05-17  | `make fullbuild` gruen (`apt-get upgrade`, `PYTHONPATH=/app/src`, `python -m uvicorn`, healthcheck-disable) | `b5243fe` |
| 7     | 2026-05-17  | Closure: Triggers 009/010 nach `done/`, Trigger 015 (Production-Image-Hardening) eroeffnet, Slice-Plan nach `done/`, Roadmap M1 → Done | dieser Commit-Stack |

## 2. Abnahme-Belege

- **`make fullbuild`-Override**:
  ```bash
  make fullbuild CRITICAL_COV_TARGETS="\
      src/grid_gym/hexagon/core/domain \
      src/grid_gym/hexagon/ports/driven \
      src/grid_gym/adapters/driven/random_mt \
      src/grid_gym/hexagon/core/simulation \
      src/grid_gym/hexagon/core/scenario \
      src/grid_gym/hexagon/core/replay \
      src/grid_gym/adapters/driving/http_api"
  ```
  Letzter Lauf am 2026-05-17 lieferte
  `[fullbuild] full closure: ci + runtime image + compose
  smoke green`.
- **Unit-Tests**: 243 (Welle-7-Stand). Coverage 90+ Line + Branch
  auf allen kritischen Targets oben.
- **Integration-Tests**: 5 (`PostgresRunRepository`-Roundtrip
  via testcontainers).
- **A-1-Contracts**: alle 16 gruen (`make arch-check` zeigt
  „Contracts: 7 kept, 0 broken" + „[arch_check] all contracts
  kept").
- **`make openapi-validate`**: gruen
  (`/src/artifacts/openapi.json: OK`).
- **`make image-audit`**: gruen
  (`trivy --ignore-unfixed` ohne HIGH/CRITICAL nach
  `apt-get upgrade -y` im runtime-Stage).

## 3. Welle-7-Erbschaft fuer M2/M6

Diese Items sind explizit als Welle-7-Closure-Restposten in
Triggers vermerkt:

- **Trigger 005** (`pyright-vs-mypy-reeval`) — bleibt `open`,
  M1-Code hat keinen Aktivierungs-Trigger.
- **Trigger 006** (`mypy --strict-bytes`) — bleibt `open`, kein
  M1-Konflikt.
- **Trigger 007** (`pyright-precommit-adr`) — bleibt `open`,
  Pre-Commit-Hooks sind M6-Scope.
- **Trigger 008** (`sbom-activation`) — bleibt `open`,
  Aktivierung mit M6 (Security/CI-Haertung).
- **Trigger 011** (`mlrandomport-subseed-width`) — bleibt
  `open`, Aktivierung mit `MLRandomPort` (Folge-ADR).
- **Trigger 013** (`replay-diff-tick-ms-parameter`) — bleibt
  `open`, Aktivierung mit erstem Replay-Diff `tick_ms != 1000`.
- **Trigger 014** (`generic-snapshot-format-codec`) — bleibt
  `open`, „Pattern-Bestaetigung mit Welle-5-Abschluss"
  (5-faches *FormatError); Refactor mit sechstem Subsystem
  Pflicht (M2-Geraete).
- **Trigger 015** (`runtime-image-hardening`) — Welle-6d-
  Erbe: `uv sync --no-editable`, Shebang-Rewrite oder
  Pip-Relocate, Base-Image-Patch-Strategie. Aktivierung mit M6.

## 4. Was M1 NICHT geliefert hat

- Geraetemodelle (Battery, PV, Load, Smart Meter, Grid
  Connection) — `GG-DEV-010..014`, `GG-BESS-001..008`,
  `GG-GRID-001..007`. **M2**.
- Fault Injection — `GG-FAULT-001..010`. **M3**.
- Multi-Agent-Subsystem — `GG-AGENT-001..008`. **M3**.
- OpenTelemetry-Tracing — `GG-OTEL-001..004`. **M3**.
- Protokolladapter (MQTT/Modbus/OPC-UA/DNP3/IEC) — **M4**.
- UI/Demo — `GG-UI-001..009`. **M5**.
- Performance-Benchmarks (`GG-RT-004/005`),
  Production-Image-Hardening (Trigger 015), SBOM (Trigger 008),
  GitHub-Actions-Matrix — **M6**.

## 5. ADRs aus M1

- `ADR 0007` — `RandomPort`-Implementierung (`Accepted`).
- `ADR 0009` — `RandomPort`-Snapshot-Schema (`Accepted`).
- `ADR 0010` — `RandomPort.snapshot_as_mapping` Composition-API
  (`Accepted`).
- `ADR 0011` — Schaerfung durch parallele ADR ohne Supersedes
  (`Accepted`, Self-bootstrap).
- `ADR 0008` — Enum-Subklassen als [`AC-DOMAIN-FROZEN-F`](../../adr/0008-enum-as-domain-frozen-form.md#adr-0008--enum-subklassen-als-ac-domain-frozen-form)orm
  (`Provisional` → `Accepted` mit M1-Welle-1-PR-Mergung).

## 6. Reviewer-Stempel

**Pro-Welle-Reviews (committeted Review-Fix-Commits):**

| Welle | Externer Review | Review-Fix-Commit(s) |
| ----- | --------------- | -------------------- |
| 0     | ✓ Welle-0-Review (Spike-0-Drittes-Review) | `791af26` |
| 1     | — (kein separater Sweep — Befunde durch Welle-2-Review-Iteration v1 abgefangen) | n/a |
| 2     | ✓ Welle-2-Review v1+v2 (intern + extern) | `bacc43b`, `0415b14`, `baef02a` |
| 3     | ✓ Welle-3-Review | `ae20b4f` |
| 4     | ✓ Welle-4-Review | `d08b5a9` |
| 5     | ✓ Welle-5-Review v1+v2 | `51bf108`, `b18f3f1` |
| 6a–6d | — (keine separaten Reviews; Welle-7-End-to-End-Sweep adressiert die Schicht) | n/a |
| 7     | ✓ Welle-7-Final-End-to-End-Sweep (siehe §7) | dieser Commit-Stack |

**Korrektur gegenueber dem ersten Closure-Wortlaut:** Wellen 1
und 6a–6d hatten **keine** separate externe Reviewer-Schleife —
ihre Befunde sind teils ueber die jeweils naechste Welle
mitgenommen, teils erst durch den finalen Welle-7-End-to-End-
Sweep (§7) typisiert aufgefallen. Der ursprueng-lich behauptete
Satz „zwei externe Reviewer-Iterationen pro Welle" war
faktisch nicht durch die Git-History gedeckt.

## 7. Welle-7-End-to-End-Sweep

Vor dem M2-Slice-Start ist M1 als Ganzes durch einen
unabhaengigen End-to-End-Review gegangen (siehe Commit-Body
dieses Stacks bzw. Welle-7-Final-Review-Output). Befunde:

- **M-1 (must-fix, hier behoben):** Reviewer-Stempel-Satz
  faktentreu gemacht (siehe §6 oben).
- **M-2 (must-fix, hier behoben):** dieser §7 als Anker fuer
  den Welle-7-Sweep angelegt; ohne ihn waere die M1-Bilanz
  audit-instabil.
- **M-3 (must-fix, hier behoben):** `Makefile`-Target `ci`
  liefert bei `coverage-gate-critical`-Fail einen klaren
  M1-Override-Hinweis (siehe Commit-Body).
- **M-4 (dokumentierter Welle-5-Restposten, nicht Pflicht-Fix
  vor M2):** Triggers 013 und 014 sind **bewusst aktiv offen**,
  nicht „nicht-final umgesetzt":
  - **Trigger 013** (`diff_replay`-tick-ms-Parameter,
    `docs/plan/planning/done-archive/013-replay-diff-tick-ms-parameter.md`):
    aktuell `tick = simulation_time // 1000` ist Welle-5-Default
    fuer `tick_ms=1000`. Aktivierung mit erstem Replay-Diff
    gegen `tick_ms != 1000` — typisch M2-Geraet mit
    `tick_ms=10/100`.
  - **Trigger 014** (`generic-snapshot-format-codec`,
    `docs/plan/planning/done-archive/014-generic-snapshot-format-codec.md`):
    fuenffaches `*FormatError`-Pattern (RandomPort, Scheduler,
    TickLoop, Scenario, Replay) ist heute pre-mature-
    abstraction-konform belassen. Aktivierung mit sechstem
    Subsystem (`devices/battery`-Validierung in M2-Welle-0).
  Beide Triggers haben dokumentierte Aktivierungs-Kriterien und
  sind **M1-Closure-konform** (Welle 5 Closure-Block in
  `done/M1-tick-loop-spine.md` §3 Welle 5 listet sie explizit
  als Welle-5-bewusst-verschobene Restposten). Sie sind **NICHT**
  M1-Reststeuerung, sondern **M2-Welle-0-Pflicht-Aktivierung**.

- **S-1..S-6 (should-consider, fuer M2-Slice-Plan):**
  - **S-1**: Trigger 014 (`generic-snapshot-format-codec`)
    als M2-Welle-0-Pflicht-Item — sechstes Subsystem
    (`devices/battery`-Validierung) ist der mechanische
    Aktivierungs-Trigger.
  - **S-2**: Sub-Slicing-Heuristik dokumentieren (Welle 6
    zerfiel in 6a/b/c/d ungeplant — M2 soll das nicht
    wiederholen ohne dokumentierte Schwelle).
  - **S-3**: M2-DoD ohne `CRITICAL_COV_TARGETS`-Override
    formulieren — kein M1-Pivot-Pattern wiederholen.
  - **S-4**: Trigger 015 (`runtime-image-hardening`,
    `uv sync --no-editable` + Shebang-Rewrite) als M2-Welle-0-
    Vorab-Raeumung einplanen, bevor neue Adapter mit den
    Welle-6d-Pragma-Hacks koppeln.
  - **S-5**: [`ADR-0008`](../../adr/0008-enum-as-domain-frozen-form.md)+0011-Erweiterungs-Pattern strikt
    fortsetzen (neue Domain-Form → eigene Erweiterungs-ADR,
    nicht Supersedes).
  - **S-6**: Lastenheft-Sektionen-6-25-Coverage als
    M2-Welle-0-Closure-Sweep mechanisch durchdiffen.

**Verdict:** „Approve" nach Behebung von M-1/M-2/M-3 in
diesem Commit-Stack (vorher „Request Changes").

Datum: 2026-05-17.
