import marshmallow
import datetime
import uuid
import bson
import yaml
import rapidjson
import decimal
from bson.raw_bson import RawBSONDocument
from typing import Any, Union, Mapping, List, Dict, Callable, Optional

from ._mimetype import MimeType, MimeTypeTolerant


EncoderType = Callable[[Any], bytes]
DecoderType = Callable[[bytes], Any]
DATETIME_FIELD: marshmallow.fields.DateTime = marshmallow.fields.DateTime()


def _convert_bson_doc(data: RawBSONDocument) -> Dict[str, Any]:
    try:
        dict_data = dict(data)
    except bson.InvalidBSON:
        dict_data = dict()

    return dict_data


class SpanJSONEncoder(rapidjson.Encoder):

    EMPTY: dict = dict()

    def default(self, obj: Any) -> Any:
        if isinstance(obj, bson.Decimal128):
            obj = obj.to_decimal()

        if isinstance(obj, datetime.datetime):
            return DATETIME_FIELD._serialize(obj, "none", SpanJSONEncoder.EMPTY)
        elif isinstance(obj, bytes):
            return obj.hex()
        elif isinstance(obj, RawBSONDocument):
            return _convert_bson_doc(obj)
        elif isinstance(obj, decimal.Decimal):
            return str(obj)
        else:
            raise ValueError(
                f"Value {obj} or type {obj.__class__} is not JSON-Serializable"
            )


JSON_ENCODER = SpanJSONEncoder(
    uuid_mode=rapidjson.UM_CANONICAL, bytes_mode=rapidjson.BM_NONE
)


DataMappingType = Optional[Union[Mapping[str, Any], List[Mapping[str, Any]]]]


def json_encode(media: DataMappingType) -> bytes:
    if media is None:
        return b""
    return JSON_ENCODER(media).encode()


def json_decode(content: bytes) -> DataMappingType:
    loaded = rapidjson.loads(content)
    if not isinstance(loaded, (dict, list)):
        raise ValueError("json did not decode to list or object")
    return loaded


def _yaml_represent_raw_bson_document(
    dumper: yaml.Dumper, data: RawBSONDocument
) -> dict:
    dict_data = _convert_bson_doc(data)
    return dumper.represent_dict(dict_data)


def _yaml_represent_bytes(dumper: yaml.Dumper, data: bytes) -> str:
    string = data.hex()
    return dumper.represent_str(string)


def _yaml_represent_uuid(dumper: yaml.Dumper, data: uuid.UUID) -> str:
    string = str(data)
    return dumper.represent_str(string)


def _yaml_represent_decimal(dumper: yaml.Dumper, data: decimal.Decimal) -> str:
    string = str(data)
    return dumper.represent_str(string)


def _yaml_represent_decimal_bson(dumper: yaml.Dumper, data: bson.Decimal128) -> str:
    converted = data.to_decimal()
    return _yaml_represent_decimal(dumper, converted)


def _yaml_represent_datetime(dumper: yaml.Dumper, data: bson.Decimal128) -> str:
    string = DATETIME_FIELD._serialize(data, "none", SpanJSONEncoder.EMPTY)
    return dumper.represent_str(string)


class SpanYamlEncoder(yaml.SafeDumper):
    pass


SpanYamlEncoder.add_representer(RawBSONDocument, _yaml_represent_raw_bson_document)
SpanYamlEncoder.add_representer(bytes, _yaml_represent_bytes)
SpanYamlEncoder.add_representer(uuid.UUID, _yaml_represent_uuid)
SpanYamlEncoder.add_representer(decimal.Decimal, _yaml_represent_decimal)
SpanYamlEncoder.add_representer(bson.Decimal128, _yaml_represent_decimal_bson)
SpanYamlEncoder.add_representer(datetime.datetime, _yaml_represent_datetime)


def yaml_encode(media: DataMappingType) -> bytes:
    if media is None:
        return b""
    return yaml.dump(media, Dumper=SpanYamlEncoder).encode()


def yaml_decode(content: bytes) -> DataMappingType:
    loaded = yaml.safe_load(content)  # type: ignore
    if not isinstance(loaded, (dict, list)):
        raise ValueError("yaml did not decode to list or object")
    return loaded


BSON_RECORD_DELIM = "\u241E".encode()
ENCODE_TYPES = Optional[
    Union[Mapping, RawBSONDocument, List[RawBSONDocument], List[Mapping]]
]


def _bson_encode_single(data: Union[RawBSONDocument, dict]) -> bytes:
    if isinstance(data, RawBSONDocument):
        return data.raw
    else:
        return bson.BSON.encode(data)


def bson_encode(data: ENCODE_TYPES) -> bytes:
    """
    Encodes ``data`` to bytes. BSON records in list are delimited by '\u241E'.
    """
    if data is None:
        return b""
    elif isinstance(data, list):
        encoded = BSON_RECORD_DELIM.join(_bson_encode_single(r) for r in data)
        # We are going to put a delimiter right at the head as a signal that this is
        # a list of bson files, even if it is only one record
        encoded = BSON_RECORD_DELIM + encoded
        return encoded
    else:
        return _bson_encode_single(data)


def bson_decode_list(content: bytes) -> List[RawBSONDocument]:
    record_raw_list = content.split(BSON_RECORD_DELIM)
    # The first record is always going to be blank.
    record_raw_list.pop(0)
    loaded_list: List[RawBSONDocument] = list()

    for record_raw in record_raw_list:
        loaded_list.append(RawBSONDocument(record_raw))

    return loaded_list


def bson_decode(content: bytes) -> Union[RawBSONDocument, List[RawBSONDocument]]:
    """
    Decodes ``content`` bytes to RawBSONDocument(s)
    """
    if content.startswith(BSON_RECORD_DELIM):
        return bson_decode_list(content)
    else:
        return RawBSONDocument(content)


# The proto encoders and decoders will just pass bytes through, since marshalling and
# unmarshalling will be handled by the schema
def proto_encode(data: bytes) -> bytes:
    return data


def proto_decode(content: bytes) -> bytes:
    return content


DEFAULT_ENCODERS: Dict[MimeTypeTolerant, EncoderType] = {
    MimeType.JSON: json_encode,
    MimeType.BSON: bson_encode,
    MimeType.YAML: yaml_encode,
    MimeType.TEXT: lambda x: x.encode(),
    MimeType.PROTO: proto_encode,
}

DEFAULT_DECODERS: Dict[MimeTypeTolerant, DecoderType] = {
    MimeType.JSON: json_decode,
    MimeType.BSON: bson_decode,
    MimeType.YAML: yaml_decode,
    MimeType.TEXT: lambda x: x.decode(),
    MimeType.PROTO: proto_decode,
}
