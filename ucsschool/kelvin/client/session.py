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

import asyncio
import datetime
import logging
import warnings
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import httpx
import jwt
from async_property import async_property

from .exceptions import InvalidRequest, InvalidToken, NoObject, ServerError

DN = str

API_VERSION = "v1"
URL_BASE = "https://{host}/ucsschool/kelvin"
URL_TOKEN = f"{URL_BASE}/token"
URL_RESOURCE_CLASS = f"{URL_BASE}/{API_VERSION}/classes/"
URL_RESOURCE_ROLE = f"{URL_BASE}/{API_VERSION}/roles/"
URL_RESOURCE_SCHOOL = f"{URL_BASE}/{API_VERSION}/schools/"
URL_RESOURCE_USER = f"{URL_BASE}/{API_VERSION}/users/"
logger = logging.getLogger(__name__)


class KelvinClientWarning(Warning):
    ...


class BadSettingsWarning(KelvinClientWarning):
    ...


@dataclass
class Token:
    expiry: datetime.datetime
    value: str

    @classmethod
    def from_str(cls, token_str: str) -> "Token":
        try:
            payload = jwt.decode(token_str, verify=False)
        except jwt.PyJWTError as exc:
            raise InvalidToken(f"Error decoding token ({token_str!r}): {exc!s}")
        if not isinstance(payload, dict) or "exp" not in payload:
            raise InvalidToken(
                f"Payload in token not a dict or missing 'exp' entry ({token_str!r})."
            )
        try:
            expiry = datetime.datetime.utcfromtimestamp(payload["exp"])
        except ValueError as exc:
            raise InvalidToken(f"Error parsing date in token ({token_str!r}): {exc!s}")
        return cls(expiry=expiry, value=token_str,)

    def is_valid(self):
        if not self.expiry or not self.value:
            return False
        if datetime.datetime.utcnow() > self.expiry:
            return False
        return True


class Session:
    def __init__(
        self,
        username: str,
        password: str,
        host: str,
        max_client_tasks: int = 10,
        **kwargs,
    ):
        if max_client_tasks < 4:
            txt = "Raising value of 'max_client_tasks' to its minimum of 4."
            warnings.warn(txt, BadSettingsWarning)
            logger.warning(txt)
            max_client_tasks = 4
        self.max_client_tasks = max_client_tasks
        self._client: Optional[httpx.AsyncClient] = None
        self._client_task_limiter = asyncio.Semaphore(max_client_tasks)
        self.username = username
        self.password = password
        self.host = host
        self.kwargs = kwargs
        self.urls = {
            "token": URL_TOKEN.format(host=host),
            "class": URL_RESOURCE_CLASS.format(host=host),
            "role": URL_RESOURCE_ROLE.format(host=host),
            "school": URL_RESOURCE_SCHOOL.format(host=host),
            "user": URL_RESOURCE_USER.format(host=host),
        }
        self._token: Optional[Token] = None

    async def __aenter__(self):
        self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def open(self) -> httpx.AsyncClient:
        if not self._client:
            self._client = httpx.AsyncClient(**self.kwargs)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
        self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if not self._client:
            raise RuntimeError("Session is closed.")
        return self._client

    @async_property
    async def token(self) -> str:
        if not self._token or not self._token.is_valid():
            resp_json = await self.post(
                self.urls["token"],
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={"username": self.username, "password": self.password},
            )
            self._token = Token.from_str(resp_json["access_token"])
        return self._token.value

    @async_property
    async def json_headers(self) -> Dict[str, str]:
        return {
            "accept": "application/json",
            "Authorization": f"Bearer {await self.token}",
            "Content-Type": "application/json",
        }

    async def request(
        self, async_request_method: Any, url: str, return_json: bool = True, **kwargs
    ) -> Union[str, Dict[str, Any]]:
        if "headers" not in kwargs:
            kwargs["headers"] = await self.json_headers
        if "timeout" not in kwargs:
            kwargs["timeout"] = 10.0
        response: httpx.Response = await async_request_method(url, **kwargs)
        try:
            resp_json = response.json()
            if "detail" in resp_json:
                detail = resp_json["detail"]
            else:
                detail = ""
        except ValueError:
            detail = ""
            resp_json = {}
        logger.debug(
            "%s %r (**%r) -> %r %r%s",
            async_request_method.__name__.upper(),
            url,
            kwargs,
            response.status_code,
            response.reason_phrase,
            f" ({detail})" if detail else "",
        )
        if 200 <= response.status_code <= 299:
            if return_json:
                return resp_json
            else:
                return response.text
        elif response.status_code == 404:
            raise NoObject(
                f"Object not found ({async_request_method.__name__.upper()} {url!r}).",
                reason=response.reason_phrase,
                status=response.status_code,
                url=url,
            )
        elif 400 <= response.status_code <= 499:
            raise InvalidRequest(
                f"Kelvin REST API returned status {response.status_code}, reason "
                f"{response.reason_phrase!r}{f' ({detail})' if detail else ''} for "
                f"{async_request_method.__name__.upper()} {url!r}.",
                reason=response.reason_phrase,
                status=response.status_code,
                url=url,
            )
        else:
            raise ServerError(
                reason=response.reason_phrase, status=response.status_code, url=url
            )  # pragma: no cover

    async def delete(self, url: str, **kwargs) -> None:
        await self.request(self.client.delete, url, return_json=False, **kwargs)

    async def get(
        self, url: str, **kwargs
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        return await self.request(self.client.get, url, **kwargs)

    # async def patch(self, url: str, **kwargs,) -> Dict[str, Any]:
    #     return await self.request(self.client.patch, url, **kwargs)

    async def post(self, url: str, **kwargs,) -> Dict[str, Any]:
        return await self.request(self.client.post, url, **kwargs)

    async def put(self, url: str, **kwargs,) -> Dict[str, Any]:
        return await self.request(self.client.put, url, **kwargs)
