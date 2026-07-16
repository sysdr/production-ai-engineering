#!/usr/bin/env python3
"""AIAM Day 3 — Memory Systems CLI Demo."""
from __future__ import annotations

import time

from memory.semantic_cache import SemanticCache
from memory.short_term import ShortTermMemory


def hr() -> None:
    print("─" * 50)


def main() -> None:
    print("\n" + "=" * 55)
    print("  AIAM Day 3 — Memory Systems Demo")
    print("=" * 55)

    print("\n[1] SHORT-TERM SLIDING WINDOW MEMORY")
    hr()
    mem = ShortTermMemory(max_turns=3)
    exchanges = [
        ("What is Python?", "Python is a high-level programming language."),
        ("What about its speed?", "Python is slower than C but fast to develop."),
        ("Show a hello world.", "print('Hello, World!')"),
        ("Now what did I ask first?", "You asked: 'What is Python?'"),
    ]
    for user, assistant in exchanges:
        mem.store("sess_1", user, assistant)
        stats = mem.stats("sess_1")
        print(
            f"  Stored: '{user[:40]}' | turns={stats['turns']} "
            f"est_tokens={stats['est_tokens']}"
        )

    print("\n  Current context window:")
    for msg in mem.get("sess_1"):
        print(f"    [{msg['role']:9s}] {msg['content'][:60]}")

    print("\n[2] SEMANTIC CACHE (TTL=5s)")
    hr()
    cache = SemanticCache(ttl_seconds=5)
    queries = [
        ("capital of France", "Paris"),
        ("What is 2+2?", "4"),
        ("capital of france", None),  # should hit cache
    ]
    for query, answer in queries:
        hit = cache.get(query)
        if hit:
            print(f"  CACHE HIT:  '{query}' → '{hit}'")
        else:
            result = answer or f"[computed: {query}]"
            cache.set(query, result)
            print(f"  CACHE MISS: '{query}' → stored '{result}'")

    print(
        f"\n  Hit rate: {cache.hit_rate():.0%}  "
        f"hits={cache.hits}  misses={cache.misses}"
    )

    print("\n[3] TTL EVICTION DEMO")
    hr()
    ttl_cache = SemanticCache(ttl_seconds=1)
    ttl_cache.set("expiring key", "expiring value")
    print(f"  Immediately:  {ttl_cache.get('expiring key')}")
    time.sleep(1.1)
    print(f"  After 1.1s:   {ttl_cache.get('expiring key')} (None = evicted)")

    print("\n" + "=" * 55)
    print("  Day 3 Complete — Memory systems demonstrated.")
    print("  Next: Day 4 — Rate Limiting & Cost Control")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
