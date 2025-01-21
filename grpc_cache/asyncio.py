from collections.abc import Callable, Coroutine
from datetime import timedelta
from functools import wraps
from inspect import signature
from logging import getLogger
from typing import Any

from google.protobuf.message import Message
from grpc import ServicerContext
from redis.exceptions import RedisError

from grpc_cache.types import AsyncBackend


__all__ = ["AsyncGRPCCache", "grpc_cache", "setup_grpc_cache"]


logger = getLogger(__name__)

gRPCAsyncMethod = Callable[[type, Message, ServicerContext], Coroutine[Any, Any, Message]]


class AsyncGRPCCache:
    """
    A caching utility for gRPC methods using Redis as a backend.

    This class provides decorators to cache gRPC responses based on specific message fields.

    Example:
        ```python
        from grpc_cache.asyncio import grpc_cache
        from grpc_cache.backends.redis import RedisAsyncBackend
        from redis.asyncio import Redis

        from my_proto.messages_pb2 import MyRequest, MyResponse, MyServicer


        redis = Redis.from_url("redis://localhost:6379/0")
        setup_grpc_cache(backend=RedisAsyncBackend(redis=redis), ex=timedelta(minutes=1))


        class MyService(MyServicer):
            @grpc_cache(fields_for_key=["field1", "field2"], ex=timedelta(minutes=5))
            async def MyMethod(self, request: MyRequest, context) -> MyResponse:
                # Perform some logic
                return MyResponse(result="Hello World")
        ```
    """

    def __init__(self) -> None:
        self._backend: AsyncBackend | None = None
        self.ex: int | timedelta | None = None

    def __call__(
        self,
        fields_for_key: list[str] | None = None,
        ex: int | timedelta | None = None,
        protobuf: Message = None,
        prefix: str = None,
    ) -> Callable[[gRPCAsyncMethod], gRPCAsyncMethod]:
        """
        Decorator to enable caching for a gRPC method.

        Args:
            fields_for_key: List of field names to construct the cache key.
            ex: Expiration time for the cache, in seconds or as a timedelta.
            protobuf: Protobuf message type for serialization (optional if return type is annotated).
            prefix: Optional prefix for cache keys.

        Returns:
            Decorator function.

        Example:
            ```python
            from grpc_cache.asyncio import grpc_cache

            from my_proto.messages_pb2 import MyRequest, MyResponse, MyServicer


            class MyService(MyServicer):
                @grpc_cache(fields_for_key=["field1", "field2"], ex=timedelta(minutes=5))
                async def MyMethod(self, request: MyRequest, context) -> MyResponse:
                    # Perform some logic
                    return MyResponse(result="Hello World")

                async def AnotherMethod(self, request: MyRequest, context) -> MyResponse:
                    await self.MyMethod.clear(request.field1, request.field2)  # clear cache for MyMethod
                    return MyResponse(result="Hello World")
            ```
        """

        if fields_for_key is None:
            fields_for_key = []

        ex = ex or self.ex

        if not isinstance(ex, int | timedelta):
            raise TypeError("ex must be an int or timedelta.")

        def inner(func: gRPCAsyncMethod) -> gRPCAsyncMethod:
            nonlocal protobuf, ex, prefix

            prefix = prefix or func.__qualname__
            func_signature = signature(func)

            if len(func_signature.parameters) != 3:
                raise ValueError("gRPC method signature must have 3 arguments.")

            protobuf = protobuf or func_signature.return_annotation

            if not protobuf or protobuf is func_signature.empty:
                raise ValueError("You must specify the protobuf argument or a return type annotation.")

            async def clear_cache(*args):
                """
                Callback for clearing cache while calling another gRPC method.

                Args:
                    *args: values for cache key
                """
                cache_key = ":".join([prefix, *args])
                try:
                    await self._backend.delete(pattern=cache_key)
                except RedisError as e:
                    logger.warning(f"Redis is unavailable: {e}")
                except Exception as e:
                    logger.warning(f"Unexpected error: {e}")

            func.clear = clear_cache

            @wraps(wrapped=func)
            async def wrapper(servicer, message, context) -> Message:
                """
                Wrapper function to handle caching logic.
                """

                # Construct the cache key
                key_parts = [prefix] + [f"{getattr(message, field)}" for field in fields_for_key]
                cache_key = ":".join(key_parts)

                try:
                    cached_response = await self._backend.get(key=cache_key)
                    if cached_response:
                        return protobuf.FromString(cached_response)
                except (TypeError, RedisError, AttributeError) as e:
                    if isinstance(e, RedisError | AttributeError):
                        logger.warning(f"Redis is unavailable: {e}")

                # Execute the original function and cache the result
                response = await func(servicer, message, context)
                cached_response = response.SerializeToString()

                try:
                    await self._backend.set(key=cache_key, value=cached_response, ex=ex)
                except (RedisError, AttributeError) as e:
                    logger.warning(f"Failed to cache response: {e}")

                return response

            return wrapper

        return inner

    def setup(self, backend: AsyncBackend, ex: int | timedelta) -> None:
        """
        Configures the gRPC cache.

        Args:
            ex: Default expiration time for the cache, in seconds or as a timedelta.
            backend: Backend storage.

        Example:
            ```python
            from grpc_cache.asyncio import setup_grpc_cache
            from grpc_cache.backends.redis import RedisAsyncBackend
            from redis.asyncio import Redis

            redis = Redis.from_url("redis://localhost:6379/0")
            setup_grpc_cache(backend=RedisAsyncBackend(redis=redis), ex=timedelta(minutes=1))
            ```
        """
        self._backend = backend
        self.ex = ex


grpc_cache = AsyncGRPCCache()
setup_grpc_cache = grpc_cache.setup
