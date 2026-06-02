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
make gates              # 10 mandatory gates (lint, format, typecheck,
                        # arch-check, tests, coverage, critical-coverage,
                        # dep-audit, noqa-gate, spdx-check)
make test-unit          # unit test suite (~1696 tests as of 2026-06-02,
                        # M5-Welle-4b closure + review-folge)
make test-integration   # Compose/testcontainers integration suite
                        # (51 passed + 4 skipped tests incl. OTLP, MQTT, Modbus,
                        # OPC-UA, DNP3, IEC-61850, M5-HTTP-API, M5-UI-Foundation,
                        # M5-Live-Telemetry, M5-Replay-Controls and M5-Alarms
                        # smokes + async pub/sub probe)
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
- **Enforced architecture.** 20 architectural contracts run on every
  `make arch-check`: 6 forbidden-import contracts via `lint-imports`
  plus 14 custom AST/graph checks in
  [`tools/arch_check.py`](tools/arch_check.py) (including
  `AC-ADAPTER-LIGHTWEIGHT`, `AC-OTLP-ADAPTER-NO-TIME`,
  `AC-TICK-LOOP-PRIVATE-RESUME-ERRORS`, and `AC-IEC61850-GPL-BOUNDARY`).
- **Ten-stage mandatory gate.** `make gates` runs lint, format-check,
  `mypy --strict`, arch-check, unit tests, coverage (90 % line per
  module / 85 % critical), critical-coverage, dependency audit,
  a `# noqa` ban, and `spdx-check` (GPL-3.0-only header lint for the
  IEC-61850 boundary) — all cache-free green without any local
  override.
- **ADR-driven decisions.** Every load-bearing decision is recorded as
  an [Architecture Decision Record](docs/plan/adr/); M1..M4 closure
  ADRs are `Accepted`, future-milestone wave ADRs land as `Provisional`
  and become `Accepted` at milestone closure.
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

As of **2026-06-02**:

- **M1 — Tick-Loop Spine** · `Done`
- **M2 — Device Models** · `Done`
- **M3 — Faults + Multi-Agent + Observability** · `Done`
  (six ADRs `Accepted`)
- **M4 — Protocol Adapters** · `Done`
  (six ADRs 0030..0035 `Accepted` 2026-06-01)
  - Wave 0 — slice plan + trigger triage · `Done`
  - Wave 1 — `DeviceProtocolPort` foundation
    (ADR [0030](docs/plan/adr/0030-device-protocol-port-surface.md)
    `Provisional`) · `Done`
  - Wave 2 — MQTT adapter
    (ADR [0031](docs/plan/adr/0031-mqtt-adapter-profile.md)
    `Provisional`) · `Done`
  - Wave 3 — Modbus-TCP adapter
    (ADR [0032](docs/plan/adr/0032-modbus-adapter-profile.md)
    `Provisional`) · `Done`
  - Wave 4 — OPC-UA adapter
    (ADR [0033](docs/plan/adr/0033-opcua-adapter-profile.md)
    `Provisional`) · `Done`
  - Wave 5a — DNP3 adapter (spike)
    (ADR [0034](docs/plan/adr/0034-dnp3-adapter-profile.md)
    `Provisional`) · `Done`
  - Wave 5b — IEC 61850 adapter (spike, GPL-isolated)
    (ADR [0035](docs/plan/adr/0035-iec61850-adapter-profile.md)
    `Provisional`) · `Done`
  - Wave 6a — cross-adapter hardening (OTel-span-wrap +
    AC-ADAPTER-LIGHTWEIGHT planted-violator test +
    `strict_bytes`) · `Done`
  - Wave 6b — IEC-61850 license/smoke hardening · `Done`
  - Wave 7 — closure · `Done`
