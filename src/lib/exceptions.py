class NotFoundError(Exception):
    pass


class ResponseError(Exception):
    def __init__(self, message: str, *, code: int | None = None) -> None:
        super().__init__(message)
        self.message: str = message
        self.code: int | None = code


class ParsingError(Exception):
    pass
