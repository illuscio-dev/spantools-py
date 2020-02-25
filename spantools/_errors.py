class SpanError(BaseException):
    """
    Base Error for all Span-Libraries. Any library which wishes to be part of the
    spanreed family should inherit it's own base exception from this.
    """


class ContentTypeUnknownError(SpanError):
    """Could not complete operation with undefined or unregistered content type."""


class ContentDecodeError(SpanError):
    """Could not load data type."""


class NoContentError(ContentDecodeError):
    """No content to decode."""


class ContentEncodeError(SpanError):
    """Could not load data type."""


class NoErrorReturnedError(SpanError):
    """No Error in Headers"""


class InvalidAPIErrorCodeError(SpanError):
    """API Error code not recognized."""