- **M5 — UI + Demo** · `In Progress` 2026-06-01
  - Wave 0 — slice plan + trigger triage · `Done`
  - Wave 1 — HTTP API surface + ADR 0036/0037 sharpening · `Done`
  - Wave 2 — UI foundation (Jinja2 + vendored HTMX + Chart.js + StaticFiles mount + 2 page routes) · `Done`
  - Wave 3 — Live-Telemetry-Dashboard (NEW `TelemetryStreamPort` + `InMemoryTelemetryStream` + WS-Subscribe + Chart.js time-series + 6-state Quality-Marker + ADR 0038) · `Done`
  - Wave 4a — Replay-Controls + TickLoop-Wiring (NEW `RunStatus` + RunRepository extension + TickLoop-Control-Surface + `request(action)` + 2 endpoint wirings + `TickLoopRegistry` + `DemoTickLoopDriver` + control UI + ADR 0039) · `Done`
  - Wave 4b — Alarms (NEW unified `Alarm` domain type + mapper family in `core/simulation/alarm_mappers.py` + `TickResult.emitted_alarms` + TickLoop drain hook + NEW `AlarmStreamPort` + `InMemoryAlarmStream` + `AlarmHistoryBuffer` + REST + WS endpoints + alarms UI page + ADR 0040; resolves ADR-0014-§6 forward pointer "AlarmSinkPort kommt mit M3" driving-side anteil) · `Done`
  - Wave 5 — Demo pipeline (canonical demo YAML + `make demo` + `python -m grid_gym demo` + lifespan demo path via `GRID_GYM_DEMO_SCENARIO_PATH` + `docs/user/demo.md` + integration smoke) · `In Progress` 2026-06-02 (slice doc `155c421` — `GG-DEMO-001..005+008` + `GG-DEMO-007` eng inkludiert; `GG-DEMO-006` deferiert auf Welle 6)
- **M6 — Performance + Security + CI/CD** · `Pending`

**Test balance (state after M5 Wave 4b closure 2026-06-02):**
~1696 unit tests + 51 integration tests passed + 4 skipped (1681
post-C3 + 15 from the review follow-up). The
4 skipped tests are the **2c mock-only fallback** for the
IEC-61850 in-process `IedServer` smoke (ADR 0035 §2.5;
trigger 009). Per-wave test increments + rationale live
canonically in the slice docs under
[`docs/plan/planning/`](docs/plan/planning/).

**`make gates`** is 10-stage and cache-free green without override:
lint, format-check, `mypy --strict`, arch-check
(20 contracts: 6 `lint-imports` + 14 `tools/arch_check.py`),
test-unit, coverage (90 % line per module / 85 % critical),
critical-coverage, dep-audit, `# noqa` ban, `spdx-check`.

