Resource Users
==============

The ``Users`` resource is represented in the LDAP tree as user objects.

To list those LDAP objects run in  a terminal:

.. code-block:: console

    FILTER='(|(objectClass=ucsschoolStaff)(objectClass=ucsschoolStudent)(objectClass=ucsschoolTeacher))'
    univention-ldapsearch -LLL "$FILTER"

UCS\@school uses the UDM to access the LDAP directory.
UDM properties have different names than their associated LDAP attributes.
Their values may also differ.
To list the same UDM objects as above, run:

.. code-block:: console

    $ FILTER='(|(objectClass=ucsschoolStaff)(objectClass=ucsschoolStudent)(objectClass=ucsschoolTeacher))'
    $ udm users/user list --filter "$FILTER"

Kelvin API documentation
------------------------

Please see the `Kelvin API documentation section Resource Users`_ about allowed values for the attributes.

User class
----------

The :py:class:`ucsschool.kelvin.client.User` class has the following public attributes and methods:

.. code-block:: python

    class User(KelvinObject):
        def __init__(
            self,
            name: str,
            school: str,
            *,
            firstname: str = None,
            lastname: str = None,
            birthday: datetime.date = None,
            disabled: bool = False,
            email: str = None,
            expiration_date: datetime.date = None,
            kelvin_password_hashes: PasswordsHashes = None,
            password: str = None,
            record_uid: str = None,
            roles: List[str],
            schools: List[str],
            school_classes: Dict[str, List[str]] = None,
            source_uid: str = None,
            udm_properties: Dict[str, Any] = None,
            ucsschool_roles: List[str] = None,
            dn: str = None,
            url: str = None,
            session: Session = None,
        ):
        self.name = name
        self.school = school
        self.firstname = firstname
        self.lastname = lastname
        self.birthday = birthday
        self.disabled = disabled
        self.email = email
        self.expiration_date = expiration_date
        self.kelvin_password_hashes = kelvin_password_hashes
        self.password = password
        self.record_uid = record_uid
        self.roles = roles
        self.schools = schools
        self.school_classes = school_classes or {}
        self.source_uid = source_uid
        self.udm_properties = udm_properties or {}
        self.ucsschool_roles = ucsschool_roles
        self.dn = dn
        self.url = url
        self.session = session

        async def reload(self) -> User:
            ...
        async def save(self) -> User:
            ...
        async def delete(self) -> None:
            ...
        def as_dict(self) -> Dict[str, Any]:
            ...

.. note::
    The field ``expiration_date`` was added to the Kelvin REST API in version ``1.5.1``. The client works with prior server versions, but the attribute will not be read or set.

UserResource class
------------------

:py:class:`ucsschool.kelvin.client.UserResource` class has the following public attributes and methods:

.. code-block:: python

    class UserResource(KelvinResource):
        def __init__(self, session: Session):
            ...
        async def get(self, **kwargs) -> User:
            ...
        async def get_from_url(self, url: str) -> User:
            ...
        async def search(self, **kwargs) -> AsyncIterator[User]:
            ...


Create user
-----------

.. code-block:: python

    from ucsschool.kelvin.client import Session, User

    async with Session(**credentials) as session:
        user = User(
            school="DEMOSCHOOL",
            schools=["DEMOSCHOOL"],
            roles=["student"],
            name="test1",
            firstname="test",
            lastname="one",
            record_uid="test1",
            source_uid="TESTID",
            session=session
        )
        await user.save()

    user.dn
    'uid=test1,cn=schueler,cn=users,ou=DEMOSCHOOL,dc=example,dc=com'


Retrieve user
-------------

.. code-block:: python

    from ucsschool.kelvin.client import Session, UserResource

    async with Session(**credentials) as session:
        user = await UserResource(session=session).get(name="test1")

    user.as_dict()

    {'name': 'test1',
     'ucsschool_roles': ['student:school:DEMOSCHOOL'],
     'school': 'DEMOSCHOOL',
     'firstname': 'test',
     'lastname': 'one',
     'birthday': None,
     'disabled': False,
     'email': None,
     'expiration_date': None,
     'kelvin_password_hashes': None,
     'password': None,
     'record_uid': 'test1',
     'roles': ['student'],
     'schools': ['DEMOSCHOOL'],
     'school_classes': {},
     'source_uid': 'TESTID',
     'udm_properties': {},
     'dn': 'uid=test1,cn=schueler,cn=users,ou=DEMOSCHOOL,dc=example,dc=com',
     'url': 'https://master.ucs.local/ucsschool/kelvin/v1/users/test1'}


