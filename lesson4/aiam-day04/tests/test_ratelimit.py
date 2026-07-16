import time

import pytest

from ratelimit.bucket import RateLimiter, TokenBucket
from ratelimit.cost_tracker import CostTracker


def test_within_limit():
    rl = RateLimiter()
    for _ in range(5):
        assert rl.check("user1", "standard") is True


def test_burst_then_limited():
    rl = RateLimiter()
    for _ in range(10):
        rl.check("burst_user", "standard")
    with pytest.raises(PermissionError):
        rl.check("burst_user", "standard")


def test_refill():
    b = TokenBucket(capacity=1, refill_rate=10)
    b.consume()
    time.sleep(0.15)
    assert b.consume()


def test_cost_tracking():
    ct = CostTracker(budget_usd=1.0)
    ct.record("alice", 1_000_000, 0)
    ct.record("bob", 0, 1_000_000)
    assert ct.total_spend() == pytest.approx(0.75, rel=0.01)


def test_budget_exceeded():
    ct = CostTracker(budget_usd=0.001)
    ct.record("bigspender", 10_000_000, 10_000_000)
    assert ct.is_over_budget()
