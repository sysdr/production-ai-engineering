import threading
import time
from dataclasses import dataclass, field

@dataclass
class TokenBucket:
    """Classic token-bucket rate limiter. Thread-safe."""
    capacity: float
    refill_rate: float
    _tokens: float = field(init=False)
    _last: float = field(init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def __post_init__(self) -> None:
        self._tokens = self.capacity
        self._last = time.monotonic()

    def consume(self, amount: float = 1.0) -> bool:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
            self._last = now
            if self._tokens >= amount:
                self._tokens -= amount
                return True
            return False

    @property
    def available(self) -> float:
        with self._lock:
            return round(self._tokens, 2)


TIER_LIMITS = {
    "standard": {"capacity": 10, "refill_rate": 1.0},
    "premium": {"capacity": 50, "refill_rate": 5.0},
    "admin": {"capacity": 200, "refill_rate": 20.0},
}


class RateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, TokenBucket] = {}

    def _get(self, user_id: str, tier: str) -> TokenBucket:
        if user_id not in self._buckets:
            cfg = TIER_LIMITS.get(tier, TIER_LIMITS["standard"])
            self._buckets[user_id] = TokenBucket(**cfg)
        return self._buckets[user_id]

    def check(self, user_id: str, tier: str = "standard") -> bool:
        bucket = self._get(user_id, tier)
        allowed = bucket.consume()
        if not allowed:
            raise PermissionError(f"Rate limit exceeded: user={user_id} tier={tier}")
        return True

    def status(self, user_id: str) -> dict:
        b = self._buckets.get(user_id)
        return {"user": user_id, "tokens_available": b.available if b else "N/A"}

    def user_count(self) -> int:
        return len(self._buckets)
