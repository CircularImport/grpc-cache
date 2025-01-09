from datetime import timedelta

from grpc_cache import grpc_cache, setup_grpc_cache
from grpc_cache.backends.inmemory import InMemoryBackend
from tests.protobuf.test_pb2 import Empty, Request, Response
from tests.protobuf.test_pb2_grpc import MathServicer


backend = InMemoryBackend()
setup_grpc_cache(backend=backend, ex=timedelta(minutes=1))


class TestService(MathServicer):
    @grpc_cache(fields_for_key=["a", "b"])
    def Sum(self, request, context) -> Response:
        return Response(c=request.a + request.b)

    def Clear(self, request, context):
        self.Sum.clear(request.a, request.b)
        return Empty()


def test_sum() -> None:
    request = Request(a=1, b=2)
    service = TestService()
    response = service.Sum(request, None)
    assert backend._store.get("TestService.Sum:1:2").value == response.SerializeToString()


def test_clear() -> None:
    assert backend._store.get("TestService.Sum:1:2")
    request = Request(a=1, b=2)
    service = TestService()
    service.Clear(request, None)
    assert not backend._store.get("TestService.Clear:1:2")