Search users
------------

The :py:meth:`search()` method allows searching for users, using a number of filters.
Most (but now all) attributes support searching inexact, using an asterisk (``*``) as placeholder.

In the following examples the search is always limited to users of the school ``DEMOSCHOOL``.
In the 1. search *all* users (of the school ``DEMOSCHOOL``) are searched,
2. users with a *username* starting with ``t``,
3. users with a *family name* starting with ``tea`` and
4. users that have the *role* ``teacher``.

.. code-block:: python

    from ucsschool.kelvin.client import Session, UserResource

    async with Session(**credentials) as session:
        async for user in UserResource(session=session).search(school="DEMOSCHOOL"):
            print(user)

    User('name'='demo_admin', dn='uid=demo_admin,cn=lehrer,cn=users,ou=DEMOSCHOOL,dc=example,dc=com')
    User('name'='demo_student', dn='uid=demo_student,cn=schueler,cn=users,ou=DEMOSCHOOL,dc=example,dc=com')
    User('name'='demo_teacher', dn='uid=demo_teacher,cn=lehrer,cn=users,ou=DEMOSCHOOL,dc=example,dc=com')
    User('name'='test1', dn='uid=test1,cn=schueler,cn=users,ou=DEMOSCHOOL,dc=example,dc=com')

        async for user in UserResource(session=session).search(
            name="t*", school="DEMOSCHOOL"
        ):
            print(user)

    User('name'='test1', dn='uid=test1,cn=schueler,cn=users,ou=DEMOSCHOOL,dc=example,dc=com')

        async for user in UserResource(session=session).search(
            lastname="tea*", school="DEMOSCHOOL"
        ):
            print(user)

    User('name'='demo_teacher', dn='uid=demo_teacher,cn=lehrer,cn=users,ou=DEMOSCHOOL,dc=example,dc=com')

        async for user in UserResource(session=session).search(
            roles=["teacher"], school="DEMOSCHOOL"
        ):
            print(user)

    User('name'='demo_admin', dn='uid=demo_admin,cn=lehrer,cn=users,ou=DEMOSCHOOL,dc=example,dc=com')
    User('name'='demo_teacher', dn='uid=demo_teacher,cn=lehrer,cn=users,ou=DEMOSCHOOL,dc=example,dc=com')


Change user properties
----------------------

Get the current user object, change some attributes and save the changes back to LDAP:

.. code-block:: python

    from ucsschool.kelvin.client import Session, User, UserResource

    async def change_properties(username: str, **changes) -> User:
        async with Session(**credentials) as session:
            user = await UserResource(session=session).get(name=username)
            for property, value in changes.items():
                setattr(user, property, value)
            return await user.save()

    user = await change_properties(
        "test1",
        firstname="newfn",
        lastname="newln",
        password="password123",
    )
    assert user.firstname == "newfn"
    assert user.lastname == "newln"


Hint: users cannot be modified, unless their ``record_uid`` and ``source_uid`` attributes are set (as is the case with the ``demo_*`` users).

Move user
---------

User objects support changing both ``school`` and ``name``.

When the ``school`` attribute of a user is changed, the new value *must* be part of the list in the ``schools`` attribute.

In the following example both ``school`` and ``name`` are changed.

.. code-block:: python

    from ucsschool.kelvin.client import Session, User, UserResource

    async with Session(**credentials) as session:
        user = User(
            school="DEMOSCHOOL", schools=["DEMOSCHOOL"],
            roles=["student"], name="test1", firstname="test",
            lastname="one", record_uid="test1",
            source_uid="TESTID", session=session
        )
        await user.save()
        user.dn
        'uid=test1,cn=schueler,cn=users,ou=DEMOSCHOOL,dc=example,dc=com'
        user.name = "test2"
        user.school = "DEMOSCHOOL2"
        user.schools = ["DEMOSCHOOL2"]
        await user.save()
        user.dn
        'uid=test2,cn=schueler,cn=users,ou=DEMOSCHOOL2,dc=example,dc=com'


Delete user
-----------

Get the current user object and delete it:

.. code-block:: python

    from ucsschool.kelvin.client import Session, User, UserResource

    async with Session(**credentials) as session:
        user = await UserResource(session=session).get(name="test1")
        await user.delete()

Trying to retrieve the deleted user will raise a :py:exc:`ucsschool.kelvin.client.NoObject` exception.


.. _`Kelvin API documentation section Resource Users`: https://docs.software-univention.de/ucsschool-kelvin-rest-api/resource-users.html
