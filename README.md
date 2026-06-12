# grid-gym

**English** | [Deutsch](README.de.md)

`grid-gym` is an open-source platform for the deterministic simulation,
validation, and analysis of electrical energy systems. It models grid
connection points, PV arrays, battery storage, smart meters, and load
profiles with reproducible tick-loop execution, snapshot/replay, fault
injection, and protocol adapters for field-bus telemetry.

> **Simulation only — not approved for production grid control.**
> `grid-gym` is a simulation, replay, and validation environment.
> Protocol adapters (MQTT, Modbus, OPC-UA, DNP3, IEC-61850) are
> intended to drive simulated devices or test rigs, not real plants
> (`GG-SAFE-007`, `GG-NONGOAL-001`).

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
make test-unit          # unit test suite (~1722 tests as of 2026-06-04,
                        # M5-Welle-4b closure + review-folge)
make test-integration   # Compose/testcontainers integration suite
                        # (80 passed + 4 skipped tests incl. OTLP, MQTT, Modbus,
                        # OPC-UA, DNP3, IEC-61850, M5-HTTP-API, M5-UI-Foundation,
                        # M5-Live-Telemetry, M5-Replay-Controls and M5-Alarms
                        # smokes + async pub/sub probe)
```

Example YAML scenarios live under
[`tests/integration/scenarios/`](tests/integration/scenarios/).

The repository is **Docker-only**: the host only needs `docker` and
`make`. No local Python or `uv` installation is required.

`make fullbuild` runs the full closure pipeline including
`image-audit` (Trivy) and a Compose smoke test. The mandatory
development gate is `make gates`.

> Vulnerability audit ignores are sourced from
> `deploy/security/vulnignore.yaml` (audit source-of-truth with
> mandatory `id`/`reason`/`expires`/`scope` fields) and rendered
> to `deploy/security/.trivyignore` via `make render-trivyignore`
> (see ADR 0044). Expired entries break the build, forcing
> maintenance without external reminders. Current single entry:
> CVE-2026-42504 (Go stdlib MIME header DoS) in the pinned
> `otel/opentelemetry-collector-contrib:0.153.0` sibling image
> with `expires: 2026-06-20` as a temporary deferral. The
> upstream resolution lands with OTel collector >0.153.0 built
> against go1.26.4+ (tracked in `docs/plan/planning/open/
> 033-otel-collector-go-stdlib-cve-bump.md`; trigger stays open
> as the canonical stable-watch).

A release is triggered by pushing a `v*.*.*` git tag (or via
manual `workflow_dispatch` in the GitHub UI). The release workflow
publishes a container image to GHCR (`ghcr.io/<owner>/grid-gym:<tag>`)
plus five release-asset files: SBOM (CycloneDX-JSON via Syft against
the runtime image), test reports (JUnit-XML), coverage HTML tarball,
OpenAPI specification (JSON), and the demo acceptance document.
Local SBOM generation: `make sbom` (writes `artifacts/sbom-<version>.cdx.json`;
version defaults to `pyproject.toml`).

CI runs six GitHub-Actions workflows: `ci.yml` (lint / format-check /
typecheck / arch-check; the four mandatory Slice-025 gates), `tests.yml`
(test-unit on a Python 3.13/3.14 matrix + test-integration), `coverage.yml`
(coverage-gate 90/85 line/branch + coverage-gate-critical 90% critical
domain), `dep-audit.yml` (pip-audit), `fullbuild.yml` (`make fullbuild`
on relevant paths + workflow_dispatch fallback; covers image-audit and
the Compose smoke test), and `release.yml` (tag-push or workflow_dispatch).

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

As of **2026-06-12**:

- **M1..M7 · `Done`** — **the MVP is delivered** (49 ADRs
  `Accepted` across M1..M7, plus ADR 0050/0051 `Proposed`). Closure
  artefacts:
  [`docs/plan/planning/done/M7-results.md`](docs/plan/planning/done/M7-results.md)
  +
  [`docs/plan/planning/done/M6-results.md`](docs/plan/planning/done/M6-results.md).
- **M7 — MVP completion** · `Done` (2026-06-12; Welle 0..X). All
  four `GG-MVP-*` items (replay-source integration `GG-MVP-002`,
  acceptance CLI `make accept` `GG-MVP-003`) and all four
  `GG-SAFE-001..004` MUSS IDs are productive. Five M7 ADRs
  (0047/0048/0049/0052/0053) `Accepted` at Welle-X closure;
  ADR 0050/0051 stay `Proposed` (own lifecycle conditions).
- **Post-MVP mode: trigger watch** — no successor milestone is
  auto-opened. Open triggers 033 (OTel-collector CVE stable watch),
  037 (multi-node deployment), 038/039/040 (demand-driven) plus the
  trigger-gated backlog carry documented activation conditions; two
  prepared `planning/next/` plans (041 AC-ADAPTER-PURE bridge
  retirement, 042 fault-engine naming — implementation slices for
  ADR 0050/0051) await a mandate. A new milestone opens on trigger
  activation or stakeholder mandate.

**Test balance:** 139 integration passed + 4 skipped (remaining
skips are IEC-61850-on-Python-3.13 only, covered by the dedicated
`make test-iec61850` stage per ADR 0046) at M7 closure (2026-06-12).
`make gates` 10-stage cache-free green without override;
`make fullbuild` incl. `accept-pin-check` green.

**Pointers:** demo acceptance steps `GG-DEMO-008` →
[`docs/user/gg-demo-008-abnahme.md`](docs/user/gg-demo-008-abnahme.md);
quality-pipeline audit `GG-SAFE-001..004` →
[`docs/user/safe-001-004-quality-pipeline.md`](docs/user/safe-001-004-quality-pipeline.md);
ADRs → [`docs/plan/adr/README.md`](docs/plan/adr/README.md);
AI-agent briefing → [`AGENTS.md`](AGENTS.md).

## Build, Test, Lint

Individual gates for fast feedback loops:

```bash
make lint                # ruff check
make format-check        # ruff format --check
make typecheck           # mypy --strict (ADR 0005)
make arch-check          # import-linter + tools/arch_check.py (ADR 0002 §A-1)
make arch-check-imports  # import-linter only (7 forbidden-import contracts)
make arch-check-custom   # tools/arch_check.py only (12 custom checks)
make fullbuild           # gates + integration + runtime image + image-audit + compose smoke
make perf                # GG-RT-004 + GG-RT-005 SOLLTE: pytest-benchmark vs tests/perf/baseline.json (20% Median-Drift; ADR 0041; opt-in `--extra perf`; tick-loop 100 devices x 10k ticks + telemetry-port 10k publish/s with payloads ≤256 byte)
# GG-RT-001 MUSS Backpressure-Healthcheck: GET /runs/{id}/healthcheck → JSON with tick_duration_ms_p50/p95, missed_ticks_count, backpressure_status (Welle-4b-c).
make perf-baseline-update # maintainer-only: regenerate tests/perf/baseline.json
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

