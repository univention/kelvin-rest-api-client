Resource Status
===============

The ``Status`` resource is *not* represented in the LDAP tree.
It offers an endpoint to retrieve information about the state of the REST API service.

As a REST API is stateless, it is not possible to know the "health" of the service.
However load balancers need this information to know when to add/remove Kelvin nodes to/from a cluster.
As an approximation of the "health", the endpoint offers the number of "internal errors" (HTTP 500) that happened in the last minute.
Most common errors are misconfiguration and the inability to connect to upstream services (OpenLDAP and UDM REST API).

Kelvin API documentation
------------------------

Please see the `Kelvin API documentation section Resource Status`_ about allowed values for the attributes.


Status class
------------

The :py:class:`ucsschool.kelvin.client.Status` class has the following public attributes and methods:

.. code-block:: python

    class Status:
        def __init__(
            self,
            *,
            internal_errors_last_minute: int,
            version: str,
            url: str = None,
            session: Session = None,
            **kwargs,
        ):
            self.internal_errors_last_minute = internal_errors_last_minute
            self.version = version
            self.url = url
            self.session = session

        def as_dict(self) -> Dict[str, Any]:
            ...

        async def reload(self) -> School:
            ...

Note: Creation, modification and deletion of ``Status`` objects is not supported.

StatusResource class
--------------------

The :py:class:`ucsschool.kelvin.client.StatusResource` class has the following public attributes and methods:

.. code-block:: python

    class RoleResource(KelvinResource):
        def __init__(self, session: Session):
            ...
        async def get(self) -> Status:
            ...
        async def get_from_url(self, url: str) -> Status:
            ...


Create status
-------------

Status objects do not support creation.

Retrieve status
---------------

.. code-block:: python

    from ucsschool.kelvin.client import Session, StatusResource

    async with Session(**credentials) as session:
        status = await StatusResource(session=session).get()

    status.as_dict()
    {'internal_errors_last_minute': 0,
     'version': '1.7.0',
     'url': 'https://master.ucs.local/ucsschool/kelvin/v1/status'}


Search status
-------------

It is not possible to search for ``Status`` objects - there is only one.
They can however be updated to the current state of the server, by executing ``reload()``.

Change status properties
------------------------

Status objects do not support modification.

Move status
-----------

Status objects do not support moving.

Delete status
-------------

Status objects do not support deletion.


.. _`Kelvin API documentation section Resource Status`: https://docs.software-univention.de/ucsschool-kelvin-rest-api/resource-status.html
