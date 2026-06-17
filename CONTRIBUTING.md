# Contributing to grid-gym

Welcome — and thank you for your interest in contributing.
This document covers the **license policy** that contributors
need to be aware of, plus the **development workflow** that
all changes go through. For architectural conventions and the
A-1 contracts that arch-check enforces, see
the [ADR index](docs/plan/adr/README.md)
and the [`AGENTS.md`](AGENTS.md) briefing.

---

## License Policy (Dual-License)

grid-gym is distributed under a **dual-license** layout. The
default is MIT; one explicitly-isolated sub-module is
GPL-3.0-only. **This affects you whenever you touch files
under the GPL-isolated paths** (listed below).

### Default: MIT

All contributions outside the GPL-isolated paths are
**MIT-licensed**. By submitting a contribution, you agree
that your contribution may be redistributed under the MIT
License as documented in [`LICENSE`](LICENSE).

You do **not** need to add a per-file SPDX header for
MIT-licensed contributions — the repo-level `LICENSE` file
covers them.

### Exception: GPL-3.0-only

The following sub-paths link against the GPLv3-licensed
`pyiec61850-ng` / `libiec61850` library (M4 Welle 5b,
[ADR 0035 §I-f](docs/plan/adr/0035-iec61850-adapter-profile.md))
and are therefore distributed under **GPL-3.0-only**:

| Sub-Path                                                                                    | Note                                                                          |
| ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `src/grid_gym/adapters/driven/protocol_iec61850/`                                           | Production adapter implementation                                             |
| `tests/unit/adapters/driven/protocol_iec61850/`                                             | Adapter unit tests (mock-client)                                              |
| `tests/integration/test_iec61850_*.py`                                                      | Integration smoke (currently mock-only-fallback; see Trigger 009)             |
| `tests/integration/fixtures/iec61850/`                                                      | libiec61850-CFG model fixtures                                                |

**Rules for contributions touching these paths:**

1. Every file under these paths **must** carry the SPDX
   header on its first non-shebang line:
   ```
   # SPDX-License-Identifier: GPL-3.0-only
   ```
   This is enforced by `make spdx-check` (CI gate).
2. By contributing to these paths, you agree that your
   contribution is licensed under **GPL-3.0-only** and may be
   redistributed under those terms. The grid-gym repo as a
   whole does not require copyright assignment — your changes
   remain yours; the GPL-3.0-only marker controls the
   distribution-license of the GPL-isolated sub-module.
3. **No static imports** of `grid_gym.adapters.driven.protocol_iec61850.*`
   from outside the boundary — that would propagate GPL-3.0
   to the rest of the MIT codebase (GPLv3 §5 license-
   aggregation). Cross-module access uses the Welle-1
   `build_protocol_ports` factory with an
   `ImportError`-tolerant plugin pattern. This is enforced
   by the [`AC-IEC61850-GPL-BOUNDARY`](docs/plan/adr/0035-iec61850-adapter-profile.md) arch-check contract
   (M4 Welle 6b C2).

### Adding a new GPL-isolated path

If you need to introduce a new path under the GPL boundary
(e.g., a new optional-extra adapter for a different GPL
library), update:

- `LICENSE` — extend the EXCEPTION block with the new path.
- `tools/check_spdx.py` — add the new path to
  `_DEFAULT_GPL_PATHS` (or `_DEFAULT_GPL_FILE_GLOBS`).
- `tools/arch_check.py` — extend or duplicate
  `_check_iec61850_gpl_boundary` for the new boundary if it
  needs its own import-boundary contract.
- `pyproject.toml` — add the optional-extra dependency.
- This `CONTRIBUTING.md` — list the new path in the table
  above.

Precedence: see how `protocol_iec61850/` was added in M4
Welle 5b ([ADR 0035](docs/plan/adr/0035-iec61850-adapter-profile.md))
and how the lint/contract tooling was wired up in M4 Welle 6b
C1+C2.

### Why pre-file SPDX headers?

The MIT/GPL boundary lives at the **file level**, not the
package level. Distribution-license tooling (SBOM
generators, `reuse-tool`, `scancode-toolkit`) reads SPDX
headers per file. Without per-file markers, a downstream
packager that bundles the GPL-isolated sub-module separately
would have no way to know which files are MIT vs GPL —
which is the situation that [`ADR 0035`](docs/plan/adr/0035-iec61850-adapter-profile.md) §I-f explicitly avoids
by making the boundary opt-in via `pip install
grid-gym[iec61850]`.

