import marshmallow
import google.protobuf.message
from typing import Mapping, Any, Union, Type


RecordType = Mapping[str, Any]
MimeTypeTolerant = Union["MimeType", str, None]
DataSchemaType = Union[marshmallow.Schema, Type[google.protobuf.message.Message]]

typing_help = False
if typing_help:
    from ._mimetype import MimeType  # noqa: F401
