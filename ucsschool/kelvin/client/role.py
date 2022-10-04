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
from typing import Any, Dict, Iterable, Type

from .base import KelvinObject, KelvinResource
from .session import Session

logger = logging.getLogger(__name__)


class Role(KelvinObject):
    _class_display_name = "Role"
    _kelvin_attrs = ["name", "display_name"]

    def __init__(
        self,
        name: str,
        *,
        display_name: str = None,
        url: str = None,
        session: Session = None,
        language: str = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            ucsschool_roles=None,
            udm_properties=None,
            dn=None,
            url=url,
            session=session,
            language=language,
        )
        self.display_name = display_name
        del self.dn
        del self.ucsschool_roles
        del self.udm_properties
        self._resource_class = RoleResource

    async def save(self) -> "RoleResource":
        raise NotImplementedError(
            "Creating and changing of school roles has not yet been "
            "implemented in the Kelvin REST API."
        )

    async def delete(self) -> None:
        raise NotImplementedError(
            "Deleting school roles has not yet been implemented in the " "Kelvin REST API."
        )

    def as_dict(self) -> Dict[str, Any]:
        attrs = self._kelvin_attrs + ["url"]
        return dict((attr, getattr(self, attr)) for attr in attrs)


class RoleResource(KelvinResource):
    class Meta:
        kelvin_object: Type[KelvinObject] = Role
        required_get_attrs: Iterable[str] = ("name",)
        required_search_attrs: Iterable[str] = ()

    def __init__(self, session: Session, language: str = None):
        super().__init__(session=session, language=language)
        self.collection_url = self.session.urls["role"]
        self.object_url = f"{self.session.urls['role']}{{name}}"
