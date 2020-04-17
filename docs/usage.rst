=====
Usage
=====

The Kelvin APIs resources (users, school classes etc) support a varying range of operations: retrieve, search, create, modify, move and delete.
Some resources support all operations, others only a subset.
See each resources usage section about which operations are supported.

All requests to the Kelvin API must be authenticated.
The ``Session`` class takes care of that.
Section :ref:`Authentication and authorization <auth>` describes its usage.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   usage-auth
   usage-role
   usage-school
   usage-school-class
   usage-users



Note on moving of objects
-------------------------

Moving an object means changing its position in LDAP.
That happens whenever the DN changes.
The DN is created from the name of the object concatenated with the subtree in which the object is located.
So both changing a users or groups ``name`` attribute as well as changing an objects ``school`` attribute initiates a move.

School class objects do not support changing the school.

When the ``school`` attribute of a user is changed, the new value *must* be part of the list in the ``schools`` attribute.
