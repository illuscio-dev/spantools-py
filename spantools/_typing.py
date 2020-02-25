from typing import Mapping, Any, Union


RecordType = Mapping[str, Any]
MimeTypeTolerant = Union["MimeType", str, None]

typing_help = False
if typing_help:
    from ._mimetype import MimeType  # noqa: F401
