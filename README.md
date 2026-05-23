# grid-gym

**English** | [Deutsch](README.de.md)

`grid-gym` is a planned modular open-source platform for the simulation,
validation, and analysis of electrical energy systems.

The focus is on deterministic execution, reproducible results,
replayability, fault injection, simulated real-time capability, and
integration suitability for test and research environments.

The project targets developers, research institutions, and system
integrators who want to model energy-management strategies, smart-grid
controls, battery-storage strategies, replay systems, and HIL-near tests
in a local, traceable environment.

## Status

**As of 2026-05-23:** M1 (Tick-Loop Spine) and M2 (Device Models) are
`Done`. M3 (Faults + Multi-Agent + Observability) is active:
Waves 0/1/2/3/4a/4b/5 are completed — the Multi-Agent subsystem is
complete (Foundation + Concretization), and the Observability
Foundation (Port-Trio + Null-Adapters + TickLoop hooks) is in place.
**Wave 6 (OTLP adapter) is the next active slice**; Wave 7 (M3
Closure) follows.

| Subsystem | Status | References |
| --- | --- | --- |
| Tick-Loop Spine (M1) | `Done` | [`done/M1-tick-loop-results.md`](docs/plan/planning/done/M1-tick-loop-results.md) |
| Device Models (M2) | `Done` | [`done/M2-devices-results.md`](docs/plan/planning/done/M2-devices-results.md); Battery, PV, Load, GridConnection, SmartMeter + GridModel balance productive |
| Fault Subsystem (M3 Waves 1+2) | `Done` | ADR [0022](docs/plan/adr/0022-fault-injection-protocol.md) `Provisional` + ADR [0025](docs/plan/adr/0025-fault-recovery-pattern.md) `Provisional`; `BatteryFaultAdapter` + `GridFaultAdapter` with `cell_failure`/`voltage_drop` and recovery logic |
| Multi-Agent Foundation (M3 Waves 3+4a) | `Done` | ADR [0023](docs/plan/adr/0023-agent-bus-protocol.md) `Provisional` + ADR [0026](docs/plan/adr/0026-agent-drain-registry-pattern.md) `Provisional`; `Agent` protocol + `AgentMessageBus` + TickLoop `agents` registry + step A0v/A0a drain + Agent Foundation state snapshot |
| Multi-Agent concrete (M3 Wave 4b) | `Done` | ADR [0027](docs/plan/adr/0027-rule-based-agent-scenario-pattern.md) `Provisional`; `RuleBasedAgent` with hybrid rules + plugin hook + scenario `agents` top-level block + bidirectional `agents.<type>.<id>` sub-snapshot resume match + end-to-end demo (`tests/integration/scenarios/agents_demo.yaml`) |
| Observability Foundation (M3 Wave 5) | `Done` | ADR [0024](docs/plan/adr/0024-observability-port-trio.md) `Provisional`; `LogPort`/`MetricsPort`/`TracePort` + `SpanContext` + Null-Adapter-Trio + additive TickLoop/Agent/Fault hooks. Plus ADR [0029](docs/plan/adr/0029-no-coverage-pragma-contract.md) `Accepted` (11th `arch_check` contract `AC-NO-COVERAGE-PRAGMA`). |
| OTLP Adapter (M3 Wave 6) | `Open` | `adapters/driven/telemetry-otlp/` + Compose-Collector + Span/Metric export verification |
| Protocol Adapters (M4) | `Pending` | MQTT, Modbus, OPC-UA, DNP3, IEC 61850 |
| UI + Demo (M5) | `Pending` | Web UI, scenario editor, live telemetry stream |
| Performance + Security + CI/CD (M6) | `Pending` | 10,000-points/s benchmark, SBOM, multi-version matrix |

**Test balance:** 1023 unit tests + 19 integration tests green
(Wave-5 end state `8b23602`). `make fullbuild` cache-free green
**without** override — Wave-5 acceptance criterion (full CI + runtime
image + Compose smoke + Trivy image audit) met. `make gates`
A-1 (lint, format-check, mypy `--strict`, arch-check 17/17
contracts kept incl. new `AC-NO-COVERAGE-PRAGMA`, test-unit,
coverage-gate 90/85 line / 95.55% total, critical-coverage 90,
dep-audit) cache-free green without override.

**CI:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml) with four
mandatory gates for `pull_request` and `push` on `main`:
`lint-imports`, `ruff check`, `python tools/arch_check.py`,
`mypy --strict`. See trigger doc
[`025-github-actions-four-gates.md`](docs/plan/planning/in-progress/025-github-actions-four-gates.md).

## Build, Test, Lint

The repository is **Docker-only**: the host only needs `docker` and
`make`. No local Python/uv installation. All builds, tests, and gates
run via Dockerfile stages.

```bash
make help                # list all targets
make gates               # all A-1 mandatory gates (lint, format-check,
                         # typecheck, arch-check, test-unit, coverage,
                         # critical-coverage, dep-audit)
make test-unit           # unit tests only
make test-integration    # integration tests via Compose (Postgres container)
make fullbuild           # gates + integration + runtime image build
```

Individual gates for fast feedback loops:

```bash
make lint                # ruff check
make format-check        # ruff format --check
make typecheck           # mypy --strict (ADR 0005)
make arch-check          # import-linter + tools/arch_check.py (ADR 0002 §A-1)
make arch-check-imports  # import-linter only (7 forbidden-import contracts)
make arch-check-custom   # tools/arch_check.py only (9 custom checks)
```

## MVP Scope

