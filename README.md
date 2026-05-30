# grid-gym

**English** | [Deutsch](README.de.md)

`grid-gym` is an open-source platform for the deterministic simulation,
validation, and analysis of electrical energy systems. It models grid
connection points, PV arrays, battery storage, smart meters, and load
profiles with reproducible tick-loop execution, snapshot/replay, fault
injection, and protocol adapters for field-bus telemetry.

## Who is it for?

`grid-gym` targets developers, research institutions, and system
integrators who need a local, traceable environment for energy-management
strategies, smart-grid controls, battery-storage strategies, replay
systems, and HIL-near tests — without requiring real field devices,
cloud services, or internet access at runtime.

## What can I run today?

`grid-gym` is already executable as a local, Docker-based validation
environment. The current implementation includes:

- a deterministic tick loop with snapshot and replay support
- productive device models for battery, PV, load, grid connection, and
  smart meter
- fault injection and recovery flows
- multi-agent scenarios with a rule-based agent
- structured logs, metrics, and traces via the observability port trio
- an OTLP adapter with a local OpenTelemetry Collector smoke test
- an MQTT protocol adapter with Mosquitto-based integration tests

You can run the current gates and scenarios with:

```bash
make help
make gates              # 9 mandatory gates (lint, format, typecheck,
                        # arch-check, tests, coverage, critical-coverage,
                        # dep-audit, noqa-gate)
make test-unit          # unit test suite (1211 tests as of 2026-05-30)
make test-integration   # Compose/testcontainers integration suite
                        # (22 tests incl. OTLP and MQTT smokes)
```

Example YAML scenarios live under
[`tests/integration/scenarios/`](tests/integration/scenarios/).

The repository is **Docker-only**: the host only needs `docker` and
`make`. No local Python or `uv` installation is required.

> `make fullbuild` currently includes an `image-audit` step that may
> fail while a pending Debian-13 base-image CVE bump
> (`CVE-2026-40356` in the `krb5` family) is addressed in a separate
> base-image-bump stack. The mandatory development gate is `make gates`.

## What makes it trustworthy?

- **Deterministic execution.** A central tick loop drives a discrete
  time model; snapshot envelopes and replay samples are
  byte-reproducible via canonical JSON serialization.
- **Enforced architecture.** 19 architectural contracts run on every
  `make arch-check`: 7 forbidden-import contracts via `lint-imports`
  plus 12 custom AST/graph checks in
  [`tools/arch_check.py`](tools/arch_check.py) (including
  `AC-ADAPTER-LIGHTWEIGHT`, `AC-OTLP-ADAPTER-NO-TIME`, and
  `AC-TICK-LOOP-PRIVATE-RESUME-ERRORS`).
- **Nine-stage mandatory gate.** `make gates` runs lint, format-check,
  `mypy --strict`, arch-check, unit tests, coverage (90 % line per
  module / 85 % critical / 96 % total), critical-coverage,
  dependency audit, and a `# noqa` ban — all cache-free green without
  any local override.
- **ADR-driven decisions.** Every load-bearing decision is recorded as
  an [Architecture Decision Record](docs/plan/adr/); M1..M3 closure
  ADRs are `Accepted`, M4 wave ADRs land as `Provisional` and become
  `Accepted` at milestone closure.
- **CI mirrors local.** GitHub Actions runs the same `lint-imports`,
  `ruff check`, `tools/arch_check.py`, and `mypy --strict` gates on
  every pull request and `main` push
  ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

## How does it relate to bess-ems?

