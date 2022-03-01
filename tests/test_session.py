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

import sys
import warnings

import pytest
from async_property import async_property

from ucsschool.kelvin.client.session import BadSettingsWarning, Session

_PYTHON_VERSION = sys.version_info[:2]
kelvin_session_kwargs_mock = {
    "username": "username",
    "password": "password",
    "host": "localhost",
    "verify": False,
}


class SessionMock:
    @async_property
    async def token(self) -> str:
        return "Token"


def call_kwargs(call_args):
    if _PYTHON_VERSION < (3, 8):
        return call_args[1]
    else:
        return call_args.kwargs


@pytest.mark.asyncio
async def test_session_closes_on_context_exit():
    async with Session(**kelvin_session_kwargs_mock) as session:
        assert session._client
    with pytest.raises(RuntimeError):
        print(session.client)


@pytest.mark.asyncio
@pytest.mark.parametrize("arg_client_tasks", range(-10, 11))
async def test_session_warn_max_client_tasks(arg_client_tasks):
    with warnings.catch_warnings(record=True) as w:
        async with Session(max_client_tasks=arg_client_tasks, **kelvin_session_kwargs_mock) as session:
            assert session.max_client_tasks >= 4
        if arg_client_tasks < 4:
            assert len(w) == 1
            assert issubclass(w[-1].category, BadSettingsWarning)
            assert "max_client_tasks" in str(w[-1].message)


@pytest.mark.asyncio
async def test_session_default_timeout(mocker):
    mocker.patch("httpx.AsyncClient.get", side_effect=NotImplementedError)
    mocker.patch("ucsschool.kelvin.client.session.Session.token", SessionMock.token)
    async with Session(**kelvin_session_kwargs_mock) as session:
        try:
            await session.get("http://example.com")
        except NotImplementedError:
            pass
        assert call_kwargs(session.client.get.call_args)["timeout"] == 10.0


@pytest.mark.asyncio
async def test_session_timeout(mocker):
    mocker.patch("httpx.AsyncClient.get", side_effect=NotImplementedError)
    mocker.patch("ucsschool.kelvin.client.session.Session.token", SessionMock.token)
    kelvin_session_kwargs = dict(kelvin_session_kwargs_mock, timeout=5)
    async with Session(**kelvin_session_kwargs) as session:
        try:
            await session.get("http://example.com")
        except NotImplementedError:
            pass
        assert call_kwargs(session.client.get.call_args)["timeout"] == 5


@pytest.mark.asyncio
async def test_session_explicit_timeout(mocker):
    mocker.patch("httpx.AsyncClient.get", side_effect=NotImplementedError)
    mocker.patch("ucsschool.kelvin.client.session.Session.token", SessionMock.token)
    async with Session(**kelvin_session_kwargs_mock) as session:
        try:
            await session.get("http://example.com", timeout=7)
        except NotImplementedError:
            pass
        assert call_kwargs(session.client.get.call_args)["timeout"] == 7


@pytest.mark.asyncio
async def test_session_override_timeout(mocker):
    mocker.patch("httpx.AsyncClient.get", side_effect=NotImplementedError)
    mocker.patch("ucsschool.kelvin.client.session.Session.token", SessionMock.token)
    kelvin_session_kwargs = dict(kelvin_session_kwargs_mock, timeout=4)
    async with Session(**kelvin_session_kwargs) as session:
        try:
            await session.get("http://example.com", timeout=6)
        except NotImplementedError:
            pass
        assert call_kwargs(session.client.get.call_args)["timeout"] == 6