For per-wave commits, ADR pointers, and detail breakdown see the
slice plans under [`docs/plan/planning/`](docs/plan/planning/) and
the ADR index under
[`docs/plan/adr/README.md`](docs/plan/adr/README.md).

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
├── .github/workflows/ci.yml     ← CI: 4 mandatory gates (Trigger 025)
├── Dockerfile, Makefile, pyproject.toml, uv.lock, alembic.ini, .python-version
│                                ← build/gate/dependency layer (ADR 0002 §6.1; alembic for M1 Wave 6c Postgres migrations)
├── LICENSE + LICENSES/GPL-3.0.txt
│                                ← MIT default + GPL-3.0-only for the IEC-61850 boundary (ADR 0035 Decision I-f, M4 Waves 5b/6b)
├── README.md + README.de.md + CHANGELOG.md + CONTRIBUTING.md + AGENTS.md
│                                ← project docs + dual-license policy + AI-coding-agent briefing
├── deploy/
│   ├── compose.yml              ← productive Compose stack + OTLP collector sibling (M3 Wave 6)
│   └── otel-collector-config.yaml ← collector config (gRPC :4317, debug + file exporters)
├── harness/                     ← agent harness contracts: README + roles + review + verification + replay
├── spec/
│   ├── lastenheft.md            ← normative requirements (GG-*)
│   ├── architecture.md          ← architecture (GG-AR-*)
│   └── protocol_profiles.md     ← per-protocol adapter profile index (M4 Wave 6a)
├── src/grid_gym/
│   ├── hexagon/
│   │   ├── core/
│   │   │   ├── agents/          ← Agent protocol + AgentMessageBus + RuleBasedAgent (M3 Waves 3+4a+4b)
│   │   │   ├── devices/         ← battery/, pv/, load/, grid_connection/, smart_meter/ (M2)
│   │   │   ├── domain/          ← frozen dataclasses (Command, Event, Alarm, ScenarioFault, ...)
│   │   │   ├── faults/          ← Battery + GridFaultAdapter (M3 Wave 2)
│   │   │   ├── grid_model/      ← balance model + LoadEvent/LoadProfile (M2 Wave 5)
│   │   │   ├── replay/          ← replay sample codec (M1 Wave 5)
│   │   │   ├── scenario/        ← YAML loader + validator (M1 Wave 5)
│   │   │   ├── serialization/   ← canonical_json (M1 Wave 0a, Trigger 014)
│   │   │   └── simulation/      ← TickLoop + scheduler + alarm_mappers (M5 Wave 4b)
│   │   └── ports/
│   │       ├── driven/          ← Clock, Random, Fault, RunRepository, Observability (Log/Metrics/Trace), DeviceProtocol (M4 Wave 1)
│   │       └── driving/         ← TelemetryStream (M5 Wave 3), AlarmStream (M5 Wave 4b)
│   └── adapters/
│       ├── driving/
│       │   ├── http_api/        ← FastAPI app + REST + WebSocket + composition roots (M5 Waves 1/4a/4b)
│       │   └── ui/              ← Jinja2 templates + vendored HTMX + Chart.js + StaticFiles (M5 Wave 2)
│       └── driven/
│           ├── persistence_postgres/    ← Postgres RunRepository + alembic migrations (M1 Wave 6c)
│           ├── random_mt/               ← MersenneTwisterRandomPort (M1 Wave 2)
│           ├── observability_null/      ← Null Log/Metrics/Trace fallback (M3 Wave 5)
│           ├── telemetry_otlp/          ← OTLP gRPC adapter (M3 Wave 6, ADR 0024)
│           ├── telemetry_stream_inmemory/ ← InMemoryTelemetryStream + DemoTelemetryGenerator (M5 Wave 3)
│           ├── alarm_stream_inmemory/   ← InMemoryAlarmStream + AlarmHistoryBuffer (M5 Wave 4b)
│           ├── protocol_mqtt/           ← paho-mqtt (M4 Wave 2, ADR 0031)
│           ├── protocol_modbus/         ← pymodbus (M4 Wave 3, ADR 0032)
│           ├── protocol_opcua/          ← asyncua + OpcuaLoopThread async-bridge (M4 Wave 4, ADR 0033)
│           ├── protocol_dnp3/           ← nfm-dnp3 productive + dnp3-outstation dev-only (M4 Wave 5a, ADR 0034)
│           ├── protocol_iec61850/       ← pyiec61850-ng GPLv3-isolated optional extra (M4 Wave 5b, ADR 0035 Decision I-f)
│           └── _protocol_otel_wrap.py   ← OtelSpanWrappedDeviceProtocolPort cross-adapter wrapper (M4 Wave 6a)
├── tests/
│   ├── unit/                    ← pytest unit tests (1696 as of 2026-06-02, M5-Welle-4b closure + review-folge)
│   ├── integration/             ← Compose-based integration tests (51 passed + 4 skipped; OTLP + MQTT + Modbus + OPC-UA + DNP3 + IEC-61850 (mock-only fallback) + M5-HTTP-API + UI-Foundation + Live-Telemetry + Replay-Controls + Alarms smokes incl.)
│   └── unit/_arch_check_*       ← architecture tests (6 lint-imports + 14 custom AC checks = 20 A-1; AC-NO-IO-MOD enforced in both tools, counted once)
├── tools/
│   ├── arch_check.py            ← AST/graph architecture checks (ADR 0002 §A-1)
│   ├── check_noqa.py            ← `# noqa` ban gate (Slice 027)
│   ├── check_spdx.py            ← SPDX header lint for the GPL-3.0-only boundary (M4 Wave 6b)
│   ├── check_refs.py            ← Markdown link validator (`make docs-check`)
│   ├── check_core_determinism.py ← core determinism sweep
│   ├── wait_otel_collector.py   ← bounded liveness poll for distroless OTLP collector
│   └── diagnose_otlp_span_export.py ← OTLP debug matrix script (Trigger 029 pattern)
└── docs/
    ├── plan/
    │   ├── adr/                 ← Architecture Decision Records (0001..0040)
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

This project is **MIT-licensed** by default — see [`LICENSE`](LICENSE).

**Exception: GPLv3-isolated IEC-61850 adapter** (M4 Wave 5b, ADR
[0035](docs/plan/adr/0035-iec61850-adapter-profile.md) Decision I-f):
the sub-paths `src/grid_gym/adapters/driven/protocol_iec61850/`,
`tests/unit/adapters/driven/protocol_iec61850/`,
`tests/integration/test_iec61850_*.py`, and
`tests/integration/fixtures/iec61850/` link against the GPLv3-
licensed [`pyiec61850-ng`](https://pypi.org/project/pyiec61850-ng/)
/ libiec61850 library and are therefore distributed under
**GPL-3.0-only**. The GPLv3 text is in [`LICENSES/GPL-3.0.txt`](LICENSES/GPL-3.0.txt).

The `pyiec61850-ng` library itself is shipped as an **optional
extra**. The default install ships only MIT-licensed code; users
opt into the IEC-61850 adapter — and the GPL distribution terms
that come with it — by explicitly installing the extra:

```bash
pip install grid-gym                  # MIT-only
pip install 'grid-gym[iec61850]'      # MIT + GPLv3 IEC-61850 adapter
```
