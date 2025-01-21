from datetime import timedelta

from redis import Redis, RedisCluster
from redis.asyncio import Redis as AsyncRedis
from redis.asyncio import RedisCluster as AsyncRedisCluster
from redis.exceptions import ConnectionError as RedisConnectionError

from grpc_cache.exceptions import BackendError, BackendUnavailableError
from grpc_cache.types import AsyncBackend, SyncBackend


__all__ = ["AsyncRedisBackend", "RedisBackend"]


class AsyncRedisBackend(AsyncBackend):
    def __init__(self, redis: AsyncRedis | AsyncRedisCluster) -> None:
        self._redis = redis

    async def set(self, key: str, value: str | bytes, ex: int | timedelta) -> None:
        try:
            await self._redis.set(name=key, value=value, ex=ex)
        except RedisConnectionError as e:
            raise BackendUnavailableError from e
        except Exception as e:
            raise BackendError from e

    async def get(self, key: str) -> bytes | None:
        try:
            return await self._redis.get(name=key)
        except RedisConnectionError as e:
            raise BackendUnavailableError from e
        except Exception as e:
            raise BackendError from e

    async def delete(self, pattern: str) -> None:
        try:
            keys = await self._redis.keys(pattern=pattern)
            if keys:
                await self._redis.delete(*keys)
        except RedisConnectionError as e:
            raise BackendUnavailableError from e
        except Exception as e:
            raise BackendError from e


class RedisBackend(SyncBackend):
    def __init__(self, redis: Redis | RedisCluster) -> None:
        self._redis = redis

    def set(self, key: str, value: str | bytes, ex: int | timedelta) -> None:
        try:
            self._redis.set(name=key, value=value, ex=ex)
        except RedisConnectionError as e:
            raise BackendUnavailableError from e
        except Exception as e:
            raise BackendError from e

    def get(self, key: str) -> bytes | None:
        try:
            return self._redis.get(name=key)
        except RedisConnectionError as e:
            raise BackendUnavailableError from e
        except Exception as e:
            raise BackendError from e

    def delete(self, pattern: str) -> None:
        try:
            keys = self._redis.keys(pattern=pattern)
            self._redis.delete(*keys)
        except RedisConnectionError as e:
            raise BackendUnavailableError from e
        except Exception as e:
            raise BackendError from e
