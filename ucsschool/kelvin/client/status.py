# -*- coding: utf-8 -*-
#
# Copyright 2022 Univention GmbH
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

from __future__ import annotations

from typing import Any, Dict

from .session import Session


class Status:
    def __init__(
        self,
        *,
        internal_errors_last_minute: int,
        version: str,
        url: str = None,
        session: Session = None,
    ):
        self.internal_errors_last_minute = internal_errors_last_minute
        self.version = version
        self.url = url
        self.session = session
        self._attrs = ["internal_errors_last_minute", "version", "url"]
        self._resource_class = StatusResource

    def __repr__(self):
        attrs_vals = [f"{attr!r}={value!r}" for attr, value in self.as_dict().items()]
        return f"{self.__class__.__name__}({', '.join(attrs_vals)})"

    def as_dict(self) -> Dict[str, Any]:
        return {attr: getattr(self, attr) for attr in self._attrs}

    async def reload(self) -> Status:
        obj: Status = await self._resource_class(session=self.session).get()
        for k, v in obj.as_dict().items():
            setattr(self, k, v)
        return self

    @classmethod
    def _from_kelvin_response(cls, response: Dict[str, Any]) -> Status:
        return cls(**response)


class StatusResource:
    class Meta:
        kelvin_object = Status

    def __init__(self, session: Session):
        self.session = session
        self.url = self.session.urls["status"]

    async def get(self) -> Status:
        return await self.get_from_url(self.url)

    async def get_from_url(self, url: str) -> Status:
        resp_json: Dict[str, Any] = await self.session.get(url)
        obj = self.Meta.kelvin_object._from_kelvin_response(resp_json)
        obj.session = self.session
        return obj
