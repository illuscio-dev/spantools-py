import json
import pytest
from spantools import (
    Error,
    NoErrorReturnedError,
    InvalidAPIErrorCodeError,
    errors_api,
    PagingReq,
    PagingResp,
)


class CustomError(errors_api.APIError):
    api_code = 2001
    http_code = 405


class TestError:
    def test_from_exception_api(self):
        exc = CustomError("some error message", error_data={"key": "value"})
        error_info, exc_returned = Error.from_exception(exc)

        assert exc_returned is exc

        assert error_info.name == CustomError.__name__
        assert error_info.code == CustomError.api_code
        assert error_info.data == exc.error_data
        assert error_info.id == exc.id
        assert error_info.message == str(exc)

    def test_from_exception_non_api(self):

        exc = ValueError("some error message")
        error_info, exc_returned = Error.from_exception(exc)

        assert exc_returned is not exc
        assert type(exc_returned) is errors_api.APIError

        assert error_info.name == errors_api.APIError.__name__
        assert error_info.code == errors_api.APIError.api_code
        assert error_info.id == exc_returned.id
        assert error_info.message == "An unknown error occurred."

    def test_to_headers(self):
        exc = CustomError("some error message", error_data={"key": "value"})
        headers = dict()

        error_info, _ = Error.from_exception(exc)
        error_info.to_headers(headers)

        assert headers["error-name"] == CustomError.__name__
        assert headers["error-message"] == str(exc)
        assert headers["error-id"] == str(exc.id)
        assert headers["error-code"] == str(CustomError.api_code)
        assert headers["error-data"] == json.dumps({"key": "value"})

    def test_to_headers_no_data(self):
        exc = CustomError("some error message")
        headers = dict()

        error_info, _ = Error.from_exception(exc)
        error_info.to_headers(headers)

        assert "error-data" not in headers

    def test_error_from_headers(self):
        exc = CustomError("some error message", error_data={"key": "value"})
        headers = dict()

        error_info, _ = Error.from_exception(exc)
        error_info.to_headers(headers)

        from_headers = Error.from_headers(headers)

        assert from_headers == error_info

    def test_error_from_headers_no_data(self):
        exc = CustomError("some error message")
        headers = dict()

        error_info, _ = Error.from_exception(exc)
        error_info.to_headers(headers)

        from_headers = Error.from_headers(headers)

        assert from_headers == error_info

    def test_error_from_headers_no_error(self):
        headers = dict()

        with pytest.raises(NoErrorReturnedError):
            Error.from_headers(headers)

    def test_to_exception(self):
        exc = errors_api.APILimitError(
            "some error message", error_data={"key": "value"}
        )

        error_info, _ = Error.from_exception(exc)
        exc_generated = error_info.to_exception()

        assert type(exc_generated) is errors_api.APILimitError
        assert exc_generated.api_code == exc.api_code
        assert exc_generated.error_data == exc.error_data
        assert str(exc_generated) == str(exc)

    def test_to_exception_custom(self):
        exc = CustomError("some error message", error_data={"key": "value"})

        error_info, _ = Error.from_exception(exc)
        exc_generated = error_info.to_exception(
            errors_additional={CustomError.api_code: CustomError}
        )

        assert type(exc_generated) is CustomError
        assert exc_generated.api_code == exc.api_code
        assert exc_generated.error_data == exc.error_data
        assert str(exc_generated) == str(exc)

    def test_to_exception_error(self):
        exc = CustomError("some error message", error_data={"key": "value"})

        error_info, _ = Error.from_exception(exc)

        with pytest.raises(InvalidAPIErrorCodeError):
            error_info.to_exception()


class TestPaging:
    def test_to_params(self, paging_req: PagingReq):
        params = dict()
        paging_req.to_params(params)

        assert params["paging-offset"] == str(paging_req.offset)
        assert params["paging-limit"] == str(paging_req.limit)

    def test_from_params(self, paging_req: PagingReq):
        params = dict()
        paging_req.to_params(params)

        from_params = PagingReq.from_params(params)

        assert from_params == paging_req

    def test_from_params_defaults(self):
        params = dict()

        from_params = PagingReq.from_params(params, default_offset=0, default_limit=10)

        assert from_params.offset == 0
        assert from_params.limit == 10

    def test_from_params_offset_key_error(self):
        params = dict()

        with pytest.raises(KeyError):
            PagingReq.from_params(params, default_limit=10)

    def test_from_params_limit_key_error(self):
        params = dict()

        with pytest.raises(KeyError):
            PagingReq.from_params(params, default_offset=0)

    def test_to_headers(self, paging_resp: PagingResp):

        headers = dict()
        paging_resp.to_headers(headers)

        assert headers["paging-offset"] == str(paging_resp.offset)
        assert headers["paging-limit"] == str(paging_resp.limit)
        assert headers["paging-current-page"] == str(paging_resp.current_page)
        assert headers["paging-next"] == paging_resp.next
        assert headers["paging-previous"] == paging_resp.previous
        assert headers["paging-total-items"] == str(paging_resp.total_items)
        assert headers["paging-total-pages"] == str(paging_resp.total_pages)

    def test_headers_round_trip_optionals(self, paging_resp: PagingResp):

        paging_resp.previous = None
        paging_resp.next = None
        paging_resp.total_items = None
        paging_resp.total_pages = None

        headers = dict()
        paging_resp.to_headers(headers)

        from_headers = PagingResp.from_headers(headers)

        assert "paging-previous" not in headers
        assert "paging-next" not in headers
        assert "paging-total-items" not in headers
        assert "paging-total-pages" not in headers

        assert from_headers == paging_resp

    def test_from_headers(self, paging_resp: PagingResp):

        headers = dict()
        paging_resp.to_headers(headers)

        from_headers = PagingResp.from_headers(headers)

        assert from_headers == paging_resp
