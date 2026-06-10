"""Integration-Smokes fuer die GG-MVP-003 Abnahme-CLI (M7-Welle-2).

Pinnt den maschinenlesbaren `AbnahmeReport`-Vertrag von
`tools/accept.py` (Slice-Doc §2 Punkt 5):

1. Happy-Path → `overall_status == "pass"`, Exit 0, JSON-Schema-conform
   (Step A + Step B laufen **real** gegen `deploy/scenarios/gg-demo.yaml`
   inkl. fault-verdrahtetem Headless-Replay; Step C wird mit einem
   `healthy`-Fetcher-Stub gespeist, weil der Demo-Stack per D-7
   Aufrufer-Pflicht ist und `/ready` seine eigene Welle-6-Smoke hat).
2. Schema-invalides Szenario → `scenario_validation` + (Dependency-)
   `replay_determinism` `fail`, Exit **1** (Aggregate-Fail, **nicht**
   „!= 0"); alle drei Sub-Step-Entries praesent (no-fail-fast).
3. JSON-Schema-Pin (Top-Level- + `checks`-Keys + `status`-Literale +
   `schema_version`; **nicht** `ready_payload`-Inhalt).
4. Kaputtes YAML (`YAMLError`) → Exit **2** (Tool-Error); Gegenprobe
   fehlende Datei → Exit **1** (Step-A-`fail`).

stdout-Vertrag: das JSON wird ohne Pre-Strip geparst
(`json.loads(captured.out)`).

`tools/accept.py` wird als Skript-Modul ueber `sys.path` geladen
(kein installiertes Paket; tools/ ist flach, kein `__init__.py`).
"""

from __future__ import annotations

import importlib
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

_TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

accept = importlib.import_module("accept")

_GG_DEMO_PATH = Path(__file__).resolve().parents[2] / "deploy" / "scenarios" / "gg-demo.yaml"

_TOP_LEVEL_KEYS = {"schema_version", "overall_status", "checks"}
_CHECK_KEYS = {"scenario_validation", "replay_determinism", "demo_healthcheck"}


def _healthy_ready_fetcher() -> tuple[int, Mapping[str, Any]]:
    """Simuliert einen laufenden, gesunden Demo-Stack (Step C). Der
    `ready_payload`-Inhalt ist bewusst additiv-erweiterbar und wird vom
    Schema-Pin nicht festgenagelt."""
    return 200, {
        "status": "healthy",
        "components": {
            "api": {"status": "healthy"},
            "ui": {"status": "healthy"},
            "db": {"status": "healthy"},
            "simulation": {"status": "healthy"},
        },
    }


def _run(argv: list[str]) -> int:
    return accept.main(argv, ready_fetcher=_healthy_ready_fetcher)


def test_accept_happy_path_returns_pass_status(capsys: pytest.CaptureFixture[str]) -> None:
    """Alle drei Sub-Pruefungen gruen → `overall_status == "pass"`,
    Exit 0. Pinnt zugleich Eigenschaft (1) fuer den **fault-verdrahteten**
    Headless-Stream (zwei Laeufe, `diff_replay`-leer) + den Stream-Hash-
    Pin (Eigenschaft 2) — beides ueber den realen Step B."""
    exit_code = _run([str(_GG_DEMO_PATH)])
    captured = capsys.readouterr()

    assert exit_code == 0
    report = json.loads(captured.out)  # stdout ist JSON-only (kein Pre-Strip)

    assert report["schema_version"] == "1"
    assert report["overall_status"] == "pass"
    checks = report["checks"]
    assert checks["scenario_validation"]["status"] == "pass"
    assert checks["scenario_validation"]["scenario_hash"] == accept.EXPECTED_DEMO_SCENARIO_HASH
    assert checks["replay_determinism"]["status"] == "pass"
    assert checks["replay_determinism"]["diff_count"] == 0
    assert checks["replay_determinism"]["volatile_only"] is True
    assert checks["demo_healthcheck"]["status"] == "pass"
    assert checks["demo_healthcheck"]["endpoint"] == "/ready"
    # `reason` ist present-on-fail → auf Pass nicht serialisiert.
    assert "reason" not in checks["scenario_validation"]
    assert "reason" not in checks["replay_determinism"]


