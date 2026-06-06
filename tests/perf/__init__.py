"""Performance-Bench-Layer (M6 Welle 4b-a; ADR 0041).

Bench-Tests werden NUR ueber `make perf` ausgefuehrt (Dockerfile-
`perf`-Stage + `pyproject.toml` `[project.optional-dependencies.
perf]`-Extra). Default-`make gates`/`make ci`/`make fullbuild`
ueberspringen `tests/perf/` (kein pytest-Argument, das den Pfad
auflistet) — ADR-0041 §2.5.
"""
