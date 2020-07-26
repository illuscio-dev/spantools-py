import pytest
import uuid
import datetime
import pytz
import grahamcracker
import marshmallow
import json
import csv
import io
import copy
import fractions
import decimal
from bson import BSON, Decimal128
from bson.raw_bson import RawBSONDocument
from dataclasses import dataclass, field
from typing import Mapping, List, Dict, Any
from proto import Echo

from spantools import (
    encode_content,
    decode_content,
    MimeType,
    ContentTypeUnknownError,
    ContentDecodeError,
    ContentEncodeError,
    NoContentError,
    DEFAULT_ENCODERS,
    DEFAULT_DECODERS,
)


def dt_factory():
    dt = datetime.datetime.now(tz=pytz.UTC)
    dt = dt.replace(microsecond=0)
    return dt


@dataclass
class DataToTest:
    string: str = "test string"
    num: int = 10
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    dt: datetime.datetime = field(default_factory=dt_factory)


@grahamcracker.schema_for(DataToTest)
class SchemaToTest(grahamcracker.DataSchema[DataToTest]):
    @marshmallow.validates("num")
    def must_be_10(self, value: int, **kwargs):
        if value != 10:
            raise marshmallow.ValidationError(message="Value Must be 10")


data_mimetypes_for_parametrize = [
    MimeType.JSON,
    "application/json",
    "application/JSON",
    "JSON",
    "json",
    MimeType.YAML,
    "application/yaml",
    "application/x-yaml",
    "application/YAML",
    "yaml",
    "YAML",
    "x-yaml",
    MimeType.BSON,
    "application/bson",
    "application/BSON",
    "application/x-bson",
    "x-bson",
    "BSON",
    "bson",
]


