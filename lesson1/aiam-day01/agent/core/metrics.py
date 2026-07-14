"""In-process metrics store for the dashboard (single-worker uvicorn)."""
from __future__ import annotations

import threading
from typing import Any


class MetricsStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: dict[str, Any] = {
            "requests_total": 0,
            "requests_ok": 0,
            "requests_blocked": 0,
            "requests_rejected": 0,
            "tokens_total": 0,
            "cost_usd_total": 0.0,
            "latency_ms_total": 0,
            "latency_ms_avg": 0.0,
            "l4_security_ms_total": 0,
            "l2_memory_ms_total": 0,
            "l1_llm_ms_total": 0,
            "demo_runs": 0,
            "last_status": "idle",
            "last_content": "",
            "recent_events": [],
        }

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._data)

    def record(
        self,
        *,
        status: str,
        tokens: int = 0,
        cost_usd: float = 0.0,
        latency_ms: int = 0,
        layer_timings: dict[str, int] | None = None,
        content: str = "",
        label: str = "",
    ) -> None:
        layer_timings = layer_timings or {}
        with self._lock:
            self._data["requests_total"] += 1
            if status == "ok":
                self._data["requests_ok"] += 1
            elif status == "blocked":
                self._data["requests_blocked"] += 1
            else:
                self._data["requests_rejected"] += 1

            self._data["tokens_total"] += max(0, tokens)
            self._data["cost_usd_total"] = round(
                self._data["cost_usd_total"] + max(0.0, cost_usd), 6
            )
            self._data["latency_ms_total"] += max(0, latency_ms)
            ok_and_err = self._data["requests_total"]
            self._data["latency_ms_avg"] = round(
                self._data["latency_ms_total"] / ok_and_err, 2
            )

            self._data["l4_security_ms_total"] += layer_timings.get("l4_security_ms", 0)
            self._data["l2_memory_ms_total"] += layer_timings.get("l2_memory_ms", 0)
            self._data["l1_llm_ms_total"] += layer_timings.get("l1_llm_ms", 0)

            self._data["last_status"] = status
            self._data["last_content"] = (content or "")[:200]

            events = self._data["recent_events"]
            events.insert(
                0,
                {
                    "label": label or status,
                    "status": status,
                    "tokens": tokens,
                    "cost_usd": cost_usd,
                    "latency_ms": latency_ms,
                },
            )
            self._data["recent_events"] = events[:10]

    def bump_demo(self) -> None:
        with self._lock:
            self._data["demo_runs"] += 1


METRICS = MetricsStore()
