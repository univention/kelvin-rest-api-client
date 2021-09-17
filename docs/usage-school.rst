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
            educational_servers: List[str] = None,
            administrative_servers: List[str] = None,
            class_share_file_server: str = None,
            home_share_file_server: str = None,
            udm_properties: Dict[str, Any] = None,
            ucsschool_roles: List[str] = None,
            dn: str = None,
            url: str = None,
            session: Session = None,
        ):
            self.name = name
            self.display_name = display_name
            self.educational_servers = educational_servers
            self.administrative_servers = administrative_servers
            self.class_share_file_server = class_share_file_server
            self.home_share_file_server = home_share_file_server
            self.udm_properties = udm_properties or {}
            self.ucsschool_roles = ucsschool_roles
            self.dn = dn
            self.url = url
            self.session = session

        async def reload(self) -> School:
            ...

        async def save(self) -> School:
            ...

        async def delete(self) -> None:
            raise NotImplementedError()

        def as_dict(self) -> Dict[str, Any]:
            ...

Note: The Kelvin API does not yet support changing or deleting school objects, and thus the Kelvin API client doesn't either.
Using ``School.save()`` or ``School.delete()`` on existing school objects will raise a :py:exc:`NotImplementedError` exception.


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



Create school
-------------

Since version ``1.4.0`` the Kelvin REST API supports the creation of school (OU) objects.
The result should be the same as using the ``Schools`` UMC module or running the ``/usr/share/ucs-school-import/scripts/create_ou`` script from the command line.
The *Kelvin REST API Client* supports this feature since version ``0.3.0``.

The only required attribute is ``name``. An educational domain controller for each school is required however.
If none is passed in the request, one will be created automatically as ``dc<name>``.
If ``name`` is longer than 11 characters this will fail.
In that case the hostname must be passed in ``educational_servers``.

For historical reasons ``administrative_servers`` and ``educational_servers`` are lists that must contain exactly one item.


.. code-block:: python

    from ucsschool.kelvin.client import Session, School

    async with Session(**credentials) as session:
        school = School(
            name="testou",
            display_name="A test school",
            session=session,
        )
        await school.save()

    school.as_dict()
    {'name': 'testou',
     'ucsschool_roles': ['school:school:testou'],
     'display_name': 'A test school',
     'educational_servers': ['dctestou'],
     'administrative_servers': [],
     'class_share_file_server': 'dctestou',
     'home_share_file_server': 'dctestou',
     'udm_properties': {},
     'dn': 'ou=testou,dc=example,dc=com',
     'url': 'https://master.ucs.local/ucsschool/kelvin/v1/schools/testou'}


Schools are saved as containers in the UCS LDAP.
The result can be verified on the target system using UDM:

.. code-block:: console

    $ udm container/ou list --filter ou=testou

    DN: ou=testou,dc=example,dc=com
      name: testou
      displayName: A test school
      ucsschoolRole: school:school:testou
      ucsschoolClassShareFileServer: cn=dctestou,cn=dc,cn=server,cn=computers,ou=testou,dc=example,dc=com
      ucsschoolHomeShareFileServer: cn=dctestou,cn=dc,cn=server,cn=computers,ou=testou,dc=example,dc=com
      ...

The administrative and educational server information is stored as group membership.
If interested, search using the hostname prefixed with a dollar (``dctestou$``):

.. code-block:: console

    $ udm groups/group list --filter 'memberUid=dctestou$'


Retrieve school
---------------

.. code-block:: python

    from ucsschool.kelvin.client import Session, SchoolResource

    async with Session(**credentials) as session:
        school = await SchoolResource(session=session).get(name="DEMOSCHOOL")

    school.as_dict()
    {'name': 'DEMOSCHOOL',
     'ucsschool_roles': ['school:school:DEMOSCHOOL'],
     'display_name': 'Demo School',
     'educational_servers': ['DEMOSCHOOL'],
     'administrative_servers': [],
     'class_share_file_server': 'DEMOSCHOOL',
     'home_share_file_server': 'DEMOSCHOOL',
     'dn': 'ou=DEMOSCHOOL,dc=example,dc=com',
     'url': 'https://master.ucs.local/ucsschool/kelvin/v1/schools/DEMOSCHOOL'}


Search schools
--------------

The :py:meth:`search()` method allows searching for schools.
The optional ``name`` argument supports an inexact search using ``*`` as a placeholder.

.. code-block:: python

    from ucsschool.kelvin.client import Session, SchoolResource

    async with Session(**credentials) as session:
        async for school in SchoolResource(session=session).search(name="DEMO*"):
            print(school)

    School('name'='DEMOSCHOOL', dn='ou=DEMOSCHOOL,dc=example,dc=com')
    School('name'='DEMOSCHOOL2', dn='ou=DEMOSCHOOL2,dc=example,dc=com')


Change school properties
------------------------

The Kelvin API does not yet support changing school objects, and thus the Kelvin API client doesn't either.

Move school
-----------

School objects do not support moving.

Delete school
-------------

The Kelvin API does not yet support deleting school objects, and thus the Kelvin API client doesn't either.


.. _`Kelvin API documentation section Resource Schools`: https://docs.software-univention.de/ucsschool-kelvin-rest-api/resource-schools.html
