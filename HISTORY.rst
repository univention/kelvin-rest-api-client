=======
History
=======

2.2.3 (2023-06-22)

* ``%xx`` escaped names of school classes, users and workgroups are now unescaped.

2.2.2 (2023-04-14)
------------------

* Support HEAD for ``SchoolClass``, ``User``, ``WorkGroup``, and ``Role``.

2.2.1 (2022-12-15)
------------------

* Use deepcopy in ``to_dict`` method to prevent values of ``udm_properties`` from being updated in objects which are copied.

2.2.0 (2022-10-13)
--------------------

* Support Http ``Accept-Language`` Header.

2.1.0 (2022-10-07)
--------------------

* Support HEAD for ``School``.

2.0.1 (2022-10-05)
--------------------

* Use detailed upstream error message in ``InvalidRequest`` exception messages.

2.0.0 (2022-09-10)
--------------------

* **API Change**: The required argument ``school`` in the ``User`` constructor has now the default argument ``None``. The argument ``name`` is not required anymore. Optional values, which are set to ``None``, are not passed to the Kelvin server anymore. This enables automatic value generation on the Kelvin REST API server. To make use of this, the attributes can be either set to ``None``, the empty string ``""`` or left out completely. Additionally, you have to create a schema for the corresponding attribute on the Kelvin REST API server.
* Send a correlation ID with each request.

1.7.1 (2022-08-30)
--------------------

* Loosen dependency constraints.

1.7.0 (2022-07-07)
--------------------

* Support user ``workgroups`` attribute.

1.6.1 (2022-06-30)
--------------------

* Ignore unknown attributes in KelvinObject child classes.

1.6.0 (2022-06-27)
--------------------

* Add support for workgroup resource.

1.5.2.1 (2022-04-05)
--------------------

* Fixed: Logger does replace values of credentials with placeholders.

1.5.2 (2022-02-22)
------------------

* Automatic tests now run with Python 3.7 - 3.10.
* Fixed: The timeout attribute from a session instance is now used for requests.

1.5.1 (2021-11-30)
------------------

* Add attribute ``expiration_date`` to the ``User`` class. The attribute was added to the Kelvin REST API app in version ``1.5.1``.

1.5.0 (2021-09-21)
------------------

* Add attribute ``udm_properties`` to classes ``School`` and ``SchoolClass``.  The attributes were added to the Kelvin REST API app in version ``1.5.0``.

0.3.0 (2021-05-04)
------------------

* Add support for the creation of school (OU) objects.

0.2.2 (2020-11-09)
------------------

* Add support for the ``kelvin_password_hashes`` attribute of the ``User`` class.

0.2.1 (2020-08-07)
------------------

* fix JWT token validity calculation: timestamp uses UTC
* documentation fixes
* dependency updates
* tests also run on Python 3.9-dev

0.2.0 (2020-04-17)
------------------

* move tox to test requirements
* fix user object creation with default parameters
* change ``as_dict`` to be a method instead of a property
* fix flaky tests
* improve test coverage
* pass more env args to tox
* fix AttributeError with repr(role)
* add complete usage documentation

0.1.0 (2020-04-16)
------------------

* First release.
