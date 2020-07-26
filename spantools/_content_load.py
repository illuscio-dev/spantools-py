import marshmallow
from typing import Any, Union, Optional, Tuple, Mapping

from ._mimetype import MimeType, MimeTypeTolerant
from ._errors import ContentDecodeError, ContentTypeUnknownError, NoContentError
from ._encoders import DecoderType, DEFAULT_DECODERS
from ._typing import DataSchemaType


DecoderIndexType = Mapping[MimeTypeTolerant, DecoderType]


def _sniff_content(content: bytes, decoders: DecoderIndexType) -> Any:
    content_mapping = None

    for mimetype, decoder in decoders.items():
        # both text and protobuf are non-sniffable.
        if mimetype in (MimeType.TEXT, MimeType.PROTO):
            continue

        try:
            content_mapping = decoder(content)
        except BaseException:
            continue
        else:
            break

    if content_mapping is None:
        raise ContentDecodeError("Could not deserialize content")

    return content_mapping


def _load_content_by_mimetype(
    content: bytes, mimetype: Union[str, MimeType], decoders: DecoderIndexType
) -> Any:
    try:
        mimetype = MimeType.from_name(mimetype)
    except ValueError:
        pass

    try:
        deserializer = decoders[mimetype]
    except KeyError:
        raise ContentTypeUnknownError(f"Unknown mimetype: {mimetype}")

    try:
        return deserializer(content)
    except BaseException:
        raise ContentDecodeError(f"Error occurred while decoding content as {mimetype}")


def decode_content(
    content: bytes,
    mimetype: MimeTypeTolerant = None,
    data_schema: Optional[DataSchemaType] = None,
    allow_sniff: bool = False,
    decoders: Optional[DecoderIndexType] = None,
) -> Tuple[Optional[Any], Optional[Any]]:
    """
    Loads content by decoder / schema from received mimetype.

    :param content: Received binary body.
    :param mimetype: mimetype info if known.
    :param data_schema: marshmallow schema to use to load data to model / object
    :param allow_sniff: If mimetype is unavailable, whether to attempt to load content
        anyway.
    :param decoders: Custom set of decoders to use.
    :return: (loaded data object, loaded mimetype) tuple.

    :raises ContentTypeUnknownError: If a method for decoding / validating the
        content is unknown or unregistered, and ``allow_sniff`` is False.
    :raises ContentDecodeError: If error occurs when decoding content or no registered.
        decoders succeed if ``allow_sniff`` is True
    :raises NoContentError: If no content is passed to be decoded. This error is
        inherited from ContentDecodeError, so catching ContentDecodeError also catches
        NoContentError.
    :raises marshmallow.ValidationError: If raised while loading content via
        ``data_schema``.
    """
    if content == b"":
        raise NoContentError("No content to decode.")

    if decoders is None:
        decoders = DEFAULT_DECODERS

    # If no mimetype was passed, we can go through and attempt to load it blind (sniff).
    if mimetype is None and allow_sniff:
        content_mimetype = _sniff_content(content, decoders=decoders)
    # Otherwise if we are not allowing that, raise a value error.
    elif mimetype is None:
        raise ContentTypeUnknownError("No mimetype supplied.")
    # Or if there is an explicit mimetyoe, use its deserializer
    else:
        content_mimetype = _load_content_by_mimetype(
            content, mimetype=mimetype, decoders=decoders
        )

    # Use the marshmallow schema to load the data object.
    if data_schema is not None:
        if isinstance(data_schema, marshmallow.Schema):
            content_loaded = data_schema.load(content_mimetype)
        else:
            content_loaded = data_schema()
            content_loaded.ParseFromString(content)
    else:
        content_loaded = content_mimetype

    return content_loaded, content_mimetype
