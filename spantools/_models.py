import uuid
import json
from dataclasses import dataclass, field, fields
from typing import Optional, Tuple, Mapping, Dict, Type, MutableMapping

from .errors_api import APIError, ERRORS_INDEXED
from ._errors import NoErrorReturnedError, InvalidAPIErrorCodeError


@dataclass
class Error:
    """Model for error information."""

    name: str
    """Name of error class."""

    message: str
    """Description of error."""

    code: int
    """API error code. NOT the http code."""

    data: Optional[dict] = None
    """Arbitrary data dict with information about the error."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    """UUID for specific instance of raised error for bug fixing."""

    @classmethod
    def from_exception(cls, exc: BaseException) -> Tuple["Error", APIError]:
        """
        Creates Error object from mapping of response headers, and handles generation
        of :class:`APIError` from Non-APIError exceptions.

        :param exc: Instance of an BaseException
        :return:

        If ``exc`` does not inherit from APIError, a general APIError will be generated
        and returned alongside the Error dataclass.

        If ``exc`` does inherit from APIError, it will be passed through.
        """
        if not isinstance(exc, APIError):
            exc = APIError("An unknown error occurred.")

        error_data = cls(
            name=exc.__class__.__name__,
            message=str(exc),
            code=exc.api_code,
            data=exc.error_data,
            id=exc.id,
        )

        return error_data, exc

    @classmethod
    def from_headers(cls, headers: Mapping[str, str]) -> "Error":
        """
        Creates Error object from mapping of response headers.

        :param headers:
        :return:
        """
        data = headers.get("error-data", None)
        if data is not None:
            data_loaded = json.loads(data)
        else:
            data_loaded = None

        try:
            error_data = cls(
                name=headers["error-name"],
                message=headers["error-message"],
                code=int(headers["error-code"]),
                data=data_loaded,
                id=uuid.UUID(headers["error-id"]),
            )
        except KeyError:
            raise NoErrorReturnedError("No or incomplete error data found in headers.")

        return error_data

    def to_exception(
        self, errors_additional: Optional[Dict[int, Type[APIError]]] = None
    ) -> APIError:
        """
        Generate APIError object for given error information.

        :param errors_additional: Additional custom APIError classes for possible raise.

        :return: BaseException instance with message, .api_code, .error_data and
            .error_id

        :raises InvalidErrorCodeError: when error class with correct api_code not
            supplied.
        """

        if errors_additional is None:
            errors_additional = dict()
        errors_additional.update(ERRORS_INDEXED)

        try:
            error_class = errors_additional[self.code]
        except KeyError:
            raise InvalidAPIErrorCodeError(
                f"Error class with code {self.code} not supplied."
            )

        error = error_class(self.message, error_data=self.data, error_id=self.id)

        return error

    def to_headers(self, headers: MutableMapping) -> None:
        """
        Adds error info to response headers in-place.

        :param headers:
        :return:

        All values are converted to strings before being added. Optional fields whose
        values are None are skipped.

        All header keys are prefixed with ``"error-"``.
        """
        # Set the header error info
        headers["error-name"] = self.name
        headers["error-message"] = self.message
        headers["error-id"] = str(self.id)
        headers["error-code"] = str(self.code)
        if self.data:
            headers["error-data"] = json.dumps(self.data)


@dataclass
class PagingReq:
    """Paging info for requests."""

    offset: int
    """Offset sent to params of request."""

    limit: int
    """Limit sent to params of request."""

    def to_params(self, params: MutableMapping[str, str]) -> None:
        """
        Adds paging info to URL params for request.

        :param params:
        :return:

        All values are converted to strings before being added.

        All param names are prefixed with ``"paging-"`` and underscores are replaces
        with hyphens.
        """
        params["paging-offset"] = str(self.offset)
        params["paging-limit"] = str(self.limit)

    @classmethod
    def from_params(
        cls,
        params: MutableMapping[str, str],
        default_offset: Optional[int] = None,
        default_limit: Optional[int] = None,
    ) -> "PagingReq":
        """
        Creates PagingReq object from mapping of request url params.

        :param params:
        :param default_offset: offset to use if None is supplied
        :param default_limit: limit to use if None is supplied
        :return:

        :raises KeyError: If offset or limit is not supplied and no default is given.
        """
        try:
            offset = int(params["paging-offset"])
        except KeyError as error:
            if default_offset is None:
                raise error
            else:
                offset = default_offset

        try:
            limit = int(params["paging-limit"])
        except KeyError as error:
            if default_limit is None:
                raise error
            else:
                limit = default_limit

        return cls(offset=offset, limit=limit)


@dataclass
class PagingResp(PagingReq):
    """Paging info for responses."""

    total_items: Optional[int]
    """Total number of returnable items."""

    current_page: int
    """Current page index (starting at one)."""

    previous: Optional[str]
    """Previous page url."""

    next: Optional[str]
    """Next page url"""

    total_pages: Optional[int]
    """Number of total pages."""

    def to_headers(self, headers: MutableMapping[str, str]) -> None:
        """
        Adds paging info to request headers in-place.

        :param headers:
        :return:

        All values are converted to strings before being added. Optional fields whose
        values are None are skipped.

        All header keys are prefixed with ``"paging-"`` and underscores are replaces
        with hyphens.
        """

        for paging_field in fields(self):

            value = getattr(self, paging_field.name)
            key = f"paging-{paging_field.name.replace('_', '-')}"

            if value is None:
                continue

            headers[key] = str(value)

    @classmethod
    def from_headers(cls, headers: Mapping[str, str]) -> "PagingResp":
        """
        Creates PagingResp object from mapping of response headers.

        :param headers:
        :return:
        """
        previous_url = headers.get("paging-previous")
        next_url = headers.get("paging-next")

        total_pages = headers.get("paging-total-pages")
        if total_pages is not None:
            total_pages_loaded: Optional[int] = int(total_pages)
        else:
            total_pages_loaded = None

        total_items = headers.get("paging-total-items")
        if total_items is not None:
            total_items_loaded: Optional[int] = int(total_items)
        else:
            total_items_loaded = None

        paging_data = cls(
            previous=previous_url,
            next=next_url,
            current_page=int(headers["paging-current-page"]),
            offset=int(headers["paging-offset"]),
            limit=int(headers["paging-limit"]),
            total_pages=total_pages_loaded,
            total_items=total_items_loaded,
        )

        return paging_data
