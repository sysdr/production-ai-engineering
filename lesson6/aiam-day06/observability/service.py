"""Coordinates request simulation, structured logging, and metrics."""
from __future__ import annotations

import random
import time
import uuid
from typing import Any

from observability.logging_config import setup_logger
from observability.metrics import METRICS

# Latency above this (ms) is considered slow and logged at WARNING.
SLOW_THRESHOLD_MS = 500

# Deterministic traffic profile so the demo always populates every metric.
DEMO_ROUTES: list[tuple[str, int, int, float]] = [
    # (route, latency_lo_ms, latency_hi_ms, error_probability)
    ("/chat", 40, 220, 0.05),
    ("/embed", 15, 120, 0.02),
    ("/search", 60, 400, 0.08),
    ("/rerank", 90, 650, 0.12),
    ("/summarize", 120, 900, 0.15),
]


class ObservabilityService:
    """Simulates AI-gateway traffic and records structured telemetry."""

    def __init__(self, seed: int | None = None) -> None:
        self.log = setup_logger("aiam.obs")
        self._rng = random.Random(seed if seed is not None else 42)

    def record_request(
        self,
        *,
        route: str,
        latency_ms: float,
        status_code: int,
        detail: str = "",
    ) -> dict[str, Any]:
        request_id = uuid.uuid4().hex[:12]
        if status_code >= 400:
            level = "ERROR"
        elif latency_ms >= SLOW_THRESHOLD_MS:
            level = "WARNING"
        else:
            level = "INFO"

        message = detail or f"{route} handled"
        self.log.log(
            {"ERROR": 40, "WARNING": 30, "INFO": 20}[level],
            message,
            extra={
                "route": route,
                "status": status_code,
                "latency_ms": round(latency_ms, 2),
                "request_id": request_id,
            },
        )
        METRICS.record_request(
            route=route,
            status_code=status_code,
            latency_ms=latency_ms,
            level=level,
            detail=message,
            request_id=request_id,
        )
        return {
            "route": route,
            "status": status_code,
            "latency_ms": round(latency_ms, 2),
            "level": level,
            "request_id": request_id,
        }

    def simulate_request(self, route: str | None = None) -> dict[str, Any]:
        profile = (
            next((r for r in DEMO_ROUTES if r[0] == route), None)
            if route
            else self._rng.choice(DEMO_ROUTES)
        )
        if profile is None:
            profile = (route or "/chat", 40, 220, 0.05)

        name, lo, hi, err_p = profile
        latency_ms = self._rng.uniform(lo, hi)
        is_error = self._rng.random() < err_p
        status_code = self._rng.choice([500, 502, 503, 429]) if is_error else 200
        # Small artificial delay keeps throughput realistic without slowing tests.
        time.sleep(min(0.003, latency_ms / 100000))
        detail = "upstream_error" if is_error else "ok"
        return self.record_request(
            route=name,
            latency_ms=latency_ms,
            status_code=status_code,
            detail=detail,
        )

    def run_demo(self, count: int = 60) -> dict[str, Any]:
        """Generate deterministic traffic that touches every metric.

        Simulated WARN/ERROR samples are injected mid-run so RED tiles stay
        non-zero, then a few successful INFO requests finish the demo so the
        recent-events feed does not look like the run failed.
        """
        results: list[dict[str, Any]] = []
        mid = max(1, count // 2)
        for i in range(count):
            if i == mid:
                results.append(
                    self.record_request(
                        route="/summarize",
                        latency_ms=880.0,
                        status_code=200,
                        detail="simulated slow upstream",
                    )
                )
                results.append(
                    self.record_request(
                        route="/rerank",
                        latency_ms=120.0,
                        status_code=503,
                        detail="simulated upstream error",
                    )
                )
            results.append(self.simulate_request())

        # Finish on healthy traffic so Recent log events tops out with INFO/ok.
        for route in ("/chat", "/embed", "/search"):
            results.append(
                self.record_request(
                    route=route,
                    latency_ms=45.0,
                    status_code=200,
                    detail="ok",
                )
            )

        METRICS.bump_demo()
        return {
            "generated": len(results),
            "sample": results[:8],
            "metrics": METRICS.snapshot(),
        }
