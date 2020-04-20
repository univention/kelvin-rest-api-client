Resource Role
=============

The ``Role`` resource is *not* represented in the LDAP tree.
The objects exist only as a vehicle to classify user objects.

Kelvin API documentation
------------------------

Please see the `Kelvin API documentation section Resource Roles`_ about allowed values for the attributes.


Role class
----------

The :py:class:`ucsschool.kelvin.client.Role` class has the following attributes and methods:

.. code-block:: python

    class Role(KelvinObject):
        def __init__(
            self,
            name: str,
            *,
            display_name: str = None,
            url: str = None,
            session: Session = None,
        ):
            self.name = name
            self.display_name = display_name
            self.url = url
            self.session = session
            del self.dn
            del self.ucsschool_roles

        async def reload(self) -> School:
            ...

        async def save(self) -> School:
            raise NotImplementedError()

        async def delete(self) -> None:
            raise NotImplementedError()

        def as_dict(self) -> Dict[str, Any]:
            ...

Note: The Kelvin API does not yet support creating, changing or deleting role objects, and thus the Kelvin API client doesn't either.
Using ``Role.save()`` or ``Role.delete()`` will raise a :py:exc:`NotImplementedError` exception.


RoleResource class
------------------

The :py:class:`ucsschool.kelvin.client.RoleResource` class has the following public attributes and methods:

.. code-block:: python

    class RoleResource(KelvinResource):
        def __init__(self, session: Session):
            ...
        async def get(self, **kwargs) -> School:
            ...
        async def get_from_url(self, url: str) -> School:
            ...
        async def search(self, **kwargs) -> AsyncIterator[School]:
            ...



Create role
-----------

The Kelvin API does not yet support creating role objects, and thus the Kelvin API client doesn't either.


Retrieve role
-------------

.. code-block:: python

    from ucsschool.kelvin.client import Session, RoleResource

    async with Session(**credentials) as session:
        role = await RoleResource(session=session).get(name="student")

    role.as_dict()
    {'name': 'student',
     'display_name': 'student',
     'url': 'https://master.ucs.local/ucsschool/kelvin/v1/roles/student'}


Search roles
------------

The :py:meth:`search()` method allows searching for roles.
No filter argument are supported.

.. code-block:: python

    from ucsschool.kelvin.client import Session, RoleResource

    async with Session(**credentials) as session:
        async for role in RoleResource(session=session).search():
            print(role)

    Role('name'='staff')
    Role('name'='student')
    Role('name'='teacher')


Change role properties
----------------------

The Kelvin API does not yet support changing role objects, and thus the Kelvin API client doesn't either.

Move role
---------

Role objects do not support moving.

Delete role
-----------

The Kelvin API does not yet support deleting role objects, and thus the Kelvin API client doesn't either.


.. _`Kelvin API documentation section Resource Roles`: https://docs.software-univention.de/ucsschool-kelvin-rest-api/resource-roles.html
