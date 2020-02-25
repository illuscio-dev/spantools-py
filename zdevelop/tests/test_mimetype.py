import pytest
from spantools import MimeType


class TestMimeType:
    def test_is_mimetype_none(self):
        assert MimeType.is_mimetype(None, MimeType.JSON) is False

    def test_to_string_none_error(self):
        with pytest.raises(ValueError):
            MimeType.to_string(None)

    def test_add_none_to_headers(self):
        headers = dict()
        MimeType.add_to_headers(headers, None)

        assert headers == dict()

    @pytest.mark.parametrize(
        "mimetype", [m for m in MimeType] + ["application/unknown"]
    )
    def test_from_headers(self, mimetype):
        headers = {"Content-Type": MimeType.to_string(mimetype)}
        extracted = MimeType.from_headers(headers)

        if isinstance(mimetype, MimeType):
            assert extracted is mimetype
        else:
            assert extracted == mimetype

    @pytest.mark.parametrize(
        "name",
        [
            "application/json",
            "application/JSON",
            "application/Json",
            "JSON",
            "json",
            "jSON",
            "x-jSON",
            "application/x-json",
            "application/json; charset=utf-8",
        ],
    )
    def test_mimetype_parsing(self, name: str):
        assert MimeType.from_name(name) is MimeType.JSON
