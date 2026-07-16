"""Exact-match + LRU semantic cache with TTL."""
from __future__ import annotations

import hashlib
import time
from typing import Optional


def _simple_hash(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode()).hexdigest()[:16]


class SemanticCache:
    """Exact-match + LRU semantic cache with TTL."""

    def __init__(self, ttl_seconds: int = 300, max_size: int = 100) -> None:
        self._store: dict[str, dict] = {}
        self.ttl = ttl_seconds
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, query: str) -> Optional[str]:
        key = _simple_hash(query)
        entry = self._store.get(key)
        if entry and (time.time() - entry["ts"]) < self.ttl:
            self.hits += 1
            return entry["value"]
        if entry:
            del self._store[key]
            self.evictions += 1
        self.misses += 1
        return None

    def set(self, query: str, value: str) -> None:
        if len(self._store) >= self.max_size:
            oldest = min(self._store, key=lambda k: self._store[k]["ts"])
            del self._store[oldest]
            self.evictions += 1
        self._store[_simple_hash(query)] = {"value": value, "ts": time.time()}

    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0
