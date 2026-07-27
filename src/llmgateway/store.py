"""Storage backend.

Redis in real deployments; an in-memory shim when Redis is unreachable so the
gateway (and its tests) run with zero infrastructure. Both expose the same small
async surface the rest of the app relies on -- nothing else should import redis.
"""

from __future__ import annotations

import fnmatch
import time
from collections import defaultdict
from typing import Protocol


class Backend(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ex: int | None = None) -> None: ...
    async def incr(self, key: str) -> int: ...
    async def expire(self, key: str, seconds: int) -> None: ...
    async def hincrbyfloat(self, key: str, field: str, amount: float) -> float: ...
    async def hgetall(self, key: str) -> dict[str, str]: ...
    async def rpush(self, key: str, value: str) -> None: ...
    async def ltrim(self, key: str, start: int, end: int) -> None: ...
    async def lrange(self, key: str, start: int, end: int) -> list[str]: ...
    async def sadd(self, key: str, member: str, ex: int | None = None) -> None: ...
    async def smembers(self, key: str) -> list[str]: ...
    async def srem(self, key: str, member: str) -> None: ...
    async def scan(self, match: str) -> list[str]: ...
    async def ping(self) -> bool: ...


class MemoryBackend:
    """Single-process fallback. Not durable; enough to run and test locally."""

    def __init__(self) -> None:
        self._str: dict[str, tuple[str, float | None]] = {}
        self._hash: dict[str, dict[str, float]] = defaultdict(dict)
        self._list: dict[str, list[str]] = defaultdict(list)
        self._set: dict[str, set[str]] = defaultdict(set)

    def _expired(self, key: str) -> bool:
        item = self._str.get(key)
        if item is None:
            return True
        _, exp = item
        if exp is not None and exp < time.time():
            del self._str[key]
            return True
        return False

    async def get(self, key: str) -> str | None:
        if self._expired(key):
            return None
        return self._str[key][0]

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._str[key] = (value, time.time() + ex if ex else None)

    async def incr(self, key: str) -> int:
        current = 0 if self._expired(key) else int(self._str[key][0])
        current += 1
        exp = self._str.get(key, (None, None))[1]
        self._str[key] = (str(current), exp)
        return current

    async def expire(self, key: str, seconds: int) -> None:
        if key in self._str:
            value, _ = self._str[key]
            self._str[key] = (value, time.time() + seconds)

    async def hincrbyfloat(self, key: str, field: str, amount: float) -> float:
        self._hash[key][field] = self._hash[key].get(field, 0.0) + amount
        return self._hash[key][field]

    async def hgetall(self, key: str) -> dict[str, str]:
        return {k: _fmt(v) for k, v in self._hash.get(key, {}).items()}

    async def rpush(self, key: str, value: str) -> None:
        self._list[key].append(value)

    async def ltrim(self, key: str, start: int, end: int) -> None:
        items = self._list.get(key, [])
        # Redis semantics: end is inclusive; -1 means last element.
        self._list[key] = items[start : (len(items) if end == -1 else end + 1)]

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        items = self._list.get(key, [])
        return items[start:] if end == -1 else items[start : end + 1]

    async def sadd(self, key: str, member: str, ex: int | None = None) -> None:
        self._set[key].add(member)

    async def smembers(self, key: str) -> list[str]:
        return list(self._set.get(key, set()))

    async def srem(self, key: str, member: str) -> None:
        self._set.get(key, set()).discard(member)

    async def scan(self, match: str) -> list[str]:
        return [k for k in self._str if fnmatch.fnmatch(k, match)]

    async def ping(self) -> bool:
        return True


class RedisBackend:
    """Adapter over redis.asyncio giving the same surface as MemoryBackend."""

    def __init__(self, client) -> None:
        self._c = client

    async def get(self, key):
        return await self._c.get(key)

    async def set(self, key, value, ex=None):
        await self._c.set(key, value, ex=ex)

    async def incr(self, key):
        return await self._c.incr(key)

    async def expire(self, key, seconds):
        await self._c.expire(key, seconds)

    async def hincrbyfloat(self, key, field, amount):
        return float(await self._c.hincrbyfloat(key, field, amount))

    async def hgetall(self, key):
        return await self._c.hgetall(key)

    async def rpush(self, key, value):
        await self._c.rpush(key, value)

    async def ltrim(self, key, start, end):
        await self._c.ltrim(key, start, end)

    async def lrange(self, key, start, end):
        return await self._c.lrange(key, start, end)

    async def sadd(self, key, member, ex=None):
        await self._c.sadd(key, member)
        # Bound bucket lifetime so stale membership self-heals alongside entries.
        if ex:
            await self._c.expire(key, ex)

    async def smembers(self, key):
        return list(await self._c.smembers(key))

    async def srem(self, key, member):
        await self._c.srem(key, member)

    async def scan(self, match):
        return [k async for k in self._c.scan_iter(match=match)]

    async def ping(self):
        return bool(await self._c.ping())


def _fmt(v: float) -> str:
    return str(int(v)) if v == int(v) else repr(v)


async def make_backend(redis_url: str) -> Backend:
    """Try Redis; fall back to in-memory if it is not reachable."""
    try:
        import redis.asyncio as redis

        client = redis.from_url(redis_url, decode_responses=True)
        backend = RedisBackend(client)
        await backend.ping()
        return backend
    except Exception:
        return MemoryBackend()
