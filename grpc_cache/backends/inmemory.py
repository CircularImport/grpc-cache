import re

from asyncio import Lock as AsyncLock
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any

from grpc_cache.types import AsyncBackend, SyncBackend


__all__ = ["AsyncInMemoryBackend", "InMemoryBackend"]


@dataclass
class Value:
    value: bytes
    ttl: datetime


class BaseInMemoryBackend:
    _store: dict[str, Value] = {}
    _lock: Any

    def _get(self, key: str) -> bytes | None:
        v = self._store.get(key)
        if not v:
            return None

        if v.ttl > datetime.now(tz=UTC):
            return v.value

        del self._store[key]


class AsyncInMemoryBackend(BaseInMemoryBackend, AsyncBackend):
    _lock = AsyncLock()

    async def set(self, key: str, value: str | bytes, ex: int | timedelta) -> None:
        if isinstance(value, str):
            value = value.encode()

        if isinstance(ex, int):
            ex = timedelta(seconds=ex)

        async with self._lock:
            self._store[key] = Value(value=value, ttl=datetime.now(tz=UTC) + ex)

    async def get(self, key: str) -> bytes | None:
        async with self._lock:
            return self._get(key)

    async def delete(self, pattern: str) -> None:
        pattern = pattern.replace("*", ".+")
        async with self._lock:
            for key in self._store:
                if re.fullmatch(pattern=pattern, string=key):
                    self._store.pop(key)


class InMemoryBackend(BaseInMemoryBackend, SyncBackend):
    _lock = Lock()

    def set(self, key: str, value: str | bytes, ex: int | timedelta) -> None:
        if isinstance(value, str):
            value = value.encode()

        if isinstance(ex, int):
            ex = timedelta(seconds=ex)

        with self._lock:
            self._store[key] = Value(value=value, ttl=datetime.now(tz=UTC) + ex)

    def get(self, key: str) -> bytes | None:
        with self._lock:
            return self._get(key)

    def delete(self, pattern: str) -> None:
        pattern = pattern.replace("*", ".+")
        with self._lock:
            for key in self._store:
                if re.fullmatch(pattern=pattern, string=key):
                    self._store.pop(key)
