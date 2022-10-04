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
from .session import Session

logger = logging.getLogger(__name__)


class School(KelvinObject):
    _class_display_name = "School"
    _kelvin_attrs = KelvinObject._kelvin_attrs + [
        "display_name",
        "educational_servers",
        "administrative_servers",
        "class_share_file_server",
        "home_share_file_server",
    ]

    def __init__(
        self,
        name: str,
        *,
        display_name: str = None,
        educational_servers: List[str] = None,
        administrative_servers: List[str] = None,
        class_share_file_server: str = None,
        home_share_file_server: str = None,
        ucsschool_roles: List[str] = None,
        udm_properties: Dict[str, Any] = None,
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
        self.display_name = display_name
        self.educational_servers = educational_servers
        self.administrative_servers = administrative_servers
        self.class_share_file_server = class_share_file_server
        self.home_share_file_server = home_share_file_server
        self._resource_class = SchoolResource

    async def save(self) -> "SchoolResource":
        if self.url:
            raise NotImplementedError(
                "Modification of school objects has not yet been implemented in the Kelvin REST API."
            )
        return await super().save()

    async def delete(self) -> None:
        raise NotImplementedError(
            "Deleting school objects has not yet been implemented in the Kelvin REST API."
        )

    def _to_kelvin_request_data(self) -> Dict[str, Any]:
        data = super()._to_kelvin_request_data()
        # passing None will produce a validation error, OK is not passing it or passing an empty list
        if data["educational_servers"] is None:
            del data["educational_servers"]
        if data["administrative_servers"] is None:
            del data["administrative_servers"]
        return data


class SchoolResource(KelvinResource):
    class Meta:
        kelvin_object: Type[KelvinObject] = School
        required_get_attrs: Iterable[str] = ("name",)
        required_head_attrs: Iterable[str] = ("name",)
        required_save_attrs: Iterable[str] = ("name",)
        required_search_attrs: Iterable[str] = ()

    def __init__(self, session: Session, language: str = None):
        super().__init__(session=session, language=language)
        self.collection_url = self.session.urls["school"]
        self.object_url = f"{self.session.urls['school']}{{name}}"
