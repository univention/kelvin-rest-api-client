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
from abc import ABC
from typing import Any, AsyncIterator, Dict, Iterable, List, TypeVar

from .exceptions import InvalidRequest, NoObject
from .session import Session

KelvinObjectType = TypeVar("KelvinObjectType", bound="KelvinObject")

logger = logging.getLogger(__name__)


class KelvinObject(ABC):
    _class_display_name = "Kelvin Object"
    _kelvin_attrs = ["name", "ucsschool_roles"]

    def __init__(
        self,
        name: str,
        *,
        ucsschool_roles: List[str] = None,
        dn: str = None,
        url: str = None,
        session: Session = None,
    ):
        self.name = name
        self.ucsschool_roles = ucsschool_roles
        self.dn = dn
        self.url = url
        self.session = session
        self._resource_class = KelvinResource
        self._fresh = True
        self._deleted = False
        self._old_attrs = {}
        self._update_old_attrs()

    def __repr__(self):
        req_attrs_vals = [
            f"{attr!r}={value!r}" for attr, value in self._required_get_attrs.items()
        ]
        if hasattr(self, "dn") and self.dn:
            req_attrs_vals.append(f"dn={self.dn!r}")
        return f"{self.__class__.__name__}({', '.join(req_attrs_vals)})"

    async def reload(self) -> KelvinObjectType:
        """
        Reload properties of object from the Kelvin API.

        :raises ucsschool.kelvin.client.NoObject: if the object cannot be found
        :return: self
        """
        if self._deleted:
            logger.warning(
                "%s %s has been deleted! Trying to load it anyway...",
                self._class_display_name,
                self,
            )
        obj = await self._resource_class(session=self.session).get(
            **self._required_get_attrs
        )
        for k, v in obj.as_dict().items():
            setattr(self, k, v)
        self._update_old_attrs()
        self._fresh = True
        return self

    async def save(self) -> KelvinObjectType:
        if self._deleted:
            raise RuntimeError(f"{self} has been deleted.")
        if not all(self._required_get_attrs.values()):
            raise AssertionError(
                f"{self.__class__.__name__}.save() requires attribute(s) to be set: "
                f"{', '.join(self._resource_class.Meta.required_get_attrs)}."
            )
        if not self._fresh:
            logger.debug("Saving possibly stale Kelvin object instance.")
        data = self._to_kelvin_request_data()
        # assumption: if self.url was set, the object exists in the Kelvin API
        # so if its not set, we'll try to create the object
        if not self.url:
            resp_json = await self.session.post(
                url=self._resource_class(session=self.session).collection_url, json=data
            )
            resp_obj = self._from_kelvin_response(resp_json)
            for k, v in resp_obj.as_dict().items():
                setattr(self, k, v)
            self._fresh = False
            return self
        # self.url was is set -> modify object
        # TODO: or creation failed and this is the fall-back
        resp_json = await self.session.put(url=self.url, json=data)
        resp_obj = self._from_kelvin_response(resp_json)
        for k, v in resp_obj.as_dict().items():
            setattr(self, k, v)
        self._fresh = False
        return self

    async def delete(self) -> None:
        if self._deleted:
            logger.warning("%s has already been deleted.", self)
            return
        if not self.url:
            raise RuntimeError(
                "Attribute 'url' unset. Run 'reload()' before 'delete()'."
            )
        await self.session.delete(self.url)
        self._deleted = True

    def as_dict(self) -> Dict[str, Any]:
        attrs = self._kelvin_attrs + ["dn", "url"]
        return dict((attr, getattr(self, attr)) for attr in attrs)

    @classmethod
    def _from_kelvin_response(cls, response: Dict[str, Any]) -> KelvinObjectType:
        try:
            # school url to school name
            school_url = response["school"]
            tmp = school_url.rsplit("/", 1)[-1]
            response["school"] = tmp.split("?")[0]
        except (IndexError, KeyError):
            pass
        return cls(**response)

    def _to_kelvin_request_data(self) -> Dict[str, Any]:
        data = self.as_dict()
        if not data["ucsschool_roles"]:
            del data["ucsschool_roles"]
        del data["dn"]
        del data["url"]
        try:
            # school name to school url
            data["school"] = f"{self.session.urls['school']}{data['school']}"
        except KeyError:
            pass
        return data

    @property
    def _required_get_attrs(self) -> Dict[str, Any]:
        return dict(
            (attr, getattr(self, attr))
            for attr in self._resource_class.Meta.required_get_attrs
        )

    def _update_old_attrs(self):
        self._old_attrs.update(self._required_get_attrs)


class KelvinResource(ABC):
    class Meta:
        kelvin_object: KelvinObjectType = KelvinObject
        required_get_attrs: Iterable[str] = ("name",)
        required_search_attrs: Iterable[str] = ("school",)

    def __init__(self, session: Session):
        self.session = session
        self.collection_url = ""
        self.object_url = ""

    async def get(self, **kwargs) -> KelvinObjectType:
        if not all(attr in kwargs for attr in self.Meta.required_get_attrs):
            raise AssertionError(
                f"{self.__class__.__name__}.get() requires argument(s): "
                f"{', '.join(self.Meta.required_get_attrs)}."
            )
        url = self.object_url.format(**kwargs)
        try:
            return await self.get_from_url(url)
        except NoObject as exc:
            raise NoObject(
                f"{self.Meta.kelvin_object._class_display_name} not found at URL {url!r} using "
                f"attributes {kwargs!r}.",
                reason=exc.reason,
                status=exc.status,
                url=url,
            ) from exc

    async def get_from_url(self, url: str) -> KelvinObjectType:
        resp_json: Dict[str, Any] = await self.session.get(url)
        obj = self.Meta.kelvin_object._from_kelvin_response(resp_json)
        obj.session = self.session
        return obj

    async def search(self, **kwargs) -> AsyncIterator[KelvinObjectType]:
        self._check_search_attrs(**kwargs)
        # not necessary, but will simplify the query string
        for k in [k for k, v in kwargs.items() if v in ("", "*")]:
            del kwargs[k]
        resp_json: List[Dict[str, Any]] = await self.session.get(
            self.collection_url, params=kwargs
        )
        for resp in resp_json:
            obj = self.Meta.kelvin_object._from_kelvin_response(resp)
            obj.session = self.session
            yield obj

    def _check_search_attrs(self, **kwargs) -> None:
        """
        :raises ucsschool.kelvin.client.InvalidRequest: when there is a problem with the kwargs
            for `search()`
        """
        if not all(attr in kwargs for attr in self.Meta.required_search_attrs):
            raise InvalidRequest(
                f"{self.__class__.__name__}.search() requires argument(s): "
                f"{', '.join(self.Meta.required_search_attrs)}."
            )
