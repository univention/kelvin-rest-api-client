=========================================
Python UCS\@school Kelvin REST API Client
=========================================

|python| |license| |code style| |bandit| |codecov| |docspassing| |travisci| |gh Code Linting| |gh Integration tests|

Python library to interact with the `UCS\@school Kelvin REST API`_.

* Free software: GNU Affero General Public License version 3
* Documentation: https://kelvin-rest-api-client.readthedocs.io


Features
--------

* Asynchronous
* Automatic handling of HTTP(S) sessions
* Type annotations
* 97% test coverage (unittests + integration tests)
* Python 3.7, 3.8, 3.9, 3.10


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

Install *UCS\@school Kelvin REST API Client* via pip from `PyPI`_:

.. code-block:: console

    $ pip install kelvin-rest-api-client


Tests
-----

There are some isolated unittests, but most tests run against a real *UCS\@school Kelvin REST API*.
A UCS Docker container has been prepared for this (additionally to the Kelvin API Docker container).
The ``Makefile`` automates downloading and starting the Docker containers (3.2 GB GB) and running the tests.
It is also possible to use an existing UCS DC Master with UCS\@school and the Kelvin API installed.

The tests expect the existence of two schools (``OUs``) on the target system (the Kelvin API does not support creation of schools yet).
The schools are ``DEMOSCHOOL`` and ``DEMOSCHOOL2``.
The first one usually already exists, but trying to create it again is safe.
To create the schools run *on the UCS DC Master*:

.. code-block:: console

    $ /usr/share/ucs-school-import/scripts/create_ou DEMOSCHOOL
    $ /usr/share/ucs-school-import/scripts/create_ou DEMOSCHOOL2

Furthermore an email domain must exist:

.. code-block:: console

    $ udm mail/domain create \
        --ignore_exists \
        --position "cn=domain,cn=mail,$(ucr get ldap/base)" \
        --set name="$(ucr get domainname)"

Since version ``1.5.0`` the Kelvin REST API supports UDM properties in all resources. A configuration is required for the tests for this feature:

.. code-block:: console

    $ cat > /etc/ucsschool/kelvin/mapped_udm_properties.json <<__EOF__
    {
        "user": ["title"],
        "school_class": ["mailAddress"],
        "school": ["description"]
    }
    __EOF__

The provided UCS Docker containers already contain both OUs.
They can be started using the Makefile:

.. code-block:: console

    $ make start-docker-containers

    Downloading Docker image '..-ucsschool-udm-rest-api-only:stable-4.4-8'...
    Downloading Docker image '../ucsschool-kelvin-rest-api:1.4.3'...
    Starting UCS docker container...
    Waiting for UCS docker container to start...
    Waiting for IP address of UCS container...
    Waiting for UDM REST API...........
    Creating Kelvin REST API container...
    Configuring Kelvin REST API container...
    Rebuilding the OpenAPI client library in the Kelvin API Container...
    Starting Kelvin REST API server...
    Waiting for Kelvin docker container to start...
    Waiting for IP address of Kelvin container...
    Waiting for Kelvin API...
    Fixing log file permissions...
    Setting up reverse proxy...
    ==> UDM REST API log file: /tmp/udm-rest-api-log/directory-manager-rest.log
    ==> UDM REST API: http://172.17.0.2/univention/udm/
    ==> Kelvin API configs: /tmp/kelvin-api/configs/
    ==> Kelvin API hooks: /tmp/kelvin-api/kelvin-hooks/
    ==> Kelvin API log file: /tmp/kelvin-api/log/http.log
    ==> Kelvin API: http://172.17.0.3:8911/ucsschool/kelvin/v1/docs
    ==> Kelvin API: https://172.17.0.2/ucsschool/kelvin/v1/docs

The Docker containers can be stopped and removed by running:

.. code-block:: console

    $ make stop-and-remove-docker-containers

The Docker images will not be removed, only the running containers.

Run tests with current Python interpreter:

.. code-block:: console

    $ make test

Using `tox`_ the tests can be executed with all supported Python versions:

.. code-block:: console

    $ make test-all

To use an existing UCS server for the tests, copy the file ``tests/test_server_example.yaml`` to ``tests/test_server.yaml`` and adapt the settings before starting the tests:

.. code-block:: console

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

.. _`UCS\@school Kelvin REST API`: https://docs.software-univention.de/ucsschool-kelvin-rest-api/
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
    :target: https://app.travis-ci.com/github/univention/kelvin-rest-api-client
.. |bandit| image:: https://img.shields.io/badge/security-bandit-yellow.svg
    :alt: Security: bandit
    :target: https://github.com/PyCQA/bandit
.. |gh Code Linting| image:: https://github.com/univention/kelvin-rest-api-client/workflows/Code%20Linting/badge.svg
    :target: https://github.com/univention/kelvin-rest-api-client/actions?query=workflow%3A%22Code+Linting%22
.. |gh Integration tests| image:: https://github.com/univention/kelvin-rest-api-client/workflows/Integration%20tests/badge.svg
    :target: https://github.com/univention/kelvin-rest-api-client/actions?query=workflow%3A%22Integration+tests%22
