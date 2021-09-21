Resource SchoolClass
====================

The ``SchoolClass`` resource is represented in the LDAP tree as group objects.

To list those LDAP objects run in  a terminal:

.. code-block:: console

    FILTER='(&(objectClass=ucsschoolGroup)(ucsschoolRole=school_class:*))'
    univention-ldapsearch -LLL "$FILTER"

UCS\@school uses the UDM to access the LDAP directory.
UDM properties have different names than their associated LDAP attributes.
Their values may also differ.
To list the same UDM objects as above, run:

.. code-block:: console

    $ FILTER='(&(objectClass=ucsschoolGroup)(ucsschoolRole=school_class:*))'
    $ udm groups/group list --filter "$FILTER"


SchoolClass class
-----------------

The :py:class:`ucsschool.kelvin.client.SchoolClass` class has the following attributes and methods:

.. code-block:: python

    class SchoolClass(KelvinObject):
        def __init__(
            self,
            name: str,
            school: str,
            *,
            description: str = None,
            users: List[str] = None,
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
            self.udm_properties = udm_properties or {}
            self.ucsschool_roles = ucsschool_roles
            self.dn = dn
            self.url = url
            self.session = session


        async def reload(self) -> SchoolClass:
            ...
        async def save(self) -> SchoolClass:
            ...
        async def delete(self) -> None:
            ...
        def as_dict(self) -> Dict[str, Any]:
            ...

SchoolClassResource class
-------------------------

The :py:class:`ucsschool.kelvin.client.SchoolClassResource` class has the following public attributes and methods:

.. code-block:: python

    class SchoolClassResource(KelvinResource):
        def __init__(self, session: Session):
            ...
        async def get(self, **kwargs) -> SchoolClass:
            ...
        async def get_from_url(self, url: str) -> SchoolClass:
            ...
        async def search(self, **kwargs) -> AsyncIterator[SchoolClass]:
            ...



Create school class
-------------------

School classes can be created explicitly or implicitly when creating or modifying users.

School classes will be automatically created when mentioned in a users ``school_classes`` attribute.
They will however not be deleted automatically if they are removed from all users and are thus empty.

.. code-block:: python

    from ucsschool.kelvin.client import Session, SchoolClass

    async with Session(**credentials) as session:
        sc = SchoolClass(
            name="testclass",
            school="DEMOSCHOOL",
            description="A test class",
            users=["demo_student", "demo_teacher"],
            session=session,
        )
        await sc.save()

    sc.as_dict()
    {'name': 'testclass',
     'ucsschool_roles': ['school_class:school:DEMOSCHOOL'],
     'school': 'DEMOSCHOOL',
     'description': 'A test class',
     'users': ['demo_student', 'demo_teacher'],
     'udm_properties': {},
     'dn': 'cn=DEMOSCHOOL-testclass,cn=klassen,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com',
     'url': 'https://master.ucs.local/ucsschool/kelvin/v1/classes/DEMOSCHOOL/testclass'}


School classes are saved as groups in the UCS LDAP.
The result can be verified on the target system using UDM:

.. code-block:: console

    $ udm groups/group list --filter cn=DEMOSCHOOL-testclass

    DN: cn=DEMOSCHOOL-testclass,cn=klassen,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com
      name: DEMOSCHOOL-testclass
      description: A test class
      ucsschoolRole: school_class:school:DEMOSCHOOL
      users: uid=demo_student,cn=schueler,cn=users,ou=DEMOSCHOOL,dc=example,dc=com
      users: uid=demo_teacher,cn=lehrer,cn=users,ou=DEMOSCHOOL,dc=example,dc=com
      ...

Every school class has a share with the same name:

.. code-block:: console

    $  udm shares/share list --filter cn=DEMOSCHOOL-testclass

    DN: cn=DEMOSCHOOL-testclass,cn=klassen,cn=shares,ou=DEMOSCHOOL,dc=example,dc=com
      name: DEMOSCHOOL-testclass
      host: DEMOSCHOOL.example.com
      path: /home/DEMOSCHOOL/groups/klassen/DEMOSCHOOL-testclass
      directorymode: 0770
      group: 7110
      ...

Example creating two school classes as a byproduct of creating a user:

.. code-block:: python

    from ucsschool.kelvin.client import Session, SchoolClassResource, User

    async with Session(**credentials) as session:
        user = User(
            school="DEMOSCHOOL", schools=["DEMOSCHOOL"],
            roles=["student"], name="test2",
            firstname="test", lastname="two",
            record_uid="test2", source_uid="TESTID",
            school_classes={"DEMOSCHOOL": ["class1", "class2"]},
            session=session)
        await user.save()

        async for sc in SchoolClassResource(session=session).search(school="DEMOSCHOOL"):
            print(sc)

    SchoolClass('name'='class1', 'school'='DEMOSCHOOL', dn='cn=DEMOSCHOOL-class1,cn=klassen,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com')
    SchoolClass('name'='class2', 'school'='DEMOSCHOOL', dn='cn=DEMOSCHOOL-class2,cn=klassen,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com')
    SchoolClass('name'='Democlass', 'school'='DEMOSCHOOL', dn='cn=DEMOSCHOOL-Democlass,cn=klassen,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com')


Retrieve school class
---------------------

It is necessary to pass both ``name`` and ``school`` arguments to the :py:meth:`get()` method, as the name alone wouldn't be unique in a domain (there can be classes of the same name in multiple schools).

.. code-block:: python

    from ucsschool.kelvin.client import Session, SchoolClassResource

    async with Session(**credentials) as session:
        sc = await SchoolClassResource(session=session).get(
            school="DEMOSCHOOL", name="testclass"
        )

    sc.as_dict()
    {'name': 'testclass',
     'ucsschool_roles': ['school_class:school:DEMOSCHOOL'],
     'school': 'DEMOSCHOOL',
     'description': 'A test class',
     'users': ['demo_student', 'demo_teacher'],
     'dn': 'cn=DEMOSCHOOL-testclass,cn=klassen,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com',
     'url': 'https://10.200.3.70/ucsschool/kelvin/v1/classes/DEMOSCHOOL/testclass'}


Search school classes
---------------------

The :py:meth:`search()` method allows searching for school classes, filtering by ``school`` (mandatory) and ``name`` (optional).

The mandatory ``school`` argument must be exact while the optional ``name`` argument support an inexact search using ``*`` as a placeholder.

.. code-block:: python

    from ucsschool.kelvin.client import Session, SchoolClassResource

    async with Session(**credentials) as session:
        async for sc in SchoolClassResource(session=session).search(school="DEMOSCHOOL"):
            print(sc)

    SchoolClass('name'='Democlass', 'school'='DEMOSCHOOL', dn='cn=DEMOSCHOOL-Democlass,cn=klassen,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com')
    SchoolClass('name'='testclass', 'school'='DEMOSCHOOL', dn='cn=DEMOSCHOOL-testclass,cn=klassen,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com')

        async for sc in SchoolClassResource(session=session).search(
            school="DEMOSCHOOL", name="test*"
        ):
            print(sc)

    SchoolClass('name'='testclass', 'school'='DEMOSCHOOL', dn='cn=DEMOSCHOOL-testclass,cn=klassen,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com')


Change school class properties
------------------------------

Get the current school class object, change some attributes and save the changes back to LDAP:

.. code-block:: python

    from ucsschool.kelvin.client import Session, SchoolClassResource

    async with Session(**credentials) as session:
        sc = await SchoolClassResource(session=session).get(
            school="DEMOSCHOOL",
            name="testclass"
        )
        sc.description = "new description"
        sc.users.remove("demo_teacher")
        await sc.save()

    sc.as_dict()
    {'name': 'testclass',
     'ucsschool_roles': ['school_class:school:DEMOSCHOOL'],
     'school': 'DEMOSCHOOL',
     'description': 'new description',
     'users': ['demo_student'],
     'dn': 'cn=DEMOSCHOOL-testclass,cn=klassen,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com',
     'url': 'https://10.200.3.70/ucsschool/kelvin/v1/classes/DEMOSCHOOL/testclass'}


Move school class
-----------------

School class objects do not support changing the ``school``.
Changing the ``name`` is allowed however.

.. code-block:: python

    from ucsschool.kelvin.client import Session, SchoolClassResource

    async with Session(**credentials) as session:
        sc = await SchoolClassResource(session=session).get(
                school="DEMOSCHOOL",
                name="testclass"
            )
        sc.name = "testclass-new"
        await sc.save()

    sc.dn
    'cn=DEMOSCHOOL-testclass-new,cn,cn=klassen,cn=schueler,cn=groups,ou=DEMOSCHOOL,dc=example,dc=com'


Delete school class
-------------------

Get the current school class object and delete it:

.. code-block:: python

    from ucsschool.kelvin.client import Session, SchoolClassResource

    async with Session(**credentials) as session:
        sc = await SchoolClassResource(session=session).get(
                school="DEMOSCHOOL",
                name="testclass"
            )
        await sc.delete()
