Resource WorkGroup
====================

The ``WorkGroup`` resource is represented in the LDAP tree as group objects.

To list those LDAP objects run in  a terminal:

.. code-block:: console

    FILTER='(&(objectClass=ucsschoolGroup)(ucsschoolRole=workgroup:*))'
    univention-ldapsearch -LLL "$FILTER"

UCS\@school uses the UDM to access the LDAP directory.
UDM properties have different names than their associated LDAP attributes.
Their values may also differ.
To list the same UDM objects as above, run:

.. code-block:: console

    $ FILTER='(&(objectClass=ucsschoolGroup)(ucsschoolRole=workgroup:*))'
    $ udm groups/group list --filter "$FILTER"


WorkGroup class
-----------------

The :py:class:`ucsschool.kelvin.client.WorkGroup` class has the following public attributes and methods:

.. code-block:: python

    class WorkGroup(KelvinObject):
        def __init__(
            self,
            name: str,
            school: str,
            *,
            description: str = None,
            users: List[str] = None,
            email: str = None,
            allowed_email_senders_users: List[str] = None,
            allowed_email_senders_groups: List[str] = None,
            create_share: bool = True,
            udm_properties: Dict[str, Any] = None,
            ucsschool_roles: List[str] = None,
            dn: str = None,
            url: str = None,
            session: Session = None,
        ):
            self.name = name
            self.school = school
            self.description = description
            self.users = users
            self.email = email
            self.allowed_email_senders_users = allowed_email_senders_users
            self.allowed_email_senders_groups = allowed_email_senders_groups
            self.create_share = create_share
            self.udm_properties = udm_properties or {}
            self.ucsschool_roles = ucsschool_roles
            self.dn = dn
            self.url = url
            self.session = session


        async def reload(self) -> WorkGroup:
            ...
        async def save(self) -> WorkGroup:
            ...
        async def delete(self) -> None:
            ...
        def as_dict(self) -> Dict[str, Any]:
            ...

WorkGroupResource class
-------------------------

The :py:class:`ucsschool.kelvin.client.WorkGroupResource` class has the following public attributes and methods:

.. code-block:: python

    class WorkGroupResource(KelvinResource):
        def __init__(self, session: Session):
            ...
        async def get(self, **kwargs) -> WorkGroup:
            ...
        async def get_from_url(self, url: str) -> WorkGroup:
            ...
        async def search(self, **kwargs) -> AsyncIterator[WorkGroup]:
            ...



Create workgroup
-------------------

Workgroups can be created explicitly or implicitly when creating or modifying users.

workgroups will be automatically created when mentioned in a users ``workgroups`` attribute.
They will however not be deleted automatically if they are removed from all users and are thus empty.

.. code-block:: python

    from ucsschool.kelvin.client import Session, WorkGroup

    async with Session(**credentials) as session:
        wg = WorkGroup(
            name="testworkgroup",
            school="DEMOSCHOOL",
            description="A test workgroup",
            users=["demo_student", "demo_teacher"],
            create_share=True,
            session=session,
        )
        await wg.save()

    wg.as_dict()
    {'name': 'testworkgroup',
     'ucsschool_roles': ['workgroup:school:DEMOSCHOOL'],
     'school': 'DEMOSCHOOL',
     'description': 'A test workgroup',
     'users': ['demo_student', 'demo_teacher'],
     'create_share': True,
     'udm_properties': {},
     'dn': 'cn=DEMOSCHOOL-testworkgroup,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com',
     'url': 'https://master.ucs.local/ucsschool/kelvin/v1/workgroups/DEMOSCHOOL/testworkgroup'}


Workgroups are saved as groups in the UCS LDAP.
The result can be verified on the target system using UDM:

.. code-block:: console

    $ udm groups/group list --filter cn=DEMOSCHOOL-testworkgroup

    DN: cn=DEMOSCHOOL-testworkgroup,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com
      name: DEMOSCHOOL-testworkgroup
      description: A test workgroup
      ucsschoolRole: workgroup:school:DEMOSCHOOL
      users: uid=demo_student,cn=schueler,cn=users,ou=DEMOSCHOOL,dc=example,dc=com
      users: uid=demo_teacher,cn=lehrer,cn=users,ou=DEMOSCHOOL,dc=example,dc=com
      ...

Every workgroup has a share with the same name:

.. code-block:: console

    $  udm shares/share list --filter cn=DEMOSCHOOL-testworkgroup

    DN: cn=DEMOSCHOOL-testworkgroup,cn=shares,ou=DEMOSCHOOL,dc=example,dc=com
      name: DEMOSCHOOL-testworkgroup
      host: DEMOSCHOOL.example.com
      path: /home/DEMOSCHOOL/groups/klassen/DEMOSCHOOL-testworkgroup
      directorymode: 0770
      group: 7110
      ...

Example creating two workgroups as a byproduct of creating a user:

