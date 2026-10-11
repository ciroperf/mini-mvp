import os
import time
from typing import Protocol

REDIS_URL = os.getenv("REDIS_URL")
CACHE_TTL_SECONDS = 120


class CacheClient(Protocol):
    async def get(self, key: str) -> str | None: ...

    async def set(self, key: str, value: str, ex: int) -> None: ...

    async def delete(self, *keys: str) -> None: ...


class _InMemoryCache:
    """Fallback usato quando REDIS_URL non e' configurato (es. nei test)."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, str]] = {}

    async def get(self, key: str) -> str | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: str, ex: int) -> None:
        self._store[key] = (time.monotonic() + ex, value)

    async def delete(self, *keys: str) -> None:
        for key in keys:
            self._store.pop(key, None)


def _build_client() -> CacheClient:
    if REDIS_URL:
        from redis.asyncio import from_url

        return from_url(REDIS_URL, decode_responses=True)
    return _InMemoryCache()


_cache_client = _build_client()


async def get_cache() -> CacheClient:
    return _cache_client
