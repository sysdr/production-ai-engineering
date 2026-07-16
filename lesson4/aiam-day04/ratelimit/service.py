"""Coordinates token-bucket rate limiting, cost tracking, and metrics."""
from __future__ import annotations

import time
from typing import Any

from ratelimit.bucket import RateLimiter
from ratelimit.cost_tracker import CostTracker
from ratelimit.metrics import METRICS


class RateLimitService:
    def __init__(self, budget_usd: float = 10.0) -> None:
        self.budget_usd = budget_usd
        self.rate_limiter = RateLimiter()
        self.cost_tracker = CostTracker(budget_usd=budget_usd)
        METRICS.sync_from_service(
            budget_usd=budget_usd,
            spend_usd=0.0,
            budget_remaining=budget_usd,
            users_tracked=0,
            tokens_input=0,
            tokens_output=0,
        )

    def _sync_metrics(self) -> None:
        METRICS.sync_from_service(
            budget_usd=self.cost_tracker.budget_usd,
            spend_usd=self.cost_tracker.total_spend(),
            budget_remaining=self.cost_tracker.budget_remaining(),
            users_tracked=max(
                self.rate_limiter.user_count(), self.cost_tracker.user_count()
            ),
            tokens_input=self.cost_tracker.total_input_tokens(),
            tokens_output=self.cost_tracker.total_output_tokens(),
        )

    def check_request(
        self,
        user_id: str,
        *,
        tier: str = "standard",
        input_tokens: int = 0,
        output_tokens: int = 0,
        label: str = "",
    ) -> dict[str, Any]:
        t0 = time.monotonic()
        allowed = False
        error: str | None = None
        cost = 0.0
        budget_alert = False

        try:
            self.rate_limiter.check(user_id, tier)
            allowed = True
            if input_tokens or output_tokens:
                cost = self.cost_tracker.record(user_id, input_tokens, output_tokens)
                if self.cost_tracker.is_over_budget():
                    budget_alert = True
        except PermissionError as exc:
            error = str(exc)

        ms = max(1, int((time.monotonic() - t0) * 1000))
        detail = (
            f"tier={tier} in={input_tokens} out={output_tokens} cost=${cost:.6f}"
            if allowed
            else (error or "throttled")
        )
        METRICS.record(
            user=user_id,
            tier=tier,
            allowed=allowed,
            input_tokens=input_tokens if allowed else 0,
            output_tokens=output_tokens if allowed else 0,
            cost_usd=cost,
            latency_ms=ms,
            detail=detail,
            label=label or "check",
            budget_alert=budget_alert,
        )
        self._sync_metrics()

        return {
            "user": user_id,
            "tier": tier,
            "allowed": allowed,
            "error": error,
            "cost_usd": cost,
            "tokens_available": self.rate_limiter.status(user_id)["tokens_available"],
            "spend_usd": self.cost_tracker.user_spend(user_id),
            "budget_remaining_usd": self.cost_tracker.budget_remaining(),
            "over_budget": self.cost_tracker.is_over_budget(),
            "latency_ms": ms,
        }

    def run_demo(self) -> dict[str, Any]:
        results: list[dict[str, Any]] = []

        allowed = blocked = 0
        for _ in range(15):
            r = self.check_request("alice", tier="standard", label="BURST_STD")
            if r["allowed"]:
                allowed += 1
            else:
                blocked += 1
        results.append(
            {
                "step": "standard_burst",
                "allowed": allowed,
                "blocked": blocked,
                "status": self.rate_limiter.status("alice"),
            }
        )

        premium_allowed = 0
        for _ in range(20):
            r = self.check_request(
                "premium_bob",
                tier="premium",
                input_tokens=1_000,
                output_tokens=500,
                label="PREMIUM",
            )
            if r["allowed"]:
                premium_allowed += 1
        results.append({"step": "premium_burst", "allowed": premium_allowed})

        users = [
            ("alice", 500_000, 200_000),
            ("bob", 300_000, 150_000),
            ("carol", 50_000, 25_000),
        ]
        for user, inp, out in users:
            r = self.check_request(
                user,
                tier="standard",
                input_tokens=inp,
                output_tokens=out,
                label="COST",
            )
            results.append({"step": "cost_record", "user": user, **r})

        budget_svc = RateLimitService(budget_usd=0.10)
        for i in range(10):
            budget_svc.check_request(
                f"user_{i}",
                tier="standard",
                input_tokens=100_000,
                output_tokens=50_000,
                label="BUDGET",
            )
        over = budget_svc.cost_tracker.is_over_budget()
        if over:
            METRICS.record(
                user="budget_demo",
                tier="standard",
                allowed=True,
                latency_ms=1,
                detail=f"BUDGET EXCEEDED — ${budget_svc.cost_tracker.total_spend():.4f}",
                label="ALERT",
                budget_alert=True,
            )
        results.append(
            {
                "step": "budget_alert",
                "over_budget": over,
                "spend_usd": budget_svc.cost_tracker.total_spend(),
            }
        )

        self._sync_metrics()
        METRICS.bump_demo()
        return {"results": results, "metrics": METRICS.snapshot()}
