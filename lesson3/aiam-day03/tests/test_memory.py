from memory.metrics import METRICS
from memory.semantic_cache import SemanticCache
from memory.service import MemoryService
from memory.short_term import ShortTermMemory


def test_store_and_retrieve():
    m = ShortTermMemory()
    m.store("s1", "hello", "world")
    h = m.get("s1")
    assert len(h) == 2
    assert h[0]["role"] == "user"


def test_window_limit():
    m = ShortTermMemory(max_turns=2)
    for i in range(5):
        m.store("s1", f"user_{i}", f"bot_{i}")
    h = m.get("s1")
    assert len(h) <= 4  # 2 turns * 2 messages


def test_flush():
    m = ShortTermMemory()
    m.store("s1", "u", "a")
    m.flush("s1")
    assert m.get("s1") == []


def test_cache_hit():
    c = SemanticCache(ttl_seconds=60)
    c.set("capital of France", "Paris")
    assert c.get("capital of france") == "Paris"
    assert c.hit_rate() == 1.0


def test_cache_miss():
    c = SemanticCache()
    assert c.get("something never stored") is None


def test_service_metrics_update():
    svc = MemoryService(cache_ttl=60)
    before = METRICS.snapshot()["memory_ops_total"]
    svc.store_turn("s-metrics", "hi", "hello", label="t")
    snap = METRICS.snapshot()
    assert snap["memory_ops_total"] == before + 1
    assert snap["turns_stored"] >= 1
    assert snap["latency_ms_avg"] > 0


def test_service_cache_hit_miss():
    svc = MemoryService(cache_ttl=60)
    miss = svc.cache_lookup("unique-q-xyz", label="m")
    assert miss["hit"] is False
    svc.cache_store("unique-q-xyz", "answer", label="s")
    hit = svc.cache_lookup("unique-q-xyz", label="h")
    assert hit["hit"] is True
    assert hit["value"] == "answer"
