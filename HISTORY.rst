=======
History
=======

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
