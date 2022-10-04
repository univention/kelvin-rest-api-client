# -*- coding: utf-8 -*-
#
# Copyright 2020 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

import base64
import datetime
import logging
import warnings
from typing import Any, Dict, Iterable, List, Type, get_type_hints

from .base import KelvinObject, KelvinResource
from .exceptions import InvalidRequest
from .session import Session

logger = logging.getLogger(__name__)


class PasswordsHashes:
    user_password: List[str]
    samba_nt_password: str
    krb_5_key: List[str]
    krb5_key_version_number: int
    samba_pwd_last_set: int

    def __init__(
        self,
        user_password: List[str],
        samba_nt_password: str,
        krb_5_key: List[str],
        krb5_key_version_number: int,
        samba_pwd_last_set: int,
    ):
        self.user_password = user_password
        self.samba_nt_password = samba_nt_password
        self.krb_5_key = krb_5_key
        self.krb5_key_version_number = krb5_key_version_number
        self.samba_pwd_last_set = samba_pwd_last_set

    def as_dict(self) -> Dict[str, Any]:
        return dict((attr, getattr(self, attr)) for attr in get_type_hints(self).keys())

    def as_dict_with_ldap_attr_names(self) -> Dict[str, Any]:
        """
        Wrapper around `as_dict()` that renames the keys to those used in a UCS'
        OpenLDAP.
        """
        res = self.as_dict()
        res["userPassword"] = res.pop("user_password")
        res["sambaNTPassword"] = res.pop("samba_nt_password")
        res["krb5Key"] = res.pop("krb_5_key")
        res["krb5KeyVersionNumber"] = res.pop("krb5_key_version_number")
        res["sambaPwdLastSet"] = res.pop("samba_pwd_last_set")
        return res

    @property
    def krb_5_key_as_bytes(self) -> List[bytes]:
        """Value of `krb_5_key` as a list of bytes."""
        return [base64.b64decode(k) for k in self.krb_5_key]

    @krb_5_key_as_bytes.setter
    def krb_5_key_as_bytes(self, value: List[bytes]) -> None:
        """Set value of `krb_5_key` from a list of bytes."""
        if not isinstance(value, list):
            raise TypeError("Argument 'value' must be a list.")
        self.krb_5_key = [base64.b64encode(v).decode("ascii") for v in value]


class User(KelvinObject):
    _class_display_name = "User"
    _kelvin_attrs = KelvinObject._kelvin_attrs + [
        "school",
        "firstname",
        "lastname",
        "birthday",
        "disabled",
        "email",
        "expiration_date",
        "kelvin_password_hashes",
        "password",
        "record_uid",
        "roles",
        "schools",
        "school_classes",
        "workgroups",
        "source_uid",
    ]

    def __init__(
        self,
        name: str = None,
        school: str = None,
        *,
        firstname: str = None,
        lastname: str = None,
        birthday: datetime.date = None,
        disabled: bool = False,
        email: str = None,
        expiration_date: datetime.date = None,
        password: str = None,
        record_uid: str = None,
        roles: List[str],
        schools: List[str],
        school_classes: Dict[str, List[str]] = None,
        workgroups: Dict[str, List[str]] = None,
        source_uid: str = None,
        udm_properties: Dict[str, Any] = None,
        ucsschool_roles: List[str] = None,
        kelvin_password_hashes: PasswordsHashes = None,
        dn: str = None,
        url: str = None,
        session: Session = None,
        language: str = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            ucsschool_roles=ucsschool_roles,
            udm_properties=udm_properties,
            dn=dn,
            url=url,
            session=session,
            language=language,
        )
        self.school = school
        self.firstname = firstname
        self.lastname = lastname
        self.birthday = birthday
        self.disabled = disabled
        self.email = email
        self.expiration_date = expiration_date
        self.password = password
        self.record_uid = record_uid
        self.roles = roles
        self.schools = schools
        self.school_classes = school_classes or {}
        self.workgroups = workgroups or {}
        self.source_uid = source_uid
        self.kelvin_password_hashes = kelvin_password_hashes
        self._resource_class = UserResource

    @classmethod
    def _from_kelvin_response(cls, response: Dict[str, Any]) -> "User":
        for attr in ("roles", "schools"):
            # turn urls to names ('school' will be done in super class)
            response[attr] = [url.rsplit("/", 1)[-1] for url in response[attr]]
        if response["birthday"]:
            response["birthday"] = datetime.datetime.strptime(response["birthday"], "%Y-%m-%d").date()
        if "expiration_date" not in response:
            warnings.warn(
                "User attribute in Kelvin REST API response missing 'expiration_date' attribute. Server "
                "version probably < '1.5.1'.",
                RuntimeWarning,
            )
            response["expiration_date"] = None
        elif response["expiration_date"]:
            response["expiration_date"] = datetime.datetime.strptime(
                response["expiration_date"], "%Y-%m-%d"
            ).date()
        return super()._from_kelvin_response(response)

    def _to_kelvin_request_data(self) -> Dict[str, Any]:
        data = super()._to_kelvin_request_data()
        url_keys = {"roles": "role", "schools": "school"}
        for attr in ("roles", "schools"):
            url_key = url_keys[attr]
            # role/school names to urls
            data[attr] = [f"{self.session.urls[url_key]}{value}" for value in data[attr]]
        if data["kelvin_password_hashes"]:
            data["kelvin_password_hashes"] = self.kelvin_password_hashes.as_dict()
        else:
            del data["kelvin_password_hashes"]
        if data["birthday"]:
            data["birthday"] = data["birthday"].strftime("%Y-%m-%d")
        if data["expiration_date"]:
            data["expiration_date"] = data["expiration_date"].strftime("%Y-%m-%d")
        return {key: value for key, value in data.items() if value is not None}


class UserResource(KelvinResource):
    class Meta:
        kelvin_object: Type[KelvinObject] = User
        required_get_attrs: Iterable[str] = ("name",)
        required_save_attrs: Iterable[str] = ("school", "roles")
        required_search_attrs: Iterable[str] = ()

    def __init__(self, session: Session, language: str = None):
        super().__init__(session=session, language=language)
        self.collection_url = self.session.urls["user"]
        self.object_url = f"{self.session.urls['user']}{{name}}"

    def _check_search_attrs(self, **kwargs) -> None:
        super()._check_search_attrs(**kwargs)
        if "*" in kwargs.get("school", ""):
            raise InvalidRequest("Argument 'school' for searching users must be exact.")
