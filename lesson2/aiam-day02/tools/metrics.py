"""In-process metrics store for the Day 2 dashboard (single-worker uvicorn)."""
from __future__ import annotations

import threading
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any


class MetricsStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._event_sequence = 0
        self._data: dict[str, Any] = {
            "tool_calls_total": 0,
            "tool_calls_ok": 0,
            "tool_calls_denied": 0,
            "tool_calls_failed": 0,
            "tool_calls_unsafe_blocked": 0,
            "latency_ms_total": 0,
            "latency_ms_avg": 0.0,
            "calculate_calls": 0,
            "echo_calls": 0,
            "write_log_calls": 0,
            "demo_runs": 0,
            "last_status": "idle",
            "last_tool": "",
            "last_output": "",
            "recent_events": [],
        }

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self._data)

    def record(
        self,
        *,
        tool: str,
        success: bool,
        error: str | None = None,
        latency_ms: int = 0,
        output: Any = None,
        label: str = "",
    ) -> None:
        with self._lock:
            self._data["tool_calls_total"] += 1
            denied = bool(error and "Permission" in error)
            unsafe = bool(error and ("Unsafe" in error or "rejected" in (error or "").lower()))
            if success:
                self._data["tool_calls_ok"] += 1
                status = "ok"
            elif denied:
                self._data["tool_calls_denied"] += 1
                status = "denied"
            elif unsafe:
                self._data["tool_calls_unsafe_blocked"] += 1
                self._data["tool_calls_failed"] += 1
                status = "blocked"
            else:
                self._data["tool_calls_failed"] += 1
                status = "failed"

            self._data["latency_ms_total"] += max(0, latency_ms)
            total = self._data["tool_calls_total"]
            self._data["latency_ms_avg"] = round(
                self._data["latency_ms_total"] / total, 2
            )

            if tool == "calculate":
                self._data["calculate_calls"] += 1
            elif tool == "echo":
                self._data["echo_calls"] += 1
            elif tool == "write_log":
                self._data["write_log_calls"] += 1

            out_str = "" if output is None else str(output)
            self._data["last_status"] = status
            self._data["last_tool"] = tool
            self._data["last_output"] = (error or out_str)[:200]

            self._event_sequence += 1
            events = self._data["recent_events"]
            events.insert(
                0,
                {
                    "id": self._event_sequence,
                    "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
                    "label": label or tool,
                    "tool": tool,
                    "status": status,
                    "expected": label in {"UNSAFE", "WRITE_DENIED", "UNKNOWN"},
                    "latency_ms": latency_ms,
                    "detail": (error or out_str)[:120],
                },
            )
            self._data["recent_events"] = events[:10]

    def bump_demo(self) -> None:
        with self._lock:
            self._data["demo_runs"] += 1


METRICS = MetricsStore()
