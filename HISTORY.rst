=======
History
=======

1.5.0 (2021-09-21)

* add attribute `udm_properties` for schools and schoolclasses which were added in ucsschool-kelvin-rest-api version 1.5.0

0.3.0 (2021-05-04)
------------------

* add support for the creation of school (OU) objects

0.2.2 (2020-11-09)
------------------

* add support for `kelvin_password_hashes` user attribute

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
* change 'as_dict' to be a method instead of a property
* fix flaky tests
* improve test coverage
* pass more env args to tox
* fix AttributeError with repr(role)
* add complete usage documentation

0.1.0 (2020-04-16)
------------------

* First release.
