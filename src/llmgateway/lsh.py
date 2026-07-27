"""Locality-sensitive hashing for the semantic cache.

A linear scan over every cached embedding does not scale — cost grows with the
cache size on every request. LSH makes lookup sub-linear: each embedding gets a
short binary signature per hash table (sign of its projection onto random
hyperplanes), and near-duplicate vectors land in the same bucket with high
probability. A lookup only compares against the handful of candidates sharing a
bucket, not the whole cache.

Using L independent tables preserves recall (a true match missed by one table is
usually caught by another). Hyperplanes are generated from a fixed seed so every
gateway replica computes identical buckets and can share one Redis index.
"""

from __future__ import annotations

import random

from .embeddings import DIM

TABLES = 8  # L: independent hash tables (recall)
BITS = 16  # k: bits per signature (selectivity)


def _make_planes() -> list[list[list[float]]]:
    rng = random.Random(20260727)  # fixed seed -> identical across processes
    return [[[rng.gauss(0, 1) for _ in range(DIM)] for _ in range(BITS)] for _ in range(TABLES)]


_PLANES = _make_planes()


def signatures(vec: list[float]) -> list[int]:
    """One integer signature per table for an embedding."""
    sigs: list[int] = []
    for planes in _PLANES:
        bits = 0
        for j, plane in enumerate(planes):
            if sum(v * p for v, p in zip(vec, plane, strict=False)) > 0.0:
                bits |= 1 << j
        sigs.append(bits)
    return sigs


def bucket_keys(vec: list[float], prefix: str = "cache:b") -> list[str]:
    """Redis set keys this vector belongs in / should be probed against."""
    return [f"{prefix}:{t}:{sig}" for t, sig in enumerate(signatures(vec))]