class TestBasicEncoding:
    @pytest.mark.parametrize("mimetype", data_mimetypes_for_parametrize)
    def encode_none(self, mimetype):
        assert encode_content(None, mimetype=mimetype) == b""

    @pytest.mark.parametrize("mimetype", data_mimetypes_for_parametrize)
    def test_data_round_trip(self, mimetype):
        data = {"key": 10}
        headers = dict()

        encoded = encode_content(data, mimetype=mimetype, headers=headers)
        print(str(encoded))

        assert isinstance(encoded, bytes)
        assert headers["Content-Type"] == MimeType.from_name(mimetype).value

        loaded, decoded = decode_content(encoded, mimetype=mimetype)

        assert dict(decoded) == dict(loaded) == data

    def test_sniff_json(self):
        data = {"key": 10}
        headers = dict()

        encoded = encode_content(data, mimetype=None, headers=headers)
        print(encoded.decode())

        assert isinstance(encoded, bytes)
        assert headers["Content-Type"] == MimeType.JSON.value

        loaded, decoded = decode_content(encoded, allow_sniff=True)

        assert decoded == loaded == data

    @pytest.mark.parametrize("mimetype", [MimeType.TEXT, "text/plain", "text", "plain"])
    def test_text_round_trip(self, mimetype):
        data = "test text"
        headers = dict()

        encoded = encode_content(data, mimetype=mimetype, headers=headers)
        print(encoded.decode())

        assert isinstance(encoded, bytes)
        assert headers["Content-Type"] == MimeType.TEXT.value

        loaded, decoded = decode_content(encoded, mimetype=mimetype)

        assert loaded == decoded == data
        assert isinstance(loaded, str)
        assert isinstance(decoded, str)

        assert not isinstance(loaded, bytes)
        assert not isinstance(decoded, bytes)

    def test_sniff_text_dump(self):
        data = "test text"
        headers = dict()

        encoded = encode_content(data, mimetype=None, headers=headers)
        print(encoded.decode())

        assert isinstance(encoded, bytes)
        assert headers["Content-Type"] == MimeType.TEXT.value

    @pytest.mark.parametrize("mimetype", data_mimetypes_for_parametrize)
    def test_schema_round_trip(self, mimetype):

        data = DataToTest()
        schema = SchemaToTest()
        headers = dict()

        encoded = encode_content(
            data, mimetype=mimetype, headers=headers, data_schema=schema
        )
        print(encoded.decode())

        assert isinstance(encoded, bytes)
        header_content_type = headers["Content-Type"]
        if mimetype is None:
            assert header_content_type == MimeType.JSON.value
        else:
            assert header_content_type == MimeType.from_name(mimetype).value

        loaded, decoded = decode_content(
            encoded, mimetype=mimetype, data_schema=schema, allow_sniff=True
        )

        assert isinstance(loaded, DataToTest)
        assert loaded == data

        assert isinstance(decoded, Mapping)

    @pytest.mark.parametrize("mimetype", data_mimetypes_for_parametrize)
    @pytest.mark.parametrize("feed_bson", [True, False])
    @pytest.mark.parametrize("feed_list", [True, False])
    def test_dump_bson_compatible_objects(
        self, mimetype, feed_bson: bool, feed_list: bool
    ):
        data = {
            "uuid": uuid.uuid4(),
            "datetime": dt_factory(),
            "bytes": b"Some Bin Data",
            "raw_bson": RawBSONDocument(
                BSON.encode({"key": "value", "nested": {"key": "value"}})
            ),
            "raw_bson_list": [
                RawBSONDocument(
                    BSON.encode({"key": "value", "nested": {"key": "value"}})
                ),
                RawBSONDocument(
                    BSON.encode({"key": "value", "nested": {"key": "value"}})
                ),
            ],
        }
        if feed_bson:
            data = RawBSONDocument(BSON.encode(data))
        if feed_list:
            data = [data, data]
        headers = dict()

        encoded = encode_content(data, mimetype=mimetype, headers=headers)
        try:
            print("ENCODED:", encoded.decode(), "", sep="\n")
        except BaseException:
            print("ENCODED:", encoded, "", sep="\n")

        loaded, decoded = decode_content(encoded, mimetype=mimetype)

        print("DECODED:", loaded, sep="\n")

        if feed_list:
            loaded = loaded[0]
            data = data[0]
            data = dict(data)
            data["raw_bson"] = dict(data["raw_bson"])
            data["raw_bson"]["nested"] = dict(data["raw_bson"]["nested"])

        assert str(loaded["uuid"]) == str(data["uuid"])
        assert set(loaded.keys()) == set(data.keys())

    def test_bson_single_list(self):
        data = [{"key": "value"}]
        encoded = encode_content(content=data, mimetype=MimeType.BSON)

        loaded, decoded = decode_content(encoded, mimetype=MimeType.BSON)
        assert isinstance(decoded, list)
        assert len(decoded) == 1
        assert isinstance(decoded[0], RawBSONDocument)
        assert dict(decoded[0]) == {"key": "value"}

    @pytest.mark.parametrize("content", ["Some Bin Data", "Some Bin Data".encode()])
    def test_unknown_mimetype(self, content):
        headers = dict()
        encoded = encode_content(content, "application/unknown", headers=headers)

        assert headers["Content-Type"] == "application/unknown"
        assert encoded == "Some Bin Data".encode()

    def test_validate_success(self):
        data = DataToTest()
        schema = SchemaToTest()

        encode_content(data, mimetype=MimeType.JSON, data_schema=schema, validate=True)

    def test_return_none(self):
        data = encode_content(content=None)
        assert data == b""

    @pytest.mark.parametrize("mimetype", [MimeType.JSON, MimeType.YAML])
    def test_json_encode_bson_types(self, mimetype: MimeType):
        encoder = DEFAULT_ENCODERS[mimetype]
        decoder = DEFAULT_DECODERS[mimetype]

        id_sample = uuid.uuid4()
        dt = datetime.datetime.now(tz=pytz.UTC)
        decimal_val = Decimal128(decimal.Decimal("1.2345"))
        with open("./zdevelop/tests/files/automation.png", mode="rb") as f:
            binary = f.read()

        data = {"id": id_sample, "dt": dt, "binary": binary, "decimal": decimal_val}

        encoded = encoder(data)
        print("ENCODED:", encoded)

        decoded = decoder(encoded)
        print("DECODED:", decoded)

        assert uuid.UUID(decoded["id"]) == id_sample
        assert (
            marshmallow.fields.DateTime()._deserialize(decoded["dt"], "attr", {}) == dt
        )
        assert bytes.fromhex(decoded["binary"]) == binary
        assert decimal.Decimal(decoded["decimal"]) == decimal_val.to_decimal()

    @pytest.mark.parametrize("mimetype", [MimeType.JSON, MimeType.YAML, MimeType.BSON])
    def test_encode_null(self, mimetype: MimeType):
        encoder = DEFAULT_ENCODERS[mimetype]
        decoder = DEFAULT_DECODERS[mimetype]

        encoded = encoder(None)
        assert encoded == b""


