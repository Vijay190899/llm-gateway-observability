# ADR-0003: Local embedding and mock provider so the stack runs offline

- **Status:** Accepted
- **Date:** 2026-07-27

## Context

Two parts of the gateway would normally reach an external paid API just to
demonstrate them: the semantic cache needs an embedding model, and completions
need an LLM provider. Requiring OpenAI/Anthropic keys to see the system work
end-to-end makes it fragile to demo, costs money on every click, and blocks CI.

## Decision

Make both boundaries pluggable, with an offline default:

- **Embeddings** (`embeddings.py`): a deterministic signed feature-hashing
  embedding over word unigrams + bigrams, L2-normalized. Dependency-free and
  stable across processes (hashlib, not the salted builtin `hash`). Cosine
  similarity of these vectors captures prompt overlap well enough to show real
  cache hits. The public surface is one `embed(text)` function, so a real
  embedding model can replace it without touching the cache.
- **Providers** (`providers.py`): a `Router` that selects an upstream by model
  name and **falls back to an in-process `MockProvider`** when no key is set.
  Real OpenAI/Anthropic providers activate automatically when their key exists.

## Consequences

- `docker compose up` gives a fully working gateway + dashboard with no secrets
  and no spend; add a key to route real traffic through the same path.
- The local embedding is a similarity *stand-in*, not a semantic model: it keys
  on lexical overlap, so paraphrases with no shared words won't hit. Documented
  as the tradeoff for zero-dependency operation; swap in real embeddings for
  production-grade semantics.
- Cost/latency numbers in the demo come from the mock provider's estimates, and
  are labelled as such.
