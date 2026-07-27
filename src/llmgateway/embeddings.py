"""Prompt embedding for the semantic cache.

Uses signed feature hashing over word unigrams and bigrams into a fixed-width
L2-normalized vector. It is deterministic, dependency-free, and fast, so the
cache works end-to-end with no embedding API or model download. The interface
is a single `embed(text) -> list[float]`; swap in OpenAI/sentence-transformers
here without touching the cache if you want richer semantics.
"""

from __future__ import annotations

import hashlib
import math
import re

DIM = 256
_WORD = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    words = _WORD.findall(text.lower())
    bigrams = [f"{a}_{b}" for a, b in zip(words, words[1:])]
    return words + bigrams


def _bucket(token: str) -> tuple[int, float]:
    # hashlib, not builtin hash(): stable across processes so cached embeddings
    # stay comparable after a restart.
    h = int.from_bytes(hashlib.md5(token.encode()).digest()[:4], "big")
    sign = 1.0 if (h >> 31) & 1 else -1.0
    return h % DIM, sign


def embed(text: str) -> list[float]:
    vec = [0.0] * DIM
    for tok in _tokens(text):
        idx, sign = _bucket(tok)
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        return vec
    return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
