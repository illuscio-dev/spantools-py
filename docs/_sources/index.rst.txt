.. automodule:: spantools

.. islelib documentation master file, created by
   sphinx-quickstart on Mon Oct  1 00:18:03 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

spantools-py
------------

Spantools is a shared set of functions and errors between python `spanreed`_ libraries.

MimeType
--------

.. autoclass:: MimeType
   :members:

   Enum class for the default supported Content-Types / Mimetypes for decoding and
   encoding.

   =========== ======================
   Enum Attr   Text Value
   =========== ======================
   JSON        application/json
   YAML        application/yaml
   BSON        application/bson
   TEXT        text/plain
   =========== ======================

   .. automethod:: is_mimetype

   .. automethod:: from_name

   .. automethod:: to_string

   .. automethod:: add_to_headers

   .. automethod:: from_headers

Typing
------

.. data:: MimeTypeTolerant

   Typing alias for ``Union[MimeType, str, None]``.

.. data:: RecordType

   TypingAlias for ``Mapping[str, Any]``. This is a type often returned by http bodies
   when decoded from json, yaml, bson, etc.

Encoding and Decoding
---------------------

.. autofunction:: encode_content

.. autofunction:: decode_content

Models
------

.. autoclass:: Error
   :members:

.. autoclass:: PagingReq
   :members:

.. autoclass:: PagingResp
   :members:

Utility Functions
-----------------

.. autofunction:: convert_params_headers


Exceptions
----------

.. autoexception:: SpanError

.. autoexception:: ContentTypeUnknownError

.. autoexception:: ContentEncodeError

.. autoexception:: ContentDecodeError

.. autoexception:: NoContentError

.. autoexception:: NoErrorReturnedError

.. autoexception:: InvalidAPIErrorCodeError


API Exceptions
--------------

.. automodule:: spantools.errors_api

:class:`APIError` and exceptions that inherit from it are designed to be raised by
spanserver during the processing of a request, then transmitted back for handling.

API exceptions are found in this toolbox for libraries which wish to consume
these errors without installing spanserver and all of its dependencies.

These errors can be found in the ``spantools.errors_api`` submodule.

.. autoexception:: APIError

   **http code:** 501

   **api code:** 1000

   Returned when any exception not inherited from APIError is raised from a SpanRoute
   method.

   Init Values / Attributes
       * **message**: ``str``: error message passed back in response

       * **error_data**: ``Optional[dict]``: error data to be passed back in response

       * **send_data**: ``bool``: send regular response data as well as error. If
         ``False``: ``'data'`` object of response is set to ``None``

.. autoexception:: InvalidMethodError
   :members:

   **http code:** 405

   **api code:** 1001

   Returned when route does not support request method (POST/DELETE/GET/etc.).


.. autoexception:: NothingToReturnError

   **http code:** 400

   **api code:** 1002

   Returned when response schema is specified but the body to be returned is None, an
   empty list, or an empty dict.


.. autoexception:: RequestValidationError

   **http code:** 400

   **api code:** 1003

   Returned when request body does not match route schema or there was an error
   decoding the request body.


.. autoexception:: APILimitError

   **http code:** 400

   **api code:** 1004

   Request param exceeds limit


.. autoexception:: ResponseValidationError

   **http code:** 400

   **api code:** 1005

   Returned when response body does not match route schema or there was an error
   encoding the response body.

