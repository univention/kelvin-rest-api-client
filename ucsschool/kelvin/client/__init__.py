# -*- coding: utf-8 -*-

from pathlib import Path

import lazy_object_proxy
import pkg_resources

from .base import KelvinObject, KelvinResource
from .exceptions import InvalidRequest, InvalidToken, KelvinClientError, NoObject, ServerError
from .role import Role, RoleResource
from .school import School, SchoolResource
from .school_class import SchoolClass, SchoolClassResource
from .session import Session
from .user import PasswordsHashes, User, UserResource
from .workgroup import WorkGroup, WorkGroupResource

__all__ = [
    "KelvinObject",
    "KelvinResource",
    "InvalidRequest",
    "InvalidToken",
    "KelvinClientError",
    "NoObject",
    "PasswordsHashes",
    "ServerError",
    "School",
    "SchoolResource",
    "SchoolClass",
    "SchoolClassResource",
    "Session",
    "Role",
    "RoleResource",
    "User",
    "UserResource",
    "WorkGroup",
    "WorkGroupResource",
]


def _app_version() -> str:
    try:
        return pkg_resources.get_distribution("kelvin-rest-api-client").version
    except pkg_resources.DistributionNotFound:  # pragma: no cover
        # not yet installed (running tests prior to installation)
        with (Path(__file__).parent.parent.parent.parent / "VERSION.txt").open("r") as fp:
            return fp.read().strip()


__author__ = """Daniel Troeder"""
__email__ = "troeder@univention.de"
__version__: str = lazy_object_proxy.Proxy(_app_version)
