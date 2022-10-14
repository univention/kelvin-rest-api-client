Language Header
===============

An ``Accept-Language`` header can be sent with each request.
The value can be set, when creating the ``Session`` object.
If not set, the ``Accept-Language`` Header will not be sent.

When an ``Accept-Language`` header is sent, the Kelvin REST API error messages are translated into the corresponding language.
(currently available languages: German and English)

To set the ``Accept-Language`` header, pass the ``language`` attribute to the ``Session`` constructor: ``Session(..., language="de-DE")``.
It is also possible to change the ``Accept-Language`` header within a ``Session`` context by passing the ``language`` attribute to the ``KelvinObject`` or the ``KelvinRessource`` constructor.

.. note::
    The Kelvin REST API server version must be greater than ``1.7.0`` to handle the ``Accept-Language`` header.

Set ``Accept-Language`` header within a ``Session`` context
-----------------------------------------------------------

Create user example:

.. code-block:: python

    from ucsschool.kelvin.client import Session, User

    async with Session(**credentials) as session:
        user = User(
            ...,
            session=session,
            language="de-DE"
        )
        await user.save()

Retrieve User example:

.. code-block:: python

    from ucsschool.kelvin.client import Session, UserResource

    async with Session(**credentials) as session:
        user = await UserResource(session=session, language="de-DE").get(name="test1")