`grid-gym` and [`bess-ems`](https://github.com/pt9912/bess-ems) are
sibling projects in the same energy-systems toolkit.

`grid-gym` is the deterministic simulation, replay, and validation
environment. It models electrical energy systems, injects faults,
records traces, and provides reproducible test scenarios.

`bess-ems` is a battery energy-management system for operating Battery
Energy Storage Systems (BESS) with a safety-first control loop,
market/schedule handling, and protocol adapters.

In practice, `grid-gym` can serve as a local test and validation
environment for a production EMS such as `bess-ems`: the EMS acts as
the system under test, while `grid-gym` provides simulated devices,
grid behavior, telemetry, replay, and fault scenarios.

The projects share architectural ideas such as hexagonal boundaries,
explicit ports/adapters, and architecture checks — but `grid-gym` is
not an EMS implementation and does not duplicate `bess-ems` control
logic.

---

## Status

As of **2026-05-30**:

- **M1 — Tick-Loop Spine** · `Done`
- **M2 — Device Models** · `Done`
- **M3 — Faults + Multi-Agent + Observability** · `Done`
  (six ADRs `Accepted`)
- **M4 — Protocol Adapters** · `In Progress`
  - Wave 0 — slice plan + trigger triage · `Done`
  - Wave 1 — `DeviceProtocolPort` foundation
    (ADR [0030](docs/plan/adr/0030-device-protocol-port-surface.md)
    `Provisional`) · `Done`
  - Wave 2 — MQTT adapter
    (ADR [0031](docs/plan/adr/0031-mqtt-adapter-profile.md)
    `Provisional`) · `Done`
  - Wave 3 — Modbus-TCP adapter (`pymodbus` wrapper + register
    schema + container smoke) · **active**
  - Waves 4–7 — OPC-UA / DNP3 / IEC 61850 / closure · `Pending`
- **M5 — UI + Demo** · `Pending`
- **M6 — Performance + Security + CI/CD** · `Pending`

**Test balance:** 1211 unit tests + 22 integration tests green.

**`make gates`** is 9-stage and cache-free green without override:
lint, format-check, `mypy --strict`, arch-check
(19 contracts: 7 `lint-imports` + 12 `tools/arch_check.py`),
test-unit, coverage (90 % line per module / 85 % critical / 96 %
total), critical-coverage, dep-audit, `# noqa` ban.

For per-wave commits, ADR pointers, and detail breakdown see the
slice plans under [`docs/plan/planning/`](docs/plan/planning/) and
the per-milestone detail table below.

### Status details

| Subsystem | Status | References |
| --- | --- | --- |
| Tick-Loop Spine (M1) | `Done` | [`done/M1-tick-loop-results.md`](docs/plan/planning/done/M1-tick-loop-results.md) |
| Device Models (M2) | `Done` | [`done/M2-devices-results.md`](docs/plan/planning/done/M2-devices-results.md) — Battery, PV, Load, GridConnection, SmartMeter + GridModel balance |
| Faults + Multi-Agent + Observability (M3) | `Done` | [`done/M3-results.md`](docs/plan/planning/done/M3-results.md) — Waves 0..7 closed, six M3 ADRs `Accepted` (detail rows below) |
| Fault Subsystem (M3 Waves 1+2) | `Done` | ADR [0022](docs/plan/adr/0022-fault-injection-protocol.md) + ADR [0025](docs/plan/adr/0025-fault-recovery-pattern.md); `BatteryFaultAdapter` + `GridFaultAdapter` with recovery logic |
| Multi-Agent Foundation (M3 Waves 3+4a) | `Done` | ADR [0023](docs/plan/adr/0023-agent-bus-protocol.md) + ADR [0026](docs/plan/adr/0026-agent-drain-registry-pattern.md); `Agent` protocol + `AgentMessageBus` + TickLoop `agents` registry |
| Multi-Agent concrete (M3 Wave 4b) | `Done` | ADR [0027](docs/plan/adr/0027-rule-based-agent-scenario-pattern.md); `RuleBasedAgent` with hybrid rules + scenario `agents` block + end-to-end demo (`tests/integration/scenarios/agents_demo.yaml`) |
| Observability Foundation (M3 Wave 5) | `Done` | ADR [0024](docs/plan/adr/0024-observability-port-trio.md) + ADR [0029](docs/plan/adr/0029-no-coverage-pragma-contract.md); `LogPort` / `MetricsPort` / `TracePort` + null-adapter trio |
| OTLP Adapter (M3 Wave 6) | `Done` | `adapters/driven/telemetry_otlp/` — gRPC log/metric/trace adapters + Compose `otel-collector` sibling + integration smoke + runbook [`docs/user/observability.md`](docs/user/observability.md) |
| Noqa hygiene (Slice 027) | `Done` | [`done/027-noqa-abbau.md`](docs/plan/planning/done/027-noqa-abbau.md) — 36 → 0 `# noqa` markers, `noqa-gate` added to `make gates` |
| Tick-Loop private-import contract (Slice 028) | `Done` | [`done/028-tick-loop-private-error-import-contract.md`](docs/plan/planning/done/028-tick-loop-private-error-import-contract.md) — 12th `tools/arch_check.py` contract |
| `DeviceProtocolPort` foundation (M4 Wave 1) | `Done` | [`done/M4-welle-1.md`](docs/plan/planning/done/M4-welle-1.md); ADR [0030](docs/plan/adr/0030-device-protocol-port-surface.md) `Provisional` — port + `*Error` hierarchy + TickLoop FIFO/LIFO lifecycle |
| MQTT adapter (M4 Wave 2) | `Done` | [`in-progress/M4-welle-2.md`](docs/plan/planning/in-progress/M4-welle-2.md); ADR [0031](docs/plan/adr/0031-mqtt-adapter-profile.md) `Provisional` — `protocol_mqtt/` 7-module package (paho-mqtt 2.x, per-target queue marshal) + Mosquitto integration smoke |
| Modbus-TCP adapter (M4 Wave 3) | `In Progress` | `pymodbus` wrapper + register schema + Modbus-server-container smoke |
| OPC-UA / DNP3 / IEC 61850 (M4 Waves 4–6) | `Pending` | Concrete adapters land in subsequent M4 waves |
| UI + Demo (M5) | `Pending` | Web UI, scenario editor, live telemetry stream |
| Performance + Security + CI/CD (M6) | `Pending` | 10,000-points/s benchmark, SBOM, multi-version matrix |

**AI-coding-agent briefing:** [`AGENTS.md`](AGENTS.md) — hard rules
(Docker-only, `# noqa` ban, `git mv` two-commit pattern,
Wave-Self-Close commit convention, language-/milestone-free
architecture spec).

## Build, Test, Lint

Individual gates for fast feedback loops:

```bash
make lint                # ruff check
make format-check        # ruff format --check
make typecheck           # mypy --strict (ADR 0005)
make arch-check          # import-linter + tools/arch_check.py (ADR 0002 §A-1)
make arch-check-imports  # import-linter only (7 forbidden-import contracts)
make arch-check-custom   # tools/arch_check.py only (12 custom checks)
make fullbuild           # gates + integration + runtime image build
                         # (see note above re: image-audit / krb5 CVE)
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
├── AGENTS.md                    ← AI-coding-agent briefing (hard rules + pointers)
├── README.md                    ← English main version (this document)
├── README.de.md                 ← German version
├── deploy/compose.yml           ← productive Compose stack + OTLP collector sibling (M3 Wave 6)
├── deploy/otel-collector-config.yaml ← collector config (gRPC :4317, debug + file exporters)
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
│       └── driven/              ← Postgres, RandomMT, OTLP, MQTT (M1 Waves 6b/6c + M3/M4)
├── tests/
│   ├── unit/                    ← pytest unit tests (1211 as of 2026-05-30, Welle-2 Stand)
│   ├── integration/             ← Compose-based integration tests (22 tests; OTLP + MQTT smoke incl.)
│   └── unit/_arch_check_*       ← architecture tests (7 lint-imports + 12 custom AC checks = 19 A-1)
├── tools/
│   ├── arch_check.py            ← AST/graph architecture checks (ADR 0002 §A-1)
│   ├── check_noqa.py            ← `# noqa` ban gate (9th A-1 gate, Slice 027)
│   ├── check_refs.py            ← Markdown link validator (`make docs-check`)
│   ├── wait_otel_collector.py   ← bounded liveness poll for distroless OTLP collector
│   └── diagnose_otlp_span_export.py ← OTLP debug matrix script (Trigger 029 pattern)
├── spec/
│   ├── lastenheft.md            ← normative requirements (GG-*)
│   └── architecture.md          ← architecture (GG-AR-*)
└── docs/
    ├── plan/
    │   ├── adr/                 ← Architecture Decision Records (0001..0031)
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
