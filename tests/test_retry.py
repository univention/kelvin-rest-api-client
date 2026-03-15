# Copyright 2026 Univention GmbH
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

import httpx
import pytest
from async_property import async_property

from ucsschool.kelvin.client.exceptions import NoObject, ServerError
from ucsschool.kelvin.client.session import Session

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


def make_async_mock(results):
    if not isinstance(results, list):
        results = [results]
    it = iter(results)

    async def side_effect(*args, **kwargs):
        res = next(it)
        if isinstance(res, Exception):
            raise res
        return res

    return side_effect


@pytest.mark.asyncio
async def test_session_retry_on_502(mocker):
    mocker.patch("ucsschool.kelvin.client.session.Session.token", SessionMock.token)

    # Mock response to return 502 then 200
    mock_response_502 = mocker.Mock(spec=httpx.Response)
    mock_response_502.status_code = 502
    mock_response_502.reason_phrase = "Bad Gateway"
    mock_response_502.json.return_value = {"detail": "Server error"}

    mock_response_200 = mocker.Mock(spec=httpx.Response)
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"success": True}

    mock_get = mocker.patch(
        "httpx.AsyncClient.get",
        side_effect=make_async_mock([mock_response_502, mock_response_502, mock_response_200]),
    )
    mock_get.__name__ = "get"

    # Passing retry_wait_fixed via kwargs to keep tests fast
    async with Session(retries=2, **kelvin_session_kwargs_mock) as session:
        session._max_retry_pause = 0.1
        session._min_retry_pause = 0.1
        resp = await session.get("http://example.com/api")
        assert resp == {"success": True}
        # In pytest-mock, when using side_effect, the mock itself is called
        assert mock_get.call_count == 3


@pytest.mark.asyncio
async def test_session_no_retry_on_404(mocker):
    mocker.patch("ucsschool.kelvin.client.session.Session.token", SessionMock.token)

    mock_response_404 = mocker.Mock(spec=httpx.Response)
    mock_response_404.status_code = 404
    mock_response_404.reason_phrase = "Not Found"
    mock_response_404.json.return_value = {"detail": "Not found"}

    mock_get = mocker.patch("httpx.AsyncClient.get", side_effect=make_async_mock(mock_response_404))
    mock_get.__name__ = "get"

    async with Session(retries=2, **kelvin_session_kwargs_mock) as session:
        session._max_retry_pause = 0.1
        session._min_retry_pause = 0.1
        with pytest.raises(NoObject):
            await session.get("http://example.com/api")
        assert mock_get.call_count == 1


@pytest.mark.asyncio
async def test_session_exhaust_retries(mocker):
    mocker.patch("ucsschool.kelvin.client.session.Session.token", SessionMock.token)

    mock_response_502 = mocker.Mock(spec=httpx.Response)
    mock_response_502.status_code = 502
    mock_response_502.reason_phrase = "Bad Gateway"
    mock_response_502.json.return_value = {"detail": "Server error"}

    mock_get = mocker.patch(
        "httpx.AsyncClient.get", side_effect=make_async_mock([mock_response_502, mock_response_502])
    )
    mock_get.__name__ = "get"

    async with Session(retries=1, **kelvin_session_kwargs_mock) as session:
        session._max_retry_pause = 0.1
        session._min_retry_pause = 0.1
        with pytest.raises(ServerError):
            await session.get("http://example.com/api")
        assert mock_get.call_count == 2


@pytest.mark.asyncio
async def test_session_retries_disabled_by_default(mocker):
    mocker.patch("ucsschool.kelvin.client.session.Session.token", SessionMock.token)

    mock_response_502 = mocker.Mock(spec=httpx.Response)
    mock_response_502.status_code = 502
    mock_response_502.reason_phrase = "Bad Gateway"
    mock_response_502.json.return_value = {"detail": "Server error"}

    mock_get = mocker.patch("httpx.AsyncClient.get", side_effect=make_async_mock(mock_response_502))
    mock_get.__name__ = "get"

    async with Session(**kelvin_session_kwargs_mock) as session:
        with pytest.raises(ServerError):
            await session.get("http://example.com/api")
        assert mock_get.call_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exception",
    [
        httpx.RemoteProtocolError("Server disconnected"),
        httpx.NetworkError("Network issue"),
        httpx.ConnectError("Connection refused"),
    ],
    ids=["RemoteProtocolError", "NetworkError", "ConnectError"],
)
async def test_session_retry_on_network_errors(mocker, exception):
    mocker.patch("ucsschool.kelvin.client.session.Session.token", SessionMock.token)

    mock_response_200 = mocker.Mock(spec=httpx.Response)
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"success": True}

    mock_get = mocker.patch(
        "httpx.AsyncClient.get",
        side_effect=make_async_mock([exception, mock_response_200]),
    )
    mock_get.__name__ = "get"

    async with Session(retries=1, **kelvin_session_kwargs_mock) as session:
        session._max_retry_pause = 0.1
        session._min_retry_pause = 0.1
        resp = await session.get("http://example.com/api")
        assert resp == {"success": True}
        assert mock_get.call_count == 2
