import uuid
from typing import Optional, Dict, List, Type

from .._errors import SpanError


class APIError(SpanError):
    """Base error returned by SpanAPI in http responses. Must have a unique code."""

    http_code: int = 501
    api_code: int = 1000

    def __init__(
        self,
        message: str,
        error_data: Optional[dict] = None,
        error_id: Optional[uuid.UUID] = None,
        send_media: bool = False,
    ):
        """
        Base error returned by SpanAPI in http responses. Must have a unique code.

        :param message: Message to be sent back to client.
        :param error_data: JSON data to be encoded in headers.
        :param error_id: Assigned uuid for error.
        :param send_media: Whether to attempt to send a json payload in the response.
        """
        super().__init__(message)
        if error_id is None:
            error_id = uuid.uuid4()

        self.error_data: Optional[dict] = error_data
        self.id: uuid.UUID = error_id
        self.send_media: bool = send_media


class InvalidMethodError(APIError):
    """Invalid method requested from endpoint"""

    http_code: int = 405
    api_code: int = 1001


class NothingToReturnError(APIError):
    """No Data to Return"""

    http_code: int = 400
    api_code: int = 1002


class RequestValidationError(APIError):
    """Request Data Does not match schema"""

    http_code: int = 400
    api_code: int = 1003


class APILimitError(APIError):
    """Too many items for batch request"""

    http_code: int = 400
    api_code: int = 1004


class ResponseValidationError(APIError):
    """Server encountered error while validating response."""

    http_code: int = 400
    api_code: int = 1005


ERRORS_LIST: List[Type[APIError]] = [
    APIError,
    InvalidMethodError,
    NothingToReturnError,
    RequestValidationError,
    APILimitError,
    ResponseValidationError,
]
"""List of all APIError Classes"""


ERRORS_INDEXED: Dict[int, Type[APIError]] = {e.api_code: e for e in ERRORS_LIST}
"""All APIError exceptions indexed by their api error code."""
