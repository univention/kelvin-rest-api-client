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

import logging
from typing import Any, Dict, Iterable, List, Type

from .base import KelvinObject, KelvinResource
from .exceptions import InvalidRequest
from .session import Session

logger = logging.getLogger(__name__)


class SchoolClass(KelvinObject):
    _class_display_name = "School class"
    _kelvin_attrs = KelvinObject._kelvin_attrs + ["school", "description", "users"]

    def __init__(
        self,
        name: str,
        school: str,
        *,
        description: str = None,
        users: List[str] = None,
        ucsschool_roles: List[str] = None,
        udm_properties: Dict[str, Any] = None,
        dn: str = None,
        url: str = None,
        session: Session = None,
    ):
        super().__init__(
            name=name,
            ucsschool_roles=ucsschool_roles,
            udm_properties=udm_properties,
            dn=dn,
            url=url,
            session=session,
        )
        self.school = school
        self.description = description
        self.users = users
        self._resource_class = SchoolClassResource

    @classmethod
    def _from_kelvin_response(cls, response: Dict[str, Any]) -> "SchoolClass":
        # user urls to user names
        response["users"] = [url.rsplit("/", 1)[-1] for url in response["users"]]
        # 'school' will be done in super class
        return super()._from_kelvin_response(response)

    def _to_kelvin_request_data(self) -> Dict[str, Any]:
        data = super()._to_kelvin_request_data()
        # users names to urls
        data["users"] = [f"{self.session.urls['user']}{user}" for user in data["users"]]
        return data


class SchoolClassResource(KelvinResource):
    class Meta:
        kelvin_object: Type[KelvinObject] = SchoolClass
        required_get_attrs: Iterable[str] = ("name", "school")
        required_search_attrs: Iterable[str] = ("school",)

    def __init__(self, session: Session):
        super().__init__(session=session)
        self.collection_url = self.session.urls["class"]
        self.object_url = f"{self.session.urls['class']}{{school}}/{{name}}"

    def _check_search_attrs(self, **kwargs) -> None:
        super()._check_search_attrs(**kwargs)
        if "*" in kwargs["school"]:
            raise InvalidRequest("Argument 'school' for searching school classes must be exact.")