def test_accept_invalid_scenario_returns_fail_status(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Schema-invalides (aber syntaktisch gueltiges) YAML →
    `scenario_validation` `fail` + `overall_status == "fail"`, Exit
    **1** (Aggregate-Fail-Pin, **nicht** „!= 0"). No-fail-fast:
    alle drei Sub-Step-Entries praesent; `replay_determinism` traegt
    den Dependency-`reason`; `demo_healthcheck` laeuft (stack-,
    nicht scenario-abhaengig)."""
    invalid = tmp_path / "broken-schema.yaml"
    invalid.write_text("name: missing-required-keys\n", encoding="utf-8")

    exit_code = _run([str(invalid)])
    captured = capsys.readouterr()

    assert exit_code == 1  # nicht „!= 0" — Exit 2 ist ein anderes Signal
    report = json.loads(captured.out)

    assert report["overall_status"] == "fail"
    checks = report["checks"]
    assert set(checks) == _CHECK_KEYS  # alle drei trotz Step-A-Fail
    assert checks["scenario_validation"]["status"] == "fail"
    assert checks["replay_determinism"]["status"] == "fail"
    assert checks["replay_determinism"]["reason"].startswith("dependency: scenario load failed")
    # Step C ist stack-, nicht scenario-abhaengig → laeuft trotz Step-A-Fail.
    assert checks["demo_healthcheck"]["status"] == "pass"


def test_accept_machine_readable_json_schema_pinned(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """JSON-Output-Schema bleibt rueckwaerts-kompatibel: Top-Level- +
    `checks`-Keys + `status`-Literale + `schema_version`-Wert sind
    gepinnt; `ready_payload`-Inhalt **nicht** (additive
    `/ready`-Erweiterungen brechen den Smoke nicht)."""
    exit_code = _run([str(_GG_DEMO_PATH)])
    captured = capsys.readouterr()

    assert exit_code == 0
    report = json.loads(captured.out)

    assert set(report) == _TOP_LEVEL_KEYS
    assert report["schema_version"] == "1"
    assert report["overall_status"] in {"pass", "fail"}
    checks = report["checks"]
    assert set(checks) == _CHECK_KEYS
    for check in checks.values():
        assert check["status"] in {"pass", "fail"}
    # ready_payload ist bewusst nicht gepinnt — nur die Anwesenheit des
    # Schluessels auf einem Pass-Healthcheck.
    assert "ready_payload" in checks["demo_healthcheck"]


def test_accept_tool_error_returns_exit_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Syntaktisch kaputtes YAML (`yaml.safe_load` → `YAMLError`) →
    Exit **2** (Tool-Error, auf konkreten Wert gepinnt, **nicht**
    „>= 1"); Traceback auf stderr, stdout-JSON darf fehlen.
    Gegenprobe im selben Smoke: fehlende Datei → Exit **1**
    (deterministisches Step-A-`fail`) — pinnt die Exit-1-vs-Exit-2-
    Abgrenzung aus D-9."""
    broken = tmp_path / "broken-syntax.yaml"
    broken.write_text("devices: [unclosed\n", encoding="utf-8")  # ParserError

    tool_error_exit = _run([str(broken)])
    captured = capsys.readouterr()

    assert tool_error_exit == 2
    assert captured.err.strip()  # Traceback auf stderr
    assert captured.out.strip() == ""  # kein JSON auf stdout

    # Gegenprobe: fehlende/unlesbare Datei ist KEIN Tool-Error → Exit 1.
    missing = tmp_path / "does-not-exist.yaml"
    missing_exit = _run([str(missing)])
    missing_captured = capsys.readouterr()

    assert missing_exit == 1
    missing_report = json.loads(missing_captured.out)
    assert missing_report["overall_status"] == "fail"
    assert missing_report["checks"]["scenario_validation"]["status"] == "fail"


def test_accept_float_in_decimal_field_returns_fail_not_tool_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Review-Folge F1: ein bare YAML-`float` in einem Decimal-Allowlist-
    Feld umgeht die `str → Decimal`-Koercion und laesst die
    `scenario_hash`-Berechnung mit `WrongTypeError` (canonical-
    incompatible) brechen — ein `GridGymError`, **kein** `ScenarioError`.
    Das ist ein deterministischer Szenario-Daten-Fehler → Exit **1**
    (`scenario_validation` fail), **nicht** Exit 2 (Tool-Error). Pinnt,
    dass Step A `GridGymError` (nicht nur `ScenarioError`) faengt — sonst
    schickt ein sehr haeufiger YAML-Editier-Fehler (`50.5` statt `"50.5"`)
    CI in den falschen Eskalations-Pfad."""
    raw = _GG_DEMO_PATH.read_text(encoding="utf-8")
    mutated = re.sub(r'(rated_power_kw:\s*)"[\d.]+"', r"\g<1>50.5", raw, count=1)
    assert mutated != raw, "Mutation muss greifen (quotiertes rated_power_kw erwartet)"
    bad = tmp_path / "float-decimal.yaml"
    bad.write_text(mutated, encoding="utf-8")

    exit_code = _run([str(bad)])
    captured = capsys.readouterr()

    assert exit_code == 1  # nicht 2 — Szenario-Daten-Fehler, kein Tool-Error
    report = json.loads(captured.out)
    assert report["overall_status"] == "fail"
    assert report["checks"]["scenario_validation"]["status"] == "fail"
    # alle drei Entries bleiben praesent (no-fail-fast).
    assert set(report["checks"]) == _CHECK_KEYS
