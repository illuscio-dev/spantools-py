import uuid

from spantools import convert_params_headers


class TestConvertHeadersParams:
    def test_basic(self):
        id_value = uuid.uuid4()

        incoming = {"int": 10, "id": id_value, "string": "value"}

        convert_params_headers(incoming)

        assert incoming["int"] == "10"
        assert incoming["id"] == str(id_value)
        assert incoming["string"] == "value"

    def test_none(self):
        convert_params_headers(None)
