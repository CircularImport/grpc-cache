class GRPCCacheException(Exception):
    pass


class BackendError(GRPCCacheException):
    pass


class BackendUnavailableError(BackendError):
    pass
