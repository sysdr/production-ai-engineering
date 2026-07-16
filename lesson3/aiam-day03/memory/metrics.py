"""In-process metrics store for the Day 3 dashboard (single-worker uvicorn)."""
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
            "memory_ops_total": 0,
            "turns_stored": 0,
            "sessions_active": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_hit_rate": 0.0,
            "ttl_evictions": 0,
            "redis_ops": 0,
            "redis_connected": False,
            "latency_ms_total": 0,
            "latency_ms_avg": 0.0,
            "demo_runs": 0,
            "last_status": "idle",
            "last_op": "",
            "last_detail": "",
            "recent_events": [],
        }

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self._data)

    def set_redis_connected(self, connected: bool) -> None:
        with self._lock:
            self._data["redis_connected"] = connected

    def set_sessions_active(self, count: int) -> None:
        with self._lock:
            self._data["sessions_active"] = max(0, count)

    def record(
        self,
        *,
        op: str,
        success: bool = True,
        latency_ms: int = 0,
        detail: str = "",
        label: str = "",
        cache_hit: bool | None = None,
        turns_delta: int = 0,
        redis_ops: int = 0,
        ttl_eviction: bool = False,
    ) -> None:
        with self._lock:
            self._data["memory_ops_total"] += 1
            if turns_delta:
                self._data["turns_stored"] += max(0, turns_delta)
            if redis_ops:
                self._data["redis_ops"] += max(0, redis_ops)
            if ttl_eviction:
                self._data["ttl_evictions"] += 1

            if cache_hit is True:
                self._data["cache_hits"] += 1
            elif cache_hit is False:
                self._data["cache_misses"] += 1

            hits = self._data["cache_hits"]
            misses = self._data["cache_misses"]
            total = hits + misses
            self._data["cache_hit_rate"] = round(hits / total, 4) if total else 0.0

            self._data["latency_ms_total"] += max(0, latency_ms)
            ops = self._data["memory_ops_total"]
            self._data["latency_ms_avg"] = round(
                self._data["latency_ms_total"] / ops, 2
            )

            status = "ok" if success else "error"
            self._data["last_status"] = status
            self._data["last_op"] = op
            self._data["last_detail"] = detail[:200]

            self._event_sequence += 1
            events = self._data["recent_events"]
            events.insert(
                0,
                {
                    "id": self._event_sequence,
                    "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
                    "label": label or op,
                    "op": op,
                    "status": status,
                    "latency_ms": latency_ms,
                    "detail": detail[:120],
                },
            )
            self._data["recent_events"] = events[:10]

    def bump_demo(self) -> None:
        with self._lock:
            self._data["demo_runs"] += 1


METRICS = MetricsStore()
