"""Semantic cache + embedding behaviour."""

import pytest

from llmgateway import cache, embeddings, lsh
from llmgateway.store import MemoryBackend


def test_identical_prompts_are_near_1():
    a = embeddings.embed("summarize the quarterly earnings report")
    assert embeddings.cosine(a, a) == pytest.approx(1.0)


def test_similar_prompts_score_higher_than_unrelated():
    base = embeddings.embed("summarize the quarterly earnings report")
    close = embeddings.embed("please summarize the quarterly earnings report")
    far = embeddings.embed("write a haiku about the ocean")
    assert embeddings.cosine(base, close) > embeddings.cosine(base, far)


async def test_store_then_lookup_hits():
    backend = MemoryBackend()
    prompt = "what is the semantic cache hit rate"
    await cache.store(backend, prompt, {"answer": 42}, "mock-gpt", 0.01)
    hit = await cache.lookup(backend, prompt, threshold=0.95)
    assert hit is not None
    assert hit.response == {"answer": 42}
    assert hit.original_cost_usd == 0.01


async def test_unrelated_prompt_misses():
    backend = MemoryBackend()
    await cache.store(backend, "how do rate limits work", {"a": 1}, "mock-gpt", 0.01)
    assert await cache.lookup(backend, "recipe for banana bread", threshold=0.95) is None


async def test_lookup_scales_over_many_entries():
    """With thousands of distinct entries, LSH still finds the true match and
    only compares a bounded number of candidates (not the whole cache)."""
    backend = MemoryBackend()
    target = "how does the semantic cache index scale under load"
    await cache.store(backend, target, {"hit": True}, "mock-gpt", 0.02)
    for i in range(3000):
        await cache.store(backend, f"unrelated filler prompt number {i} about topic {i}", {"i": i}, "mock-gpt", 0.0)

    hit = await cache.lookup(backend, target, threshold=0.95)
    assert hit is not None and hit.response == {"hit": True}

    # The query's buckets hold far fewer entries than the full cache — that
    # smaller set is all a lookup ever compares against.
    probed = set()
    for bkey in lsh.bucket_keys(embeddings.embed(target)):
        probed.update(await backend.smembers(bkey))
    assert len(probed) < 500  # vs 3001 total entries
