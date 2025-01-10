from abc import ABC, abstractmethod
from datetime import timedelta


class SyncBackend(ABC):
    @abstractmethod
    def set(self, key: str, value: str | bytes, ex: int | timedelta) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get(self, key: str) -> bytes | None:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, pattern: str) -> None:
        raise NotImplementedError()


class AsyncBackend(ABC):
    @abstractmethod
    async def set(self, key: str, value: str | bytes, ex: int | timedelta) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def get(self, key: str) -> bytes | None:
        raise NotImplementedError()

    @abstractmethod
    async def delete(self, pattern: str) -> None:
        raise NotImplementedError()
