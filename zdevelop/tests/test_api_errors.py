import uuid
from spantools import errors_api


class TestAPIErrors:
    def test_index(self):
        for code, exc in errors_api.ERRORS_INDEXED.items():
            assert code == exc.api_code

    def test_generate_id(self):
        exc = errors_api.APIError("some error")

        assert isinstance(exc.id, uuid.UUID)

    def test_set_send_media(self):
        exc = errors_api.APIError("some error", send_media=True)
        assert exc.send_media is True
