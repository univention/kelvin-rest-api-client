.. _auth:

Authentication and authorization
--------------------------------

All requests to the Kelvin API must be authenticated.
Requests to resource endpoints must carry a valid token.
The token will expire after an hour and must then be refreshed.
The ``Session`` class of the *Kelvin REST API Client* takes care of all that.
All it needs are the credentials of a user that is a members of the group ``ucsschool-kelvin-rest-api-admins`` on the host that is running the Kelvin API.

The user ``Administrator`` is automatically added to this group for testing purposes.
In production a regular admin user account or a dedicated service account should be used.

To use the *Kelvin REST API Client*, first get the UCS servers CA certificate (from ``http://FQDN.OF.UCS/ucs-root-ca.crt``).
Then use the ``Session`` context manager to open an authenticated HTTPS session for use by the *Kelvin REST API Client* resource classes.

.. code-block:: console

    $ wget --no-check-certificate -O /tmp/ucs-root-ca.crt https://master.ucs.local/ucs-root-ca.crt

We'll store the credentials and path to the UCS CA certificate for the following examples in a dictionary:

.. code-block:: python

    credentials = {
        "username": "Administrator",
        "password": "s3cr3t",
        "host": "master.ucs.local",
        "verify": "/tmp/ucs-root-ca.crt",
    }

For testing purposes the clients certificate check can be disabled by setting the value of ``verify`` to the boolean value ``False``.