The first acceptance-ready state shall run locally on a developer machine
and require no external cloud services, real field devices, or internet
access at runtime. After provisioning the container images, the demo
shall be executable offline.

According to the requirements specification, the MVP comprises at least:

- local single-node operation via Docker Compose
- an end-to-end scenario with grid connection point, PV, load profile,
  smart meter, and battery storage
- live telemetry, time-series persistence, and deterministic replay
- a CLI or script for acceptance checks
- machine-readable acceptance results for replay verification,
  scenario validation, and demo health check

## Planned Functional Areas

- simulation core with discrete time steps, central time model, and
  deterministic event scheduler
- scenario, snapshot, export, and replay system
- canonical serialization for replay diff and golden-file comparisons
- device models for battery storage, PV systems, load profiles,
  grid connection points, and smart meters
- simplified grid models for frequency, voltage, and load behavior
- fault injection for communication failures, stale data, NaN values,
  frequency drops, voltage dips, and device failures
- REST API, WebSocket telemetry, and local web UI for demo and test operation
- PostgreSQL-based persistence in the MVP; further storage adapters optional
- architecture, integration, replay, and demo acceptance tests
- optional adapters and extensions such as MQTT, Modbus TCP, OPC-UA, DNP3,
  IEC 61850, TimescaleDB, InfluxDB, agents, HIL, MPC, and RL

## Project Structure

```text
.
├── .github/workflows/ci.yml     ← GitHub Actions: 4 mandatory gates (Trigger 025)
├── CHANGELOG.md
├── Dockerfile                   ← multi-stage (lint, arch-check, test, runtime)
├── LICENSE
├── Makefile                     ← build/test gates per Dockerfile stage
├── alembic.ini                  ← Postgres migrations (M1 Wave 6c)
├── pyproject.toml               ← build/tool configuration (ADR 0002 §6.1)
├── uv.lock                      ← pinned dependencies (uv)
├── .python-version              ← 3.14 (uv-compatible)
├── README.md                    ← English main version (this document)
├── README.de.md                 ← German version
├── deploy/compose.yml           ← productive Compose stack (M1 Wave 6c)
├── src/grid_gym/
│   ├── hexagon/
│   │   ├── core/
│   │   │   ├── agents/          ← Agent protocol + AgentMessageBus + RuleBasedAgent (M3 Waves 3+4a+4b)
│   │   │   ├── devices/         ← Battery, PV, Load, GridConnection, SmartMeter (M2)
│   │   │   ├── domain/          ← frozen dataclasses (Command, Event, ScenarioFault, ...)
│   │   │   ├── faults/          ← Battery + GridFaultAdapter (M3 Wave 2)
│   │   │   ├── grid_model/      ← balance model + LoadEvent/LoadProfile (M2 Wave 5)
│   │   │   ├── replay/          ← replay sample codec (M1 Wave 5)
│   │   │   ├── scenario/        ← YAML loader + validator (M1 Wave 5)
│   │   │   ├── serialization/   ← canonical_json (M1 Wave 0a, Trigger 014)
│   │   │   └── simulation/      ← TickLoop + scheduler
│   │   └── ports/driven/        ← ClockPort, RandomPort, FaultPort, RunRepositoryPort
│   └── adapters/
│       ├── driving/             ← HTTP API (FastAPI, M1 Wave 6a)
│       └── driven/              ← Postgres, RandomMT (M1 Waves 6b/6c)
├── tests/
│   ├── unit/                    ← pytest unit tests (1023 as of 2026-05-23)
│   ├── integration/             ← Compose-based integration tests (19 tests)
│   └── unit/_arch_check_*       ← architecture tests (7 import-linter + 7 custom AC checks)
├── tools/
│   └── arch_check.py            ← AST/graph architecture checks (ADR 0002 §A-1)
├── spec/
│   ├── lastenheft.md            ← normative requirements (GG-*)
│   └── architecture.md          ← architecture (GG-AR-*)
└── docs/
    ├── plan/
    │   ├── adr/                 ← Architecture Decision Records (0001..0027)
    │   └── planning/
    │       ├── open/            ← trigger watch, open follow-ups
    │       ├── next/            ← planned but not yet active
    │       ├── in-progress/     ← active roadmap + slice plans
    │       └── done/            ← completed slices + closure notes
    ├── user/                    ← user-/operator-facing (code review etc.)
    └── archive/                 ← discarded/historical drafts
```

Source code, tests, and tooling scripts (`src/grid_gym/`, `tests/`,
`tools/`) were created with Spike-0 (closure: [`docs/plan/planning/done/spike-0.md`](docs/plan/planning/done/spike-0.md),
2026-05-15); `Dockerfile`, `Makefile`, and `pyproject.toml` form
the binding build/gate layer per
[`ADR 0002`](docs/plan/adr/0002-language-and-build-stack.md)
(`Accepted` 2026-05-15) and
[`ADR 0005`](docs/plan/adr/0005-type-check-gate.md)
(`Accepted` 2026-05-15).

The documentation and planning structure is defined in
[`docs/plan/adr/0001-documentation-and-planning-structure.md`](docs/plan/adr/0001-documentation-and-planning-structure.md).

**Note:** the linked ADRs, slice plans, and planning documents under
[`docs/`](docs/) and [`spec/`](spec/) are written in German. The English
README mirrors the structure and key facts; for deep-dive content,
consult [`README.de.md`](README.de.md) or the German source documents.

## License

This project is licensed under the MIT License. Details are in [`LICENSE`](LICENSE).