.. code-block:: python

    from ucsschool.kelvin.client import Session, WorkGroupResource, User

    async with Session(**credentials) as session:
        user = User(
            school="DEMOSCHOOL", schools=["DEMOSCHOOL"],
            roles=["student"], name="test2",
            firstname="test", lastname="two",
            record_uid="test2", source_uid="TESTID",
            workgroups={"DEMOSCHOOL": ["workgroup1", "workgroup2"]},
            session=session)
        await user.save()

        async for wg in WorkGroupResource(session=session).search(school="DEMOSCHOOL"):
            print(sc)

    WorkGroup('name'='workgroup1', 'school'='DEMOSCHOOL', dn='cn=DEMOSCHOOL-workgroup1,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com')
    WorkGroup('name'='workgroup2', 'school'='DEMOSCHOOL', dn='cn=DEMOSCHOOL-workgroup2,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com')
    WorkGroup('name'='Demoworkgroup', 'school'='DEMOSCHOOL', dn='cn=DEMOSCHOOL-Demoworkgroup,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com')


Retrieve workgroup
---------------------

It is necessary to pass both ``name`` and ``school`` arguments to the :py:meth:`get()` method, as the name alone wouldn't be unique in a domain (there can be workgroups of the same name in multiple schools).

.. code-block:: python

    from ucsschool.kelvin.client import Session, WorkGroupResource

    async with Session(**credentials) as session:
        wg = await WorkGroupResource(session=session).get(
            school="DEMOSCHOOL", name="testworkgroup"
        )

    wg.as_dict()
    {'name': 'testworkgroup',
     'ucsschool_roles': ['workgroup:school:DEMOSCHOOL'],
     'school': 'DEMOSCHOOL',
     'description': 'A test workgroup',
     'users': ['demo_student', 'demo_teacher'],
     'create_share': True,
     'dn': 'cn=DEMOSCHOOL-testworkgroup,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com',
     'url': 'https://10.200.3.70/ucsschool/kelvin/v1/workgroups/DEMOSCHOOL/testworkgroup'}


Search workgroups
---------------------

The :py:meth:`search()` method allows searching for workgroups, filtering by ``school`` (mandatory) and ``name`` (optional).

The mandatory ``school`` argument must be exact while the optional ``name`` argument support an inexact search using ``*`` as a placeholder.

.. code-block:: python

    from ucsschool.kelvin.client import Session, WorkGroupResource

    async with Session(**credentials) as session:
        async for wg in WorkGroupResource(session=session).search(school="DEMOSCHOOL"):
            print(sc)

    WorkGroup('name'='Demoworkgroup', 'school'='DEMOSCHOOL', dn='cn=DEMOSCHOOL-Demoworkgroup,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com')
    WorkGroup('name'='testworkgroup', 'school'='DEMOSCHOOL', dn='cn=DEMOSCHOOL-testworkgroup,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com')

        async for wg in WorkGroupResource(session=session).search(
            school="DEMOSCHOOL", name="test*"
        ):
            print(sc)

    WorkGroup('name'='testworkgroup', 'school'='DEMOSCHOOL', dn='cn=DEMOSCHOOL-testworkgroup,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com')


Change workgroup properties
------------------------------

Get the current workgroup object, change some attributes and save the changes back to LDAP:

.. code-block:: python

    from ucsschool.kelvin.client import Session, WorkGroupResource

    async with Session(**credentials) as session:
        wg = await WorkGroupResource(session=session).get(
            school="DEMOSCHOOL",
            name="testworkgroup"
        )
        wg.description = "new description"
        wg.users.remove("demo_teacher")
        await wg.save()

    wg.as_dict()
    {'name': 'testworkgroup',
     'ucsschool_roles': ['workgroup:school:DEMOSCHOOL'],
     'school': 'DEMOSCHOOL',
     'description': 'new description',
     'users': ['demo_student'],
     'create_share': True,
     'dn': 'cn=DEMOSCHOOL-testworkgroup,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com',
     'url': 'https://10.200.3.70/ucsschool/kelvin/v1/workgroups/DEMOSCHOOL/testworkgroup'}


Move workgroup
-----------------

Workgroup objects do not support changing the ``school``.
Changing the ``name`` is allowed however.

.. code-block:: python

    from ucsschool.kelvin.client import Session, WorkGroupResource

    async with Session(**credentials) as session:
        wg = await WorkGroupResource(session=session).get(
            school="DEMOSCHOOL",
            name="testworkgroup"
        )
        wg.name = "testworkgroup-new"
        await wg.save()

    wg.dn
    'cn=DEMOSCHOOL-testworkgroup-new,cn,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com'


Delete workgroup
-------------------

Get the current workgroup object and delete it:

.. code-block:: python

    from ucsschool.kelvin.client import Session, WorkGroupResource

    async with Session(**credentials) as session:
        wg = await WorkGroupResource(session=session).get(
            school="DEMOSCHOOL",
            name="testworkgroup"
        )
        await wg.delete()
