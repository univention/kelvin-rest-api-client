# -*- coding: utf-8 -*-


from packaging import version

from ucsschool.kelvin.client import __version__


def test_app_version():
    isinstance(version.parse(str(__version__)), version.Version)
