class RequestError(Exception):
    pass


class UnauthorizedError(RequestError):
    pass


class TooManyRequestsError(RequestError):
    pass
