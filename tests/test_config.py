"""Smoke tests so CI is green from day one."""

from llmgateway import __version__
from llmgateway.config import get_settings


def test_version_is_set():
    assert __version__


def test_cache_threshold_is_sane():
    settings = get_settings()
    # Similarity threshold must stay in [0, 1]; a bad default silently breaks caching.
    assert 0.0 <= settings.cache_similarity_threshold <= 1.0
