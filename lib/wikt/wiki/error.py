"""Basic Wiki code parsing from a page."""

__all__ = ["WikiParserError"]


class WikiParserError(Exception):
    """Raised when parsing the wiki code fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
