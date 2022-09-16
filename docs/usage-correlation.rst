Correlation ID
==============

A unique, random correlation ID will be sent with each request.
The value can be set, when creating the ``Session`` object.
If not set, a random ID will be generated automatically.

The header name defaults to ``X-Request-ID``.
A different one can be set, by passing it with the ``request_id_header`` argument to the ``Session`` constructor.
The name of the header that is sent, will be in the header ``Access-Control-Expose-Headers``.

If an ID already exists, e.g. when inside a micro services chain, pass the ID on to the Kelvin REST API server with ``Session(..., request_id="a1b2c3d4e5")``.
