"""Thread-safe metrics store for the Day 07 sandbox dashboard."""
from __future__ import annotations

import threading
import time
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any


class MetricsStore:
    """In-process counters powering the sandbox dashboard (single worker)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._event_sequence = 0
        self._start_monotonic = time.monotonic()
        self._durations: list[float] = []
        self._data: dict[str, Any] = {
            "executions_total": 0,
            "executions_ok": 0,
            "executions_blocked": 0,
            "executions_timeout": 0,
            "executions_error": 0,
            "allowed_module_hits": 0,
            "blocked_module_hits": 0,
            "demo_runs": 0,
            "recent_events": [],
        }

    def record(
        self,
        *,
        label: str,
        ok: bool,
        timeout: bool,
        blocked: bool,
        error: bool,
        duration_ms: float,
        output: str,
        allowed_hit: bool = False,
        blocked_hit: bool = False,
    ) -> None:
        with self._lock:
            self._data["executions_total"] += 1
            if timeout:
                self._data["executions_timeout"] += 1
                outcome = "TIMEOUT"
            elif blocked:
                self._data["executions_blocked"] += 1
                outcome = "BLOCKED"
            elif error:
                self._data["executions_error"] += 1
                outcome = "ERROR"
            elif ok:
                self._data["executions_ok"] += 1
                outcome = "OK"
            else:
                self._data["executions_error"] += 1
                outcome = "ERROR"

            if allowed_hit:
                self._data["allowed_module_hits"] += 1
            if blocked_hit:
                self._data["blocked_module_hits"] += 1

            self._durations.append(max(0.0, float(duration_ms)))
            self._event_sequence += 1
            event = {
                "id": self._event_sequence,
                "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds"),
                "label": label,
                "outcome": outcome,
                "duration_ms": round(duration_ms, 2),
                "detail": (output or "")[:120],
            }
            events: list[dict[str, Any]] = self._data["recent_events"]
            events.insert(0, event)
            del events[20:]

    def mark_demo(self) -> None:
        with self._lock:
            self._data["demo_runs"] += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            data = deepcopy(self._data)
            durations = list(self._durations)

        total = data["executions_total"]
        elapsed = max(time.monotonic() - self._start_monotonic, 1e-6)
        data["throughput_eps"] = round(total / elapsed, 3)
        data["block_rate"] = round(data["executions_blocked"] / total, 4) if total else 0.0
        data["timeout_rate"] = (
            round(data["executions_timeout"] / total, 4) if total else 0.0
        )
        data["ok_rate"] = round(data["executions_ok"] / total, 4) if total else 0.0
        data["duration_avg_ms"] = (
            round(sum(durations) / len(durations), 2) if durations else 0.0
        )
        data["duration_max_ms"] = round(max(durations), 2) if durations else 0.0
        data["duration_p50_ms"] = self._percentile(durations, 50)
        data["duration_p95_ms"] = self._percentile(durations, 95)
        data["duration_p99_ms"] = self._percentile(durations, 99)
        return data

    @staticmethod
    def _percentile(values: list[float], p: float) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        import math

        rank = max(1, math.ceil((p / 100.0) * len(ordered)))
        return round(ordered[min(rank, len(ordered)) - 1], 2)


METRICS = MetricsStore()
