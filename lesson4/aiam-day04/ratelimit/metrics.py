"""In-process metrics store for the Day 4 dashboard (single-worker uvicorn)."""
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
            "requests_total": 0,
            "requests_allowed": 0,
            "requests_throttled": 0,
            "throttle_rate": 0.0,
            "tokens_input_total": 0,
            "tokens_output_total": 0,
            "spend_usd_total": 0.0,
            "budget_usd": 10.0,
            "budget_remaining_usd": 10.0,
            "users_tracked": 0,
            "budget_alerts": 0,
            "standard_tier_checks": 0,
            "premium_tier_checks": 0,
            "admin_tier_checks": 0,
            "latency_ms_avg": 0.0,
            "latency_ms_total": 0,
            "demo_runs": 0,
            "last_status": "idle",
            "last_user": "",
            "last_detail": "",
            "recent_events": [],
        }

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self._data)

    def sync_from_service(
        self,
        *,
        budget_usd: float,
        spend_usd: float,
        budget_remaining: float,
        users_tracked: int,
        tokens_input: int,
        tokens_output: int,
    ) -> None:
        with self._lock:
            self._data["budget_usd"] = round(budget_usd, 6)
            self._data["spend_usd_total"] = round(spend_usd, 6)
            self._data["budget_remaining_usd"] = round(budget_remaining, 6)
            self._data["users_tracked"] = users_tracked
            self._data["tokens_input_total"] = tokens_input
            self._data["tokens_output_total"] = tokens_output

    def record(
        self,
        *,
        user: str,
        tier: str,
        allowed: bool,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        latency_ms: int = 0,
        detail: str = "",
        label: str = "",
        budget_alert: bool = False,
    ) -> None:
        with self._lock:
            self._data["requests_total"] += 1
            if allowed:
                self._data["requests_allowed"] += 1
            else:
                self._data["requests_throttled"] += 1

            total = self._data["requests_total"]
            throttled = self._data["requests_throttled"]
            self._data["throttle_rate"] = round(throttled / total, 4) if total else 0.0

            if input_tokens:
                self._data["tokens_input_total"] += input_tokens
            if output_tokens:
                self._data["tokens_output_total"] += output_tokens
            if cost_usd:
                self._data["spend_usd_total"] = round(
                    self._data["spend_usd_total"] + cost_usd, 6
                )

            tier_key = f"{tier}_tier_checks"
            if tier_key in self._data:
                self._data[tier_key] += 1

            if budget_alert:
                self._data["budget_alerts"] += 1

            self._data["latency_ms_total"] += max(0, latency_ms)
            self._data["latency_ms_avg"] = round(
                self._data["latency_ms_total"] / total, 2
            )

            status = "ok" if allowed else "throttled"
            self._data["last_status"] = status
            self._data["last_user"] = user
            self._data["last_detail"] = detail[:200]

            self._event_sequence += 1
            events = self._data["recent_events"]
            events.insert(
                0,
                {
                    "id": self._event_sequence,
                    "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
                    "label": label or tier,
                    "user": user,
                    "tier": tier,
                    "status": status,
                    "latency_ms": latency_ms,
                    "detail": detail[:120],
                    "cost_usd": round(cost_usd, 6),
                },
            )
            self._data["recent_events"] = events[:10]

    def bump_demo(self) -> None:
        with self._lock:
            self._data["demo_runs"] += 1


METRICS = MetricsStore()
