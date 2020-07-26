# option flags
from enum import Enum
from typing import Mapping, MutableMapping, cast


from ._typing import MimeTypeTolerant


class MimeType(Enum):
    JSON = "application/json"
    YAML = "application/yaml"
    BSON = "application/bson"
    PROTO = "application/protobuf"
    TEXT = "text/plain"

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.split(";")[0]
        return text.lower().replace("x-", "")

    @classmethod
    def is_mimetype(cls, value: MimeTypeTolerant, mimetype: "MimeType") -> bool:
        """
        Checks if string or enum is equivalent to a given mimetype enum value.
        Similar to ``isinstance()`` or ``issubclass()``.

        :param value: to check
        :param mimetype: to check against.

        :return: True: is equivalent. False: is not Equivalent.

        Does some cleaning (such as resolving case and removing 'x-' from type).

        For instance, all of the following will pass equivalence for ``MimeType.YAML``:

            - 'application/yaml'

            - 'application/YAML'

            - 'application/x-yaml'

            - 'yaml'

            - 'x-yaml'
        """
        if isinstance(value, MimeType):
            return value is mimetype
        else:
            try:
                cleaned = cls._clean_text(value)  # type: ignore
            except AttributeError:
                return False

            return (
                mimetype.value.endswith(cleaned)
                or mimetype.value.startswith(cleaned)
                or cleaned == mimetype
            )

    @classmethod
    def from_name(cls, value: MimeTypeTolerant) -> "MimeType":
        """
        Returns enum for given name. Does some cleaning (such as resolving case and
        removing 'x-' from type.)

        :param value: Value to convert to enum.

        :raises ValueError: No MimeType enum for value.
        """
        try:
            return next(m for m in cls if cls.is_mimetype(value, m))
        except StopIteration:
            raise ValueError(f"No MimeType known for {value}")

    @classmethod
    def to_string(cls, value: MimeTypeTolerant) -> str:
        """
        Get string value for given enum or string mimetype.

        :param value: Incoming value
        :return: String representation.

        :raises ValueError: If mimetype is ``None``.
        """
        try:
            return cls.from_name(value).value
        except ValueError:
            if value is None:
                raise ValueError("Mimetype is None")
            else:
                value = cast(str, value)
                return value

    @staticmethod
    def add_to_headers(
        headers: MutableMapping[str, str], mimetype: MimeTypeTolerant
    ) -> None:
        """
        Add 'Content-Type' header for mimetype.

        :param headers: headers obj
        :param mimetype: to add
        :return:
        """
        if mimetype is None:
            return
        else:
            headers["Content-Type"] = MimeType.to_string(mimetype)

    @classmethod
    def from_headers(cls, headers: Mapping[str, str]) -> MimeTypeTolerant:
        """
        Get mimetype from 'Content-Type' value of headers.

        :param headers: to fetch from.
        :return: mimetype.

        If known mimetype, enum value will be returned. If 'Content-Type' is not in
        headers, None is returned.
        """
        name = headers.get("Content-Type")
        try:
            return cls.from_name(name)
        except ValueError:
            return name