class TestErrors:
    def test_unknown_mimetype(self):
        with pytest.raises(ContentTypeUnknownError):
            encode_content({"key": "dict"}, "application/unknown")

    def test_unknown_mimetype_validation_error(self):
        data = DataToTest()
        schema = SchemaToTest()

        with pytest.raises(marshmallow.ValidationError):
            encode_content(
                data, mimetype="application/unknown", data_schema=schema, validate=True
            )

    def test_validate_failure(self):
        data = DataToTest()
        schema = SchemaToTest()

        data.num = 11

        with pytest.raises(marshmallow.ValidationError):
            encode_content(
                data, mimetype=MimeType.JSON, data_schema=schema, validate=True
            )

    def test_sniff_content_failure(self):
        with pytest.raises(ContentDecodeError):
            decode_content(b"Some Bin Data", mimetype=None, allow_sniff=True)

    def test_no_mimetype_disallow_sniff(self):
        with pytest.raises(ContentTypeUnknownError):
            decode_content(b"Some Bin Data", None)

    def test_no_decoder_for_mimetype(self):
        with pytest.raises(ContentTypeUnknownError):
            decode_content(b"Some Bin Data", mimetype="application/unknown")

    def test_json_decoder_error(self):
        with pytest.raises(ContentDecodeError):
            encoded = json.dumps("Some Data").encode()
            decode_content(encoded, mimetype=MimeType.JSON)

    def test_register_mimetype_encoders(self):

        from spantools import DEFAULT_ENCODERS, DEFAULT_DECODERS

        def csv_encode(data: List[dict]) -> bytes:
            encoded = io.StringIO()
            headers = list(data[0].keys())
            writer = csv.DictWriter(encoded, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
            return encoded.getvalue().encode()

        def csv_decode(data: bytes) -> List[Dict[str, Any]]:
            csv_file = io.StringIO(data.decode())
            reader = csv.DictReader(csv_file)
            return [row for row in reader]

        custom_encoders = copy.copy(DEFAULT_ENCODERS)
        custom_decoders = copy.copy(DEFAULT_DECODERS)

        custom_encoders["text/csv"] = csv_encode
        custom_decoders["text/csv"] = csv_decode

        data = [{"key": "value1"}, {"key": "value2"}]
        encoded = encode_content(data, mimetype="text/csv", encoders=custom_encoders)

        assert isinstance(encoded, bytes)

        loaded, decoded = decode_content(
            encoded, mimetype="text/csv", decoders=custom_decoders
        )
        assert loaded == decoded == data

    def test_encode_error(self):
        with pytest.raises(ContentEncodeError):
            output = encode_content(
                content={"key": fractions.Fraction("1/4")}, mimetype=MimeType.JSON
            )
            print(output)

    def test_no_content_error(self):
        """
        Tests that a 'NoContentError' is thrown when a blank byte-string is passed.
        """
        with pytest.raises(NoContentError):
            decode_content(b"")

    def test_no_content_is_decode_error(self):
        """
        Tests that a 'NoContentError' is a ContentDecodeError.
        """
        with pytest.raises(ContentDecodeError):
            decode_content(b"")

    def test_proto_schema_round_trip(self):
        """
        Tests that we can use protobuf classes as schemas.
        """

        echo = Echo(message="some message")

        serialized = encode_content(echo, mimetype=MimeType.PROTO, data_schema=Echo)

        assert isinstance(serialized, bytes)

        deserialized, raw = decode_content(serialized, MimeType.PROTO, Echo)

        assert isinstance(deserialized, Echo)
        assert echo.message == "some message"
        assert echo is not deserialized

        assert isinstance(raw, bytes)
        assert raw == serialized