---

## Development Workflow

### Build, Test, Lint (Docker-only)

All builds, tests, and gates run via `make` targets that
build Docker images — no local Python venv needed. See
[`Makefile`](Makefile) for the full list.

Common workflows:

```bash
make test-unit          # pytest tests/unit/
make test-integration   # pytest tests/integration/
make arch-check         # import-linter + tools/arch_check.py (20 contracts)
make gates              # all 10 A-1 gates: lint + format-check + typecheck
                        # + arch-check + test-unit + coverage-gate
                        # + coverage-gate-critical + dep-audit + noqa-gate
                        # + spdx-check
make docs-check         # tools/check_refs.py (Markdown link validator)
make spdx-check         # tools/check_spdx.py (GPL-3.0-only header lint)
```

For the typecheck stage (mypy --strict + strict_bytes), see
[ADR 0005](docs/plan/adr/0005-type-check-gate.md).
For the coverage thresholds, see the `coverage-gate` targets in
the [`Makefile`](Makefile).

### Slice Workflow

Non-trivial changes are organized as **slices** under
`docs/plan/planning/`. Each slice gets a doc that records
scope, anti-scope, verification path, and DoD checklist;
commits within a slice are typically C0..C4
(C0 = slice-doc, C1..Cn = code, last = status/DoD-sync).

Examples:

- [`done/M4-welle-6a.md`](docs/plan/planning/done-archive/M4-welle-6a.md) —
  Cross-Adapter-Hardening (OTel-Span-Wrap, profile index).
- [`done/033-iec61850-adapter-review-folge.md`](docs/plan/planning/done-archive/033-iec61850-adapter-review-folge.md) —
  IEC-61850 review-follow-up (15 findings).
- [`done/034-iec61850-otel-wrap-review-folge.md`](docs/plan/planning/done-archive/034-iec61850-otel-wrap-review-folge.md) —
  OTel-wrap review-follow-up (15 findings).

When in doubt about whether your change deserves its own
slice: look at recent commits on `main` — if the change
spans more than a single `feat:` commit, it likely warrants
a slice-doc.

### Commit Style

Conventional-Commits-style prefix: `feat(welle-Nx):`,
`fix(...):`, `chore(...):`, `docs(plan):`, `refactor(...):`,
etc. Subject line under 70 chars; body explains the **why**;
trailer `Co-Authored-By:` if AI-assisted.

For commits that involve a file move + content rewrite, **do
two separate commits**: first `git mv` rename-only, then
content edit. This preserves git's rename detection (one of
the cross-conversation recurring conventions from the
user-memory; see also the Welle 1..6a self-close-move
pattern).

### Quality Gates (CI)

`make gates` is the canonical green-bar; CI runs the same
target. The 10 A-1 gates as of M4 Welle 6b:

1. `lint` (ruff)
2. `format-check` (ruff format)
3. `typecheck` (mypy --strict + strict_bytes; [`ADR 0005`](docs/plan/adr/0005-type-check-gate.md))
4. `arch-check` (import-linter + tools/arch_check.py; 20
   contracts; [`ADR 0002`](docs/plan/adr/0002-language-and-build-stack.md) §A-1 + [`ADR 0024`](docs/plan/adr/0024-observability-port-trio.md) §4.5.5 + [`ADR 0029`](docs/plan/adr/0029-no-coverage-pragma-contract.md) +
   Slice 028 + [`ADR 0035`](docs/plan/adr/0035-iec61850-adapter-profile.md) §I-f)
5. `test-unit`
6. `coverage-gate` (90% line / 85% branch; [`ADR 0007`](docs/plan/adr/0007-random-port.md))
7. `coverage-gate-critical` (90% on critical-domain targets)
8. `dep-audit`
9. `noqa-gate` (Slice 027 — no `# noqa` markers)
10. `spdx-check` (M4 Welle 6b — GPL-3.0-only header in
    IEC-61850 boundary)

---

## Questions / Issues

For bugs, feature requests, and discussion: please open an
issue on the repository tracker. For architectural decisions
that need persistent rationale, follow the ADR pattern in
[`docs/plan/adr/`](docs/plan/adr/) — every numbered ADR
records context, decision, and consequences.
