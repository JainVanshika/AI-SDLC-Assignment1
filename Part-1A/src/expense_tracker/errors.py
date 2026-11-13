"""The one error type of the library: a stable code, a message and the field at fault."""


class ExpenseError(Exception):
    """Raised for every refused request. `code` is stable; `field` names the offending input."""

    def __init__(self, code: str, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field
