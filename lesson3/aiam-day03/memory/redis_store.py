"""Optional Redis backend for session turns and cache entries."""
from __future__ import annotations

import json
import os
from typing import Any, Optional

try:
    import redis
except ImportError:  # pragma: no cover
    redis = None  # type: ignore[assignment]


class RedisStore:
    """Thin Redis wrapper; no-ops when Redis is unavailable."""

    def __init__(self, url: str | None = None) -> None:
        self.url = url or os.getenv("REDIS_URL", "")
        self._client: Any = None
        self.ops = 0
        self._connect()

    def _connect(self) -> None:
        if not self.url or redis is None:
            self._client = None
            return
        try:
            client = redis.Redis.from_url(
                self.url,
                decode_responses=True,
                socket_connect_timeout=1.5,
                socket_timeout=1.5,
            )
            client.ping()
            self._client = client
        except Exception:  # noqa: BLE001 — fall back to in-memory
            self._client = None

    @property
    def connected(self) -> bool:
        if self._client is None:
            return False
        try:
            self._client.ping()
            return True
        except Exception:  # noqa: BLE001
            self._client = None
            return False

    def set_json(self, key: str, value: Any, ttl: int | None = None) -> bool:
        if not self.connected:
            return False
        payload = json.dumps(value)
        if ttl:
            self._client.setex(key, ttl, payload)
        else:
            self._client.set(key, payload)
        self.ops += 1
        return True

    def get_json(self, key: str) -> Optional[Any]:
        if not self.connected:
            return None
        raw = self._client.get(key)
        self.ops += 1
        if raw is None:
            return None
        return json.loads(raw)

    def delete(self, key: str) -> bool:
        if not self.connected:
            return False
        self._client.delete(key)
        self.ops += 1
        return True
