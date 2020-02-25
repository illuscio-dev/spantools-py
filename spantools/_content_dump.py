import marshmallow
from typing import Optional, Any, Union, Mapping, MutableMapping, Callable

from ._mimetype import MimeType, MimeTypeTolerant
from ._errors import ContentTypeUnknownError, ContentEncodeError
from ._encoders import EncoderType, DEFAULT_ENCODERS


EncoderIndexType = Mapping[MimeTypeTolerant, EncoderType]


def _auto_mimetype(
    content: Optional[Any],
    mimetype: MimeTypeTolerant,
    data_schema: Optional[marshmallow.Schema],
) -> MimeTypeTolerant:
    """
    Supplies automatically determined mimetype for serialization if none was explicitly
    declared (will be either JSON or TEXT)
    """
    if mimetype is None:
        if data_schema is not None or isinstance(content, (Mapping, list)):
            mimetype = MimeType.JSON
        elif isinstance(content, str):
            mimetype = MimeType.TEXT

    return mimetype


def _check_unknown_mimetype_content(
    content: Optional[Any], mimetype: Optional[Union[MimeType, str]]
) -> None:
    """Checks that unknown content is something we can encode without an encoder."""
    # If it is not a valid mimetype spanreed is aware of then the content MUST
    # already be bytes or a string, since spanreed won't know how to decode it.
    if not isinstance(content, (str, bytes)):
        raise ContentTypeUnknownError(
            f"mimetype '{mimetype}' is unknown but content is not serialized"
        )


class _SchemaDumpEncode:
    """
    This class acts as an encoder, taking a single ``content`` argument, but has all the
    information to dump / validate content through a schema if the settings require it.
    """

    def __init__(
        self,
        schema_method: Callable,
        encoder: Optional[EncoderType],
        validator: Optional[Callable],
    ):
        self.schema_method: Callable = schema_method
        self.encoder: Optional[EncoderType] = encoder
        self.validator: Optional[Callable] = validator

    def __call__(self, content: Any) -> bytes:
        dumped = self.schema_method(content)
        if self.validator is not None:
            errors = self.validator(dumped)
            if errors:
                raise marshmallow.ValidationError(message=errors)

        if self.encoder is not None:
            return self.encoder(dumped)
        else:
            return dumped.encode()


def _generate_schema_encoder(
    data_schema: marshmallow.Schema,
    validate: bool,
    mimetype_encoder: Optional[EncoderType],
) -> EncoderType:
    schema_method = data_schema.dump
    validator = None

    if validate is True:
        validator = data_schema.validate

    schema_encoder = _SchemaDumpEncode(
        schema_method=schema_method, encoder=mimetype_encoder, validator=validator
    )
    return schema_encoder


def _byte_pass_through(content: Union[bytes, str]) -> bytes:
    if isinstance(content, str):
        content = content.encode()
    return content


def _get_mimetype_encoder(
    content: Optional[Any],
    mimetype: MimeTypeTolerant,
    validate: bool,
    encoders: EncoderIndexType,
) -> EncoderType:
    try:
        mimetype = MimeType.from_name(mimetype)
    except ValueError:
        pass

    try:
        encoder = encoders[mimetype]
    except KeyError:
        if validate is True:
            raise marshmallow.ValidationError("Unknown mimetype could not be validated")

        _check_unknown_mimetype_content(content, mimetype)
        encoder = _byte_pass_through

    return encoder


def _encode_known_mimetype(
    content: Optional[Any],
    mimetype: MimeTypeTolerant,
    headers: MutableMapping[str, str],
    data_schema: Optional[marshmallow.Schema],
    validate: bool,
    encoders: EncoderIndexType,
) -> bytes:
    # Otherwise if this is a mimetype known to spanreed, we can serialize it.
    if content is None:
        return b""
    encoder = _get_mimetype_encoder(content, mimetype, validate, encoders)

    # Put the mimetype into the headers as-is
    if mimetype is not None:
        MimeType.add_to_headers(headers, mimetype)

    if data_schema is not None:
        encoder = _generate_schema_encoder(
            data_schema=data_schema, validate=validate, mimetype_encoder=encoder
        )

    try:
        content = encoder(content)
    except marshmallow.ValidationError as error:
        raise error
    except BaseException:
        raise ContentEncodeError("Error while encoding content")

    return content


def encode_content(
    content: Optional[Any],
    mimetype: MimeTypeTolerant = None,
    headers: Optional[MutableMapping[str, str]] = None,
    data_schema: Optional[marshmallow.Schema] = None,
    validate: bool = False,
    encoders: Optional[EncoderIndexType] = None,
) -> bytes:
    """
    Encodes content object to bytes using encoder / schema.

    :param content: Object to be encoded.
    :param mimetype: Content-Type to serialize to.
    :param headers: Request headers to which content information should be added.
    :param data_schema: Marshmallow schema. Will be used to dump / validate content
        before encoding.
    :param validate: Whether to validate content after dumping. This may come with a big
        performance penalty.
    :param encoders: Custom set of encoders to use for encoding content.

    :return: Encoded content for request.

    :raises ContentTypeUnknownError: If a method for serializing / validating the
        content is unknown and the content is not already bytes.
    :raises ContentEncodeError: If error occurs when encoding content.
    :raises marshmallow.ValidationError: If raised while dumping / validating content
        via ``data_schema``.
    """
    # If there is no content, we can just return
    if content is None:
        return b""
    if headers is None:
        headers = dict()
    if encoders is None:
        encoders = DEFAULT_ENCODERS

    mimetype = _auto_mimetype(content, mimetype, data_schema)
    content = _encode_known_mimetype(
        content, mimetype, headers, data_schema, validate, encoders
    )

    return content
