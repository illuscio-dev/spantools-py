import pytest
from spantools import PagingReq, PagingResp


@pytest.fixture
def paging_req() -> PagingReq:
    return PagingReq(offset=20, limit=10)


@pytest.fixture
def paging_resp() -> PagingResp:
    return PagingResp(
        previous="www.someapi.com/items?offset=10&limit=10",
        next="www.someapi.com/items?offset=30&limit=10",
        current_page=3,
        offset=20,
        limit=10,
        total_pages=5,
        total_items=50,
    )
