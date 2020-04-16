=====
Usage
=====

To use the *Kelvin REST API Client* in a project, first get the UCS servers CA certificate (from ``http://FQDN.OF.UCS/ucs-root-ca.crt``).
Then use the ``Session`` context manager to open a HTTPS session and authenticate.

Change some properties
----------------------

Open the session, get the current LDAP object, change some attributes and save the changes back to LDAP:

.. code-block:: python

    >>> import asyncio
    >>> from ucsschool.kelvin.client import Session, User, UserResource
    >>>
    >>> async def change_properties(username: str, **changes) -> User:
    ...     async with Session(
    ...         "USERNAME",
    ...         "PASSWORD",
    ...         "master.ucs.local",
    ...         verify="ucs-root-ca.crt"
    ...     ) as session:
    ...         user = await UserResource(session=session).get(name=username)
    ...         for property, value in changes.items():
    ...             setattr(user, property, value)
    ...         return await user.save()
    ...
    >>> async def main() -> User:
    ...     return await change_properties(
    ...         "test_user",
    ...         firstname="newfn",
    ...         lastname="newln",
    ...         password="password123",
    ...     )
    ...
    >>> obj = asyncio.run(main())
    >>> assert obj.firstname == "newfn"
    >>> assert obj.lastname == "newln"


Move an object
--------------

Moving an object means changing its position in LDAP.
That happens whenever the DN changes.
The DN is created from the name of the object concatenated with the subtree in which the object is located.
So both changing a users or groups ``name`` attribute as well as changing an objects ``school`` attribute initiates a move.

School class objects do not support changing the school.

When the ``school`` attribute of a user is changed, the new value *must* be part of the list in the ``schools`` attribute.
