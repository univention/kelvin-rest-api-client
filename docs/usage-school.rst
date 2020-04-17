Resource School
===============

The ``School`` resource is represented in the LDAP tree as ``OU`` objects.

To list those LDAP objects run in  a terminal:

.. code-block:: console

    FILTER='objectClass=ucsschoolOrganizationalUnit'
    univention-ldapsearch -LLL "$FILTER"

UCS\@school uses the UDM to access the LDAP directory.
UDM properties have different names than their associated LDAP attributes.
Their values may also differ.
To list the same UDM objects as above, run:

.. code-block:: console

    $ FILTER='objectClass=ucsschoolOrganizationalUnit'
    $ udm container/ou list --filter "$FILTER"


Kelvin API documentation
------------------------

Please see the `Kelvin API documentation section Resource Schools`_ about allowed values for the attributes.


School class
------------

The :py:class:`ucsschool.kelvin.client.School` class has the following attributes and methods:

.. code-block:: python

    class School(KelvinObject):
        def __init__(
            self,
            name: str,
            *,
            display_name: str = None,
            administrative_servers: List[str] = None,
            class_share_file_server: str = None,
            dc_name: str = None,
            dc_name_administrative: str = None,
            educational_servers: List[str] = None,
            home_share_file_server: str = None,
            ucsschool_roles: List[str] = None,
            dn: str = None,
            url: str = None,
            session: Session = None,
        ):
            self.name = name
            self.display_name = display_name
            self.administrative_servers = administrative_servers
            self.class_share_file_server = class_share_file_server
            self.dc_name = dc_name
            self.dc_name_administrative = dc_name_administrative
            self.educational_servers = educational_servers
            self.home_share_file_server = home_share_file_server
            self.ucsschool_roles = ucsschool_roles
            self.dn = dn
            self.url = url
            self.session = session

        async def reload(self) -> School:
            ...

        async def save(self) -> School:
            raise NotImplementedError()

        async def delete(self) -> None:
            raise NotImplementedError()

        def as_dict(self) -> Dict[str, Any]:
            ...

Note: The Kelvin API does not yet support creating, changing or deleting school objects, and thus the Kelvin API client doesn't either.
Using ``School.save()`` or ``School.delete()`` will raise a :py:exc:`NotImplementedError` exception.


SchoolResource class
--------------------

The :py:class:`ucsschool.kelvin.client.SchoolResource` class has the following public attributes and methods:

.. code-block:: python

    class SchoolResource(KelvinResource):
        def __init__(self, session: Session):
            ...
        async def get(self, **kwargs) -> School:
            ...
        async def get_from_url(self, url: str) -> School:
            ...
        async def search(self, **kwargs) -> AsyncIterator[School]:
            ...



Creating school classes
-----------------------

The Kelvin API does not yet support creating school objects, and thus the Kelvin API client doesn't either.

To create a school (OU) object, either use the servers ``Schools`` UMC module or run the ``/usr/share/ucs-school-import/scripts/create_ou`` script from the servers command line.


Retrieving a school
-------------------

.. code-block:: python

    from ucsschool.kelvin.client import Session, SchoolResource

    async with Session(**credentials) as session:
        school = await SchoolResource(session=session).get(name="DEMOSCHOOL")

    school.as_dict()
    {'name': 'DEMOSCHOOL',
     'ucsschool_roles': ['school:school:DEMOSCHOOL'],
     'display_name': 'Demo School',
     'administrative_servers': [],
     'class_share_file_server': 'DEMOSCHOOL',
     'dc_name': None,
     'dc_name_administrative': None,
     'educational_servers': ['DEMOSCHOOL'],
     'home_share_file_server': 'DEMOSCHOOL',
     'dn': 'ou=DEMOSCHOOL,dc=example,dc=com',
     'url': 'https://master.ucs.local/ucsschool/kelvin/v1/schools/DEMOSCHOOL'}


Searching for schools
---------------------

The :py:meth:`search()` method allows searching for schools.
The optional ``name`` argument supports an inexact search using ``*`` as a placeholder.

.. code-block:: python

    from ucsschool.kelvin.client import Session, SchoolResource

    async with Session(**credentials) as session:
        async for school in SchoolResource(session=session).search(name="DEMO*"):
            print(school)

    School('name'='DEMOSCHOOL', dn='ou=DEMOSCHOOL,dc=example,dc=com')
    School('name'='DEMOSCHOOL2', dn='ou=DEMOSCHOOL2,dc=example,dc=com')


Changing a schools properties
-----------------------------

The Kelvin API does not yet support changing school objects, and thus the Kelvin API client doesn't either.

Moving
------

School objects do not support moving.

Deleting a school class
-----------------------

The Kelvin API does not yet support deleting school objects, and thus the Kelvin API client doesn't either.


.. _`Kelvin API documentation section Resource Schools`: https://docs.software-univention.de/ucsschool-kelvin-rest-api/resource-schools.html