## Optional / Roadmap Extensions

The MVP scope above is implemented; the following extensions are
intentionally held out of the MVP and tracked as optional
additions in the normative requirements ([`spec/lastenheft.md`](spec/lastenheft.md)):

- additional time-series storage adapters
  (TimescaleDB `GG-PERSIST-006`, InfluxDB `GG-PERSIST-007`)
- hardware-in-the-loop (HIL) integration `GG-TEST-004`
- model-predictive control (MPC) agents `GG-FUTURE-001`
- reinforcement-learning (RL) agents `GG-FUTURE-002`

## Project Structure

```text
.
├── .github/workflows/ci.yml     ← CI: 4 mandatory gates
├── AGENTS.md, CHANGELOG.md, CONTRIBUTING.md, README.de.md, README.md
│                                ← project docs + dual-license policy + AI-agent briefing
├── Dockerfile, Makefile, alembic.ini, pyproject.toml, uv.lock, .python-version
│                                ← build / gate / dependency layer (ADR 0002 §6.1)
├── LICENSE + LICENSES/          ← MIT default + GPL-3.0-only for the IEC-61850 boundary
├── deploy/
│   ├── compose.yml              ← productive Compose stack + OTLP collector sibling
│   └── otel-collector-config.yaml ← collector config (gRPC :4317)
├── docs/
│   ├── archive/                 ← discarded / historical drafts
│   ├── plan/
│   │   ├── adr/                 ← Architecture Decision Records (0001..0045)
│   │   └── planning/
│   │       ├── done/            ← completed slices + closure notes
│   │       ├── in-progress/     ← active roadmap + slice plans
│   │       ├── next/            ← planned but not yet active
│   │       └── open/            ← trigger watch, open follow-ups
│   └── user/                    ← user-/operator-facing docs (code review etc.)
├── harness/                     ← agent harness (roles, review, verification, replay)
├── spec/
│   ├── architecture.md          ← architecture (GG-AR-*)
│   ├── lastenheft.md            ← normative requirements (GG-*)
│   └── protocol_profiles.md     ← per-protocol adapter profile index
├── src/grid_gym/
│   ├── adapters/
│   │   ├── driven/
│   │   │   ├── _protocol_otel_wrap.py     ← OtelSpanWrappedDeviceProtocolPort wrapper
│   │   │   ├── alarm_stream_inmemory/     ← InMemoryAlarmStream + AlarmHistoryBuffer
│   │   │   ├── observability_null/        ← Null Log / Metrics / Trace fallback
│   │   │   ├── persistence_postgres/      ← Postgres RunRepository + alembic migrations
│   │   │   ├── protocol_dnp3/             ← nfm-dnp3 productive + dnp3-outstation dev-only
│   │   │   ├── protocol_iec61850/         ← pyiec61850-ng GPLv3-isolated optional extra
│   │   │   ├── protocol_modbus/           ← pymodbus
│   │   │   ├── protocol_mqtt/             ← paho-mqtt
│   │   │   ├── protocol_opcua/            ← asyncua + OpcuaLoopThread async bridge
│   │   │   ├── random_mt/                 ← MersenneTwisterRandomPort
│   │   │   ├── telemetry_otlp/            ← OTLP gRPC adapter (log / metric / trace exporters)
│   │   │   └── telemetry_stream_inmemory/ ← InMemoryTelemetryStream + DemoTelemetryGenerator
│   │   └── driving/
│   │       ├── http_api/        ← FastAPI app + REST + WebSocket + composition roots
│   │       └── ui/              ← Jinja2 templates + vendored HTMX + Chart.js + StaticFiles
│   └── hexagon/
│       ├── core/
│       │   ├── agents/          ← Agent protocol + AgentMessageBus + RuleBasedAgent
│       │   ├── devices/         ← battery/, grid_connection/, load/, pv/, smart_meter/
│       │   ├── domain/          ← frozen dataclasses (Command, Event, Alarm, ScenarioFault, ...)
│       │   ├── faults/          ← Battery + GridFaultAdapter
│       │   ├── grid_model/      ← balance model + LoadEvent / LoadProfile
│       │   ├── replay/          ← replay sample codec
│       │   ├── scenario/        ← YAML loader + validator
│       │   ├── serialization/   ← canonical_json
│       │   └── simulation/      ← TickLoop + scheduler + alarm_mappers
│       └── ports/
│           ├── driven/         ← Clock, DeviceProtocol, Fault, Observability, Random, RunRepository
│           └── driving/        ← AlarmStream, TelemetryStream
├── tests/
│   ├── integration/             ← Compose-based integration tests (80 passed + 4 skipped)
│   ├── unit/                    ← pytest unit tests (1722 as of 2026-06-04)
│   └── unit/_arch_check_*       ← architecture tests (6 lint + 14 custom = 20 contracts)
└── tools/
    ├── arch_check.py                ← AST / graph architecture checks (ADR 0002 §A-1)
    ├── check_core_determinism.py    ← core determinism sweep
    ├── check_noqa.py                ← `# noqa` ban gate
    ├── check_refs.py                ← Markdown link validator (`make docs-check`)
    ├── check_spdx.py                ← SPDX header lint for the GPL-3.0-only boundary
    ├── diagnose_otlp_span_export.py ← OTLP debug matrix script
    └── wait_otel_collector.py       ← bounded liveness poll for distroless OTLP collector
```

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
