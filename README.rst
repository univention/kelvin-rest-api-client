=========================================
Python UCS\@school Kelvin REST API Client
=========================================

|python| |license| |code style| |bandit| |codecov| |docspassing| |travisci|

Python library to interact with the *UCS\@school Kelvin REST API*.

* Free software: GNU Affero General Public License version 3
* Documentation: https://kelvin-rest-api-client.readthedocs.io


Features
--------

* Asynchronous
* Automatic handling of HTTP(S) sessions
* Type annotations
* 90% test coverage (unittests + integration tests)
* Python 3.7, 3.8, 3.9


Usage
-----

The ``Session`` context manager opens and closes a HTTP session:

.. code-block:: python

    >>> import asyncio
    >>> from ucsschool.kelvin.client import Session, User, UserResource
    >>>
    >>> async def get_user(username: str) -> User:
    ...     async with Session(
    ...         "USERNAME",
    ...         "PASSWORD",
    ...         "master.ucs.local",
    ...         verify="ucs-root-ca.crt"
    ...     ) as session:
    ...         return await UserResource(session=session).get(name=username)
    ...
    >>> obj = asyncio.run(get_user("demo_student"))
    >>>
    >>> print(obj)
    User('name'='test_user', dn='uid=test_user,cn=schueler,cn=users,ou=DEMOSCHOOL,dc=example,dc=com')
    >>> print(obj.firstname, obj.lastname)
    Test User

There are more examples in the `docs`_ *usage* section.

For HTTPS to work, the SSL CA of the target system (UCS Master) must either be publicly signed, installed on the client system or available as file (as in the example above).
If the SSL CA certificate is not available ``verify=False``.
Obviously that is *not safe*! The CA of any UCS server can always be downloaded from ``http://FQDN.OF.UCS/ucs-root-ca.crt``.


Installation
------------

Install *UCS\@school Kelvin REST API Client* via pip from `PyPI`_::

    $ pip install kelvin-rest-api-client


Tests
-----

There are some isolated unittests, but most tests run against a real *UCS\@school Kelvin REST API*.
.. A UCS Docker container is used for this. The ``Makefile`` automates downloading and starting the Docker container (1 GB) and running the tests.

The tests expect the existence of two schools (``OUs``) on the target system (the Kelvin API does not support creation of schools yet).
The schools are ``DEMOSCHOOL`` and ``DEMOSCHOOL2``.
The first one usually already exists, but trying to create it again will is safe.
To create the schools run *on the system with the Kelvin API*::

    $ /usr/share/ucs-school-import/scripts/create_ou DEMOSCHOOL
    $ /usr/share/ucs-school-import/scripts/create_ou DEMOSCHOOL2

Run tests with current Python interpreter::

    $ make test

Using `tox`_ the tests can be executed with all supported Python versions::

    $ make test-all

To use an existing UCS server for the tests, copy the file ``tests/test_server_example.yaml`` to ``tests/test_server.yaml`` and adapt the settings before starting the tests::

    $ cp tests/test_server_example.yaml tests/test_server.yaml
    $ $EDITOR tests/test_server.yaml
    # check settings with a single test:
    $ python -m pytest tests/test_user.py::test_get
    # if OK, run all tests:
    $ make test


Logging
-------

Standard logging is used for tracking the libraries activity.
To capture the log messages for this project, subscribe to a logger named ``ucsschool.kelvin.client``.
*Attention:* Passwords and session tokens will be logged at log level ``DEBUG``!

The *UCS\@school Kelvin REST API* on the UCS server logs into the file ``/var/log/univention/ucsschool-kelvin-rest-api/http.log``.
The *UDM REST API* on the UCS server logs into the file ``/var/log/univention/directory-manager-rest.log``.

Repo permissions
----------------
* Github: @dansan and @JuergenBS
* Gitlab: @JuergenBS
* PyPI: @dansan and @SamuelYaron
* RTD: @dansan and @SamuelYaron

Credits
-------

.. _`tox`: http://tox.readthedocs.org/
.. _`docs`: https://kelvin-rest-api-client.readthedocs.io
.. _`PyPI`: https://pypi.org/project/kelvin-rest-api-client/
.. |license| image:: https://img.shields.io/badge/License-AGPL%20v3-orange.svg
    :alt: GNU AGPL V3 license
    :target: https://www.gnu.org/licenses/agpl-3.0
.. |python| image:: https://img.shields.io/badge/python-3.7+-blue.svg
    :alt: Python 3.7+
    :target: https://www.python.org/
.. |code style| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :alt: Code style: black
    :target: https://github.com/psf/black
.. |codecov| image:: https://codecov.io/gh/univention/kelvin-rest-api-client/branch/master/graph/badge.svg
    :alt: Code coverage
    :target: https://codecov.io/gh/univention/kelvin-rest-api-client
.. |docspassing| image:: https://readthedocs.org/projects/kelvin-rest-api-client/badge/?version=latest
    :alt: Documentation Status
    :target: https://kelvin-rest-api-client.readthedocs.io/en/latest/?badge=latest
.. |travisci| image:: https://travis-ci.com/univention/kelvin-rest-api-client.svg?branch=master
    :target: https://travis-ci.com/univention/kelvin-rest-api-client
.. |bandit| image:: https://img.shields.io/badge/security-bandit-yellow.svg
    :alt: Security: bandit
    :target: https://github.com/PyCQA/bandit
