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
make test-unit          # unit test suite (~1626 tests as of 2026-06-01,
                        # M5-Welle-3 closure)
make test-integration   # Compose/testcontainers integration suite
                        # (49 passed + 4 skipped tests incl. OTLP, MQTT, Modbus,
                        # OPC-UA, DNP3, IEC-61850, M5-HTTP-API, M5-UI-Foundation
                        # and M5-Live-Telemetry smokes + async pub/sub probe)
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

As of **2026-06-01**:

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
  - Wave 4 — Replay-Controls + Alarms · `Pending` (next active slice)
- **M6 — Performance + Security + CI/CD** · `Pending`

**Test balance (state after M5 Wave 3 closure 2026-06-01):**
~1626 unit tests + 49 integration tests passed + 4 skipped. The
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
| `DeviceProtocolPort` foundation (M4 Wave 1) | `Done` | [`done/M4-welle-1.md`](docs/plan/planning/done/M4-welle-1.md); ADR [0030](docs/plan/adr/0030-device-protocol-port-surface.md) `Accepted` — port + `*Error` hierarchy + TickLoop FIFO/LIFO lifecycle |
| MQTT adapter (M4 Wave 2) | `Done` | [`done/M4-welle-2.md`](docs/plan/planning/done/M4-welle-2.md); ADR [0031](docs/plan/adr/0031-mqtt-adapter-profile.md) `Accepted` — `protocol_mqtt/` 7-module package (paho-mqtt 2.x, per-target queue marshal) + Mosquitto integration smoke |
| Modbus-TCP adapter (M4 Wave 3) | `Done` | [`done/M4-welle-3.md`](docs/plan/planning/done/M4-welle-3.md); ADR [0032](docs/plan/adr/0032-modbus-adapter-profile.md) `Accepted` — `protocol_modbus/` 5-module package (pymodbus 3.x sync client, no thread marshal needed — Decision M-c direct-sync; 5 datatypes, FC03/FC10 defaults with FC04/FC06 overrides) + in-process pymodbus-server integration smoke for the default profile. Follow-up [`031`](docs/plan/planning/done/031-modbus-adapter-review-folge.md) implemented the FC06 multi-register guard, read/write error taxonomy, and deliberate smoke boundary. Trigger-006-Re-Eval (`mypy --strict-bytes`) is positive; activation remains a separate follow-up. |
| OPC-UA adapter (M4 Wave 4) | `Done` | [`done/M4-welle-4.md`](docs/plan/planning/done/M4-welle-4.md); ADR [0033](docs/plan/adr/0033-opcua-adapter-profile.md) `Accepted` — `protocol_opcua/` 6-module package (asyncua 1.2b2; **first async-only stack** in the repo with a dedicated `OpcuaLoopThread` running an asyncio event loop in a daemon thread — Decision O-b; 8 datatypes (Boolean/Int16/UInt16/Int32/UInt32/Float/Double/String), polling read + direct write, Subscription-Pfad deferred to Wave 6) + in-process `asyncua.Server` integration smoke parameterised over all 8 datatypes (Decision O-e; LGPL-3.0 library-linking, avoids `open62541/open62541` MPL-2.0 container drama). asyncua pin `>=1.2b2,<2.0` accepts pre-release upgrades and ships the Python-3.14 forward-reference fix missing in 1.1.8. Follow-up [`032`](docs/plan/planning/done/032-opcua-adapter-review-folge.md) addressed 6 HIGH + 11 MEDIUM code-review findings (lifecycle-lock for `OpcuaLoopThread`, port exception filter, Quality.INVALID for string reads, float32 quantisation). |
| DNP3 adapter (M4 Wave 5a, spike) | `Done` | [`done/M4-welle-5a.md`](docs/plan/planning/done/M4-welle-5a.md); ADR [0034](docs/plan/adr/0034-dnp3-adapter-profile.md) `Accepted` — `protocol_dnp3/` 5-module package (nfm-dnp3 1.0.x as master, Pure-Python + MIT, **sync API** so no loop thread needed — Decision D-b direct-sync analogous to Modbus M-c; 4 group/variation combinations {(1,1), (1,2), (30,1), (30,5)} for binary inputs + 32-bit int/float analog inputs; Class-0 integrity-poll read with result-filter-by-index — Decision D-d, `read_analog_inputs(start, stop)` deliberately not used due to qualifier-0x01 wire-incompat with dnp3-outstation; write path is Wave-5a anti-scope, throws `Dnp3PortWriteNotImplementedError`) + in-process `dnp3_outstation.AsyncOutstation` integration smoke (Decision D-e; **two-library setup** — `nfm-dnp3` as production master in `[project] dependencies`, `dnp3-outstation` as test-only sibling in `[dependency-groups.dev]`; wire-compat verified via C1 probe + C2 smoke). C2 library-bug-find: `AnalogInput.__repr__` shows `idx=0` but actual field is `index` — fixed in `_port._find_point`. |
| IEC-61850 adapter (M4 Wave 5b, spike, GPL-isolated) | `Done` | [`in-progress/M4-welle-5b.md`](docs/plan/planning/in-progress/M4-welle-5b.md); ADR [0035](docs/plan/adr/0035-iec61850-adapter-profile.md) `Accepted` — `protocol_iec61850/` 5-module package (pyiec61850-ng 1.6.x as the single library covering both `MMSClient` and in-process `IedServer`, **sync API** so no loop thread needed — Decision I-b direct-sync analogous to Modbus M-c and DNP3 D-b; 4 datatypes (bool/int32/float/string) × FC allow-list `{MX,ST,SP,CF,DC}` with adapter-default `MX`; per-target `MMSClient.read_value(reference, fc)` — Decision I-d, RCB subscription + GOOSE deferred to Wave 6; write path is Wave-5b anti-scope, throws `Iec61850PortWriteNotImplementedError`) + in-process `IedServer(model_path=fixture)` integration smoke under **2c mock-only fallback** active (Decision I-e + I-f; **first GPL-isolated sub-module** in the repo via `SPDX-License-Identifier: GPL-3.0-only` per file + `LICENSES/GPL-3.0.txt` + LICENSE notice + `pyiec61850-ng` as opt-in `pip install grid-gym[iec61850]` extra, not in `[project] dependencies`; probe-run on Python 3.12 verified MMSClient↔IedServer roundtrip with the libiec61850-native CFG fixture, but grid-gym Docker on Python 3.14 segfaults inside `_pyiec61850.so` SWIG layer — DoD satisfied via 18 mock-client unit tests, Wave-6 sharpening paths: Python-3.12-runtime / library upgrade / wheel rebuild). Probe-run library findings 2026-06-01: reference convention concatenates MODEL+LD names without separator (`simpleIO`+`GenericIO`→`simpleIOGenericIO`), MMSClient FC argument accepts two-letter string, IedServer requires `model_path` else `start()` raises `ModelError`. |
| Cross-adapter hardening (M4 Wave 6a) | `Done` | [`done/M4-welle-6a.md`](docs/plan/planning/done/M4-welle-6a.md) (self-close-move `d1cb65d`; slice 034 review-folge `bde8fdb` addresses 15 findings) — OTel-span-wrap via `OtelSpanWrappedDeviceProtocolPort` composition wrapper for all 5 adapters (ADR 0024 §4.5; standard attributes `adapter_type`/`target`/`operation`/`latency_ms`; adapter code diff: zero), adapter profile index under [`spec/protocol_profiles.md`](spec/protocol_profiles.md) with 5 entries + ADR links + Lastenheft IDs, Lastenheft §16 implementation matrix synced to `✅ M4` × 5, architecture §8.2 sharpened with OTel-wrap pattern. AC-ADAPTER-LIGHTWEIGHT planted-violator property test (Wave-1-§7 follow-up closure) verifies arch-check filter correctness. Trigger 006 closure: `[tool.mypy] strict_bytes = true` activated. compose.yml header consolidated into 2 sibling tables (container + in-process) with license columns. Trigger 004 deferred to M5/M6. |
| M4 closure (Wave 7) | `Done` | [`done/M4-welle-7.md`](docs/plan/planning/done/M4-welle-7.md) + [`done/M4-results.md`](docs/plan/planning/done/M4-results.md) — 6 M4-ADRs (0030..0035) `Provisional → Accepted` (C1 `d2071f0`); `done/M4-results.md` with wave table / acceptance evidence (10 A-1 gates, 1584 unit + 35+4 integration, 20 contracts) / per-wave reviews / S-1..S-6 verification / heritage section (C2 `0c644f0`); roadmap M4 → `Done`, M5 as next active slice (C3, this commit). `make fullbuild` pre-existing red due to krb5 CVE drift since M3 Wave-7 `c61ab0d` — Base-Image-Bump as M5-Wave-0 trigger. IEC-61850 in-process smoke remains under 2c mock-only fallback with trigger 009. |
| IEC 61850 license/smoke hardening (M4 Wave 6b) | `Done` | [`done/M4-welle-6b.md`](docs/plan/planning/done/M4-welle-6b.md) (self-close-move `bf23458`) — SPDX-License-Identifier lint via new `tools/check_spdx.py` (10th A-1 gate `make spdx-check`; 11 GPL-boundary files lint-clean), new arch_check contract `AC-IEC61850-GPL-BOUNDARY` (14th arch_check contract; 19 → 20 contracts kept; AST import scan over MIT code), new `CONTRIBUTING.md` with dual-license policy (default MIT, GPL-3.0-only opt-in for `protocol_iec61850/*` boundary), IedServer-smoke reactivation probe path-A finding (PyPI `pyiec61850-ng 1.6.1.2` identical to Wave 5b, no cp314-manylinux wheel) → path C active with concrete trigger 009 (passive: library publishes cp314-wheel; active: separate slice for Dockerfile multi-Python test stage), plus Slice 034 F13 follow-up (`_is_adapter_lightweight_path` extended to flat-file `_protocol_*.py` cross-adapter helpers under `adapters/driven/`). |
| UI + Demo (M5) | `In Progress` 2026-06-01 | Web UI, scenario editor, live telemetry stream. **Wave 0 done 2026-06-01** ([`done/M5-welle-0.md`](docs/plan/planning/done/M5-welle-0.md)) — slice plan + trigger triage + pre-M5-Wave-0 sondierungs-ADR [0036](docs/plan/adr/0036-ui-stack-choice.md) `Provisional` (Option 1: FastAPI + HTMX + Jinja2 + Chart.js). **Wave 1 done 2026-06-01** ([`done/M5-welle-1.md`](docs/plan/planning/done/M5-welle-1.md)) — HTTP API surface produktiv (5 REST + 1 WebSocket endpoint under `src/grid_gym/adapters/driving/http_api/` in 4 new modules with APIRouter splitting due to `AC-NO-GOD-UTILS`; Pydantic schemas with `ErrorResponse` standard format per `GG-API-004`); ADR [0036](docs/plan/adr/0036-ui-stack-choice.md) `Provisional` with HTMX-FastAPI smoke probe evidence `9c20dad`; NEW ADR [0037](docs/plan/adr/0037-http-api-surface-pattern.md) `Provisional` — Decision API-1 (`POST /runs/{id}/control` with action body), Decision API-2 (no separate `UICommandPort`; UI uses HTTP API directly), Decision API-3 (roadmap typo `GG-AR-PORT-DRG-002` discarded). +16 unit + 2 integration tests; 10/10 A-1 gates green. **Wave 2 done 2026-06-01** ([`done/M5-welle-2.md`](docs/plan/planning/done/M5-welle-2.md)) — UI foundation produktiv: Decision 2 final fixiert auf `src/grid_gym/adapters/driving/ui/` (hexagonal architecture consistency); 6 Jinja2 templates incl. 2 HTMX partials (`base.html` + `navigation.html` + `demo.html`/`_demo_content.html` + `health.html`/`_health_content.html`); 3 vendored static assets HTMX 2.0.9 (51 KB, MIT) + Chart.js 4.5.1 UMD build (208 KB, MIT) + `style.css` skeleton + `VENDORED.md` with SHA256 + upstream URLs + maintenance instructions; `jinja2>=3.1,<4.0` new runtime dep with `AC-PORTS-NO-FW` + `AC-NO-FW` forbidden-list extension; `StaticFiles` mount on `/static` + `ui_router` with 2 page-routes (`GET /` demo-hello + `GET /ui/health`); HTMX-partial pattern via `HX-Request` header inspection. +10 unit + 2 integration tests; 10/10 A-1 gates green. **Wave 3 done 2026-06-01** ([`in-progress/M5-welle-3.md`](docs/plan/planning/in-progress/M5-welle-3.md)) — Live-Telemetry-Dashboard produktiv: NEW ADR [0038](docs/plan/adr/0038-telemetry-stream-port.md) `Provisional` for `TelemetryStreamPort` (driving port with `subscribe(run_id) -> AsyncIterator[TelemetryPoint]` + `publish()` + bounded `asyncio.Queue` Drop-Oldest backpressure + `try/finally` cleanup; closes M5-Welle-0 Decision 11); NEW `InMemoryTelemetryStream` driven adapter with `DemoTelemetryGenerator` async stub-producer (4 points/tick: battery-power/soc + grid-power/voltage; quality `stale` 2 of 50 ticks); WS-endpoint `WS /runs/{run_id}/telemetry` switched from Welle-1 counter-stub to Subscribe-pattern with `run_id` filter (ADR 0038 §3.1); NEW UI page `GET /runs/{run_id}/dashboard` with HTMX `hx-ext="ws"` bridge + Chart.js time-series glue (3 datasets, MAX_POINTS=200 sliding window) + 6 CSS quality-marker classes (`quality-ok`/`stale`/`invalid`/`nan`/`missing`/`fault_injected`); FastAPI lifespan-hook for demo-generator task lifecycle. Lastenheft acceptance: `GG-API-002` (WebSocket-Telemetry with `run_id`/`simulation_time_ms`/`sequence`/payload) + `GG-UI-002` (Live-Telemetry) + `GG-UI-003` (Time-series for 3 metrics) + `GG-UI-009` (6 quality markers visible). +16 unit + 6 integration tests; 10/10 A-1 gates green. |
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
│   ├── unit/                    ← pytest unit tests (1462 as of 2026-05-31, M4-Welle-5a closure)
│   ├── integration/             ← Compose-based integration tests (35 tests; OTLP + MQTT + Modbus + OPC-UA + DNP3 smoke incl.)
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
