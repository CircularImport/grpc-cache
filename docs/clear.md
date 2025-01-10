To delete the cache of a method when calling a linked method, you must call the `clear` method.

Examples:

Sync 
```python
@grpc_cache(fields_for_key=["user_id", "project_id"])
def MyMethod(self, request, context) -> Response:
    # Some logic
    return Response(...)

def AnotherMethod(self, request, context) -> AnotherResponse:
    self.MeMethod.clear(request.user_id, request.project_id)
    return AnotherResponse(...)
```

Async
```python
@grpc_cache(fields_for_key=["user_id", "project_id"])
async def MyMethod(self, request, context) -> Response:
    # Some logic
    return Response(...)

async def AnotherMethod(self, request, context) -> AnotherResponse:
    await self.MeMethod.clear(request.user_id, request.project_id)
    return AnotherResponse(...)
```

You can use wildcard to delete multiple cache entries.

```python
@grpc_cache(fields_for_key=["user_id", "page"])
async def List(self, request, context) -> Response:
    # Some logic
    return Response(...)

async def AnotherMethod(self, request, context) -> AnotherResponse:
    await self.List.clear(request.user_id, "*")
    return AnotherResponse(...)
```