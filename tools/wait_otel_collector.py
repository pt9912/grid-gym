"""Bounded-Poll auf den OTel-Collector-Health-Endpoint.

Wird vom `make runtime`-Target aus dem `api`-Container ausgefuehrt,
weil das offizielle `otel/opentelemetry-collector-contrib:*`-Image
distroless ist (kein wget/nc/sh fuer einen in-container healthcheck-
Block in `deploy/compose.yml`).

Default-Endpoint: `http://otel-collector:13133/` (Compose-Sibling-
Hostname + `health_check`-Extension-Port). Bounded-Poll mit 30s-
Timeout im 500ms-Raster — gross genug fuer Cold-Start des Collectors,
nicht so gross, dass ein echter Boot-Fail die `make runtime`-Smoke
unnoetig verzoegert.

Nutzt ausschliesslich Python-stdlib (urllib + time), damit das
Skript im produktions-shaped `grid-gym-runtime`-Image ohne
Zusatz-Dependencies laeuft.
"""

from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request

_DEFAULT_URL = "http://otel-collector:13133/"
_TIMEOUT_S = 30.0
_INTERVAL_S = 0.5
_PROBE_TIMEOUT_S = 2.0


def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_URL
    deadline = time.monotonic() + _TIMEOUT_S
    last_error: BaseException | None = None
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=_PROBE_TIMEOUT_S).read()  # noqa: S310
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as exc:
            last_error = exc
            time.sleep(_INTERVAL_S)
            continue
        print(f"[wait_otel_collector] {url} ready")
        return 0
    print(
        f"[wait_otel_collector] {url} still unhealthy after {_TIMEOUT_S}s: {last_error!r}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
