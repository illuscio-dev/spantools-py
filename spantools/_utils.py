from typing import Optional, MutableMapping, Any


def convert_params_headers(incoming: Optional[MutableMapping[str, Any]]) -> None:
    """
    Converts a str, Any mapping to a str, str mapping.

    :param incoming:
    :return:

    Useful for converting header and
    param dicts for requests before send, as many libraries require all values be
    strings.

    Dicts are converted in place through running str() on their values. This means that
    any non-string values should give proper values via str().
    """
    if not incoming:
        return

    for key, value in incoming.items():
        incoming[key] = str(value)
