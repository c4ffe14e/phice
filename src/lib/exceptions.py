class InvalidResponse(Exception):
    code: int = 500
    description: str = "Invaled response from API"


class NotFound(Exception):
    pass


class ResponseError(Exception):
    code: int = 500
    description: str = ""

    def __init__(self, desc: str) -> None:
        super().__init__()
        self.description = desc
