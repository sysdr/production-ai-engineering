"""In-process metrics store for the Day 6 dashboard (single-worker uvicorn)."""
from __future__ import annotations

import math
import threading
import time
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any


class Histogram:
    """Simple latency histogram with nearest-rank percentiles."""

    def __init__(self) -> None:
        self._values: list[float] = []

    def observe(self, value: float) -> None:
        self._values.append(max(0.0, float(value)))

    def count(self) -> int:
        return len(self._values)

    def percentile(self, p: float) -> float:
        if not self._values:
            return 0.0
        ordered = sorted(self._values)
        rank = max(1, math.ceil((p / 100.0) * len(ordered)))
        return round(ordered[min(rank, len(ordered)) - 1], 2)

    def avg(self) -> float:
        if not self._values:
            return 0.0
        return round(sum(self._values) / len(self._values), 2)

    def maximum(self) -> float:
        return round(max(self._values), 2) if self._values else 0.0


class MetricsStore:
    """Thread-safe store powering the RED (Rate/Errors/Duration) dashboard."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._event_sequence = 0
        self._start_monotonic = time.monotonic()
        self._latency = Histogram()
        self._routes: dict[str, dict[str, int]] = {}
        self._data: dict[str, Any] = {
            "requests_total": 0,
            "requests_ok": 0,
            "requests_error": 0,
            "error_rate": 0.0,
            "throughput_rps": 0.0,
            "latency_p50_ms": 0.0,
            "latency_p95_ms": 0.0,
            "latency_p99_ms": 0.0,
            "latency_avg_ms": 0.0,
            "latency_max_ms": 0.0,
            "logs_info": 0,
            "logs_warn": 0,
            "logs_error": 0,
            "demo_runs": 0,
            "last_route": "",
            "last_status": 0,
            "routes": {},
            "recent_events": [],
        }

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self._data)

    def record_request(
        self,
        *,
        route: str,
        status_code: int,
        latency_ms: float,
        level: str,
        detail: str = "",
        request_id: str = "",
    ) -> None:
        with self._lock:
            self._data["requests_total"] += 1
            if status_code < 400:
                self._data["requests_ok"] += 1
            else:
                self._data["requests_error"] += 1

            total = self._data["requests_total"]
            self._data["error_rate"] = round(
                self._data["requests_error"] / total, 4
            )

            self._latency.observe(latency_ms)
            self._data["latency_p50_ms"] = self._latency.percentile(50)
            self._data["latency_p95_ms"] = self._latency.percentile(95)
            self._data["latency_p99_ms"] = self._latency.percentile(99)
            self._data["latency_avg_ms"] = self._latency.avg()
            self._data["latency_max_ms"] = self._latency.maximum()

            level_upper = level.upper()
            if level_upper == "ERROR":
                self._data["logs_error"] += 1
            elif level_upper in ("WARN", "WARNING"):
                self._data["logs_warn"] += 1
            else:
                self._data["logs_info"] += 1

            elapsed = max(1e-3, time.monotonic() - self._start_monotonic)
            self._data["throughput_rps"] = round(total / elapsed, 2)

            bucket = self._routes.setdefault(route, {"count": 0, "errors": 0})
            bucket["count"] += 1
            if status_code >= 400:
                bucket["errors"] += 1
            self._data["routes"] = deepcopy(self._routes)

            self._data["last_route"] = route
            self._data["last_status"] = status_code

            self._event_sequence += 1
            events = self._data["recent_events"]
            events.insert(
                0,
                {
                    "id": self._event_sequence,
                    "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
                    "route": route,
                    "status": status_code,
                    "level": level_upper,
                    "latency_ms": round(latency_ms, 2),
                    "detail": detail[:120],
                    "request_id": request_id,
                },
            )
            self._data["recent_events"] = events[:12]

    def bump_demo(self) -> None:
        with self._lock:
            self._data["demo_runs"] += 1


METRICS = MetricsStore()
