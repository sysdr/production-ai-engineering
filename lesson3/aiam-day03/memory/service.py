"""Coordinates short-term memory, semantic cache, Redis, and metrics."""
from __future__ import annotations

import time
from typing import Any

from memory.metrics import METRICS
from memory.redis_store import RedisStore
from memory.semantic_cache import SemanticCache
from memory.short_term import ShortTermMemory


class MemoryService:
    def __init__(
        self,
        *,
        max_turns: int = 10,
        cache_ttl: int = 300,
        redis_url: str | None = None,
    ) -> None:
        self.memory = ShortTermMemory(max_turns=max_turns)
        self.cache = SemanticCache(ttl_seconds=cache_ttl)
        self.redis = RedisStore(redis_url)
        METRICS.set_redis_connected(self.redis.connected)

    def refresh_redis_status(self) -> bool:
        ok = self.redis.connected
        METRICS.set_redis_connected(ok)
        return ok

    def store_turn(
        self, session_id: str, user: str, assistant: str, *, label: str = ""
    ) -> dict[str, Any]:
        t0 = time.monotonic()
        self.memory.store(session_id, user, assistant)
        redis_ops = 0
        if self.redis.set_json(
            f"session:{session_id}",
            self.memory.get(session_id),
            ttl=3600,
        ):
            redis_ops = 1
        ms = max(1, int((time.monotonic() - t0) * 1000))
        METRICS.set_sessions_active(self.memory.session_count())
        METRICS.record(
            op="store_turn",
            latency_ms=ms,
            detail=f"session={session_id}",
            label=label or "store",
            turns_delta=1,
            redis_ops=redis_ops,
        )
        return {"session_id": session_id, "stats": self.memory.stats(session_id)}

    def get_history(self, session_id: str, *, label: str = "") -> list[dict[str, str]]:
        t0 = time.monotonic()
        history = self.memory.get(session_id)
        redis_ops = 0
        if not history:
            remote = self.redis.get_json(f"session:{session_id}")
            if remote:
                redis_ops = 1
                history = remote
        ms = max(1, int((time.monotonic() - t0) * 1000))
        METRICS.record(
            op="get_history",
            latency_ms=ms,
            detail=f"turns={len(history) // 2}",
            label=label or "history",
            redis_ops=redis_ops,
        )
        return history

    def cache_lookup(self, query: str, *, label: str = "") -> dict[str, Any]:
        t0 = time.monotonic()
        before_evict = self.cache.evictions
        hit = self.cache.get(query)
        redis_ops = 0
        if hit is None:
            remote = self.redis.get_json(f"cache:{query.strip().lower()}")
            if remote is not None:
                redis_ops = 1
                hit = remote
                self.cache.set(query, hit)
                # Count as hit after Redis hydrate
                self.cache.hits += 1
                self.cache.misses = max(0, self.cache.misses - 1)
        ms = max(1, int((time.monotonic() - t0) * 1000))
        ttl_eviction = self.cache.evictions > before_evict and hit is None
        METRICS.record(
            op="cache_lookup",
            latency_ms=ms,
            detail="hit" if hit is not None else "miss",
            label=label or "cache",
            cache_hit=hit is not None,
            redis_ops=redis_ops,
            ttl_eviction=ttl_eviction,
        )
        return {"query": query, "hit": hit is not None, "value": hit}

    def cache_store(self, query: str, value: str, *, label: str = "") -> dict[str, Any]:
        t0 = time.monotonic()
        self.cache.set(query, value)
        redis_ops = 0
        if self.redis.set_json(
            f"cache:{query.strip().lower()}", value, ttl=self.cache.ttl
        ):
            redis_ops = 1
        ms = max(1, int((time.monotonic() - t0) * 1000))
        METRICS.record(
            op="cache_store",
            latency_ms=ms,
            detail=f"stored '{query[:40]}'",
            label=label or "cache_set",
            redis_ops=redis_ops,
        )
        return {"query": query, "stored": True}

    def flush_session(self, session_id: str, *, label: str = "") -> None:
        t0 = time.monotonic()
        self.memory.flush(session_id)
        redis_ops = 1 if self.redis.delete(f"session:{session_id}") else 0
        ms = max(1, int((time.monotonic() - t0) * 1000))
        METRICS.set_sessions_active(self.memory.session_count())
        METRICS.record(
            op="flush",
            latency_ms=ms,
            detail=f"flushed {session_id}",
            label=label or "flush",
            redis_ops=redis_ops,
        )

    def run_demo(self) -> dict[str, Any]:
        """Exercise sliding window, cache hit/miss, TTL eviction, Redis."""
        results: list[dict[str, Any]] = []
        self.refresh_redis_status()

        exchanges = [
            ("What is Python?", "Python is a high-level programming language."),
            ("What about its speed?", "Python is slower than C but fast to develop."),
            ("Show a hello world.", "print('Hello, World!')"),
            ("Now what did I ask first?", "You asked: 'What is Python?'"),
        ]
        for user, assistant in exchanges:
            results.append(
                {
                    "step": "store_turn",
                    **self.store_turn("sess_demo", user, assistant, label="WINDOW"),
                }
            )

        history = self.get_history("sess_demo", label="CONTEXT")
        results.append({"step": "history", "turns": len(history) // 2, "messages": history})

        # Cache miss then hit
        miss = self.cache_lookup("capital of France", label="CACHE_MISS")
        results.append({"step": "cache_lookup", **miss})
        if not miss["hit"]:
            self.cache_store("capital of France", "Paris", label="CACHE_SET")
        hit = self.cache_lookup("capital of france", label="CACHE_HIT")
        results.append({"step": "cache_lookup", **hit})

        # TTL eviction (1s)
        ttl_cache = SemanticCache(ttl_seconds=1)
        ttl_cache.set("expiring key", "expiring value")
        immediate = ttl_cache.get("expiring key")
        time.sleep(1.1)
        after = ttl_cache.get("expiring key")
        if after is None:
            METRICS.record(
                op="ttl_eviction",
                latency_ms=1,
                detail="key expired after 1.1s",
                label="TTL",
                cache_hit=False,
                ttl_eviction=True,
            )
        results.append(
            {
                "step": "ttl",
                "immediate": immediate,
                "after": after,
                "evicted": after is None,
            }
        )

        self.flush_session("sess_demo", label="FLUSH")
        METRICS.bump_demo()
        return {"results": results, "metrics": METRICS.snapshot()}
