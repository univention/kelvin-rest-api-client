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

import base64
import json
from typing import Dict, List, Optional

import httpx
import pytest
from async_property import async_property
from faker import Faker

from ucsschool.kelvin.client import InvalidRequest, RoleResource, Session

fake = Faker()

HOST = "dummy.fqdn"
ROLES_URL = f"https://{HOST}/ucsschool/kelvin/v2/roles/"
ROLE_NAMES = ["staff", "student", "teacher", "legal_guardian", "school_admin"]


class SessionMock:
    @async_property
    async def token(self) -> str:
        return "Token"


def role(name: str) -> Dict[str, str]:
    return {"name": name, "display_name": name, "url": f"{ROLES_URL}{name}"}


def link_header(rels: Dict[str, str]) -> str:
    return ", ".join(f'<{url}>; rel="{rel}"' for rel, url in rels.items())


def encode_cursor(direction: str, name: str) -> str:
    return base64.urlsafe_b64encode(json.dumps({direction: name}).encode()).decode().rstrip("=")


def decode_cursor(cursor: str) -> Dict[str, str]:
    return json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))


def paginating_handler(requests: List[httpx.Request], relative_links: bool = False):
    """
    Serve ROLE_NAMES like Kelvin v2: with ``limit``, one page sorted by name, and a ``Link``
    header (RFC 8288) with ``first``, ``prev``, ``next`` and ``last`` URLs, which keep all
    search parameters and address the page with an opaque ``cursor``. Only forward paging is
    implemented, as the client only follows ``next``.
    """
    names = sorted(ROLE_NAMES)

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        params = request.url.params
        if "limit" not in params:
            return httpx.Response(200, json=[role(name) for name in ROLE_NAMES])
        limit = int(params["limit"])
        after = decode_cursor(params["cursor"])["after"] if "cursor" in params else None
        rest = [name for name in names if after is None or name > after]
        page = rest[:limit]
        base = "/ucsschool/kelvin/v2/roles/" if relative_links else ROLES_URL

        def page_url(cursor: Optional[str]) -> str:
            url = httpx.URL(base, params=params.remove("cursor"))
            return str(url.copy_merge_params({"cursor": cursor}) if cursor else url)

        rels = {"first": page_url(None)}
        if after is not None:
            rels["prev"] = page_url(encode_cursor("before", page[0]))
        if len(rest) > limit:
            rels["next"] = page_url(encode_cursor("after", page[-1]))
        rels["last"] = page_url(encode_cursor("before", ""))
        return httpx.Response(
            200, json=[role(name) for name in page], headers={"Link": link_header(rels)}
        )

    return handler


def make_session(handler) -> Session:
    return Session(
        username="admin",
        password=fake.password(),
        host=HOST,
        api_version="v2",
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("relative_links", (False, True), ids=("absolute", "relative"))
@pytest.mark.parametrize("page_size", (1, 2, 5, 10))
async def test_search_page_size_follows_next_links(mocker, page_size, relative_links):
    mocker.patch("ucsschool.kelvin.client.session.Session.token", SessionMock.token)
    requests: List[httpx.Request] = []
    async with make_session(paginating_handler(requests, relative_links)) as session:
        objs = [obj async for obj in RoleResource(session=session).search(page_size=page_size)]
    assert [obj.name for obj in objs] == sorted(ROLE_NAMES)
    assert len(requests) == -(-len(ROLE_NAMES) // page_size)
    assert all(req.url.params["limit"] == str(page_size) for req in requests)
    assert all(obj.session is session for obj in objs)


@pytest.mark.asyncio
async def test_search_page_size_keeps_search_params(mocker):
    mocker.patch("ucsschool.kelvin.client.session.Session.token", SessionMock.token)
    requests: List[httpx.Request] = []
    async with make_session(paginating_handler(requests)) as session:
        _ = [obj async for obj in RoleResource(session=session).search(page_size=2, name="s*")]
    assert len(requests) == 3
    assert all(req.url.params["name"] == "s*" for req in requests)


@pytest.mark.asyncio
async def test_search_limit_fetches_single_page(mocker):
    mocker.patch("ucsschool.kelvin.client.session.Session.token", SessionMock.token)
    requests: List[httpx.Request] = []
    async with make_session(paginating_handler(requests)) as session:
        objs = [obj async for obj in RoleResource(session=session).search(limit=2)]
    assert [obj.name for obj in objs] == sorted(ROLE_NAMES)[:2]
    assert len(requests) == 1


@pytest.mark.asyncio
async def test_search_page_size_without_link_header(mocker):
    """Servers without pagination support (v1) return everything in one response."""
    mocker.patch("ucsschool.kelvin.client.session.Session.token", SessionMock.token)
    requests: List[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=[role(name) for name in ROLE_NAMES])

    async with make_session(handler) as session:
        objs = [obj async for obj in RoleResource(session=session).search(page_size=2)]
    assert [obj.name for obj in objs] == ROLE_NAMES
    assert len(requests) == 1


@pytest.mark.asyncio
async def test_search_page_size_stops_on_repeated_next_link(mocker):
    mocker.patch("ucsschool.kelvin.client.session.Session.token", SessionMock.token)
    requests: List[httpx.Request] = []
    next_url = f"{ROLES_URL}?limit=1&cursor={encode_cursor('after', 'staff')}"

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200, json=[role("staff")], headers={"Link": link_header({"next": next_url})}
        )

    async with make_session(handler) as session:
        objs = [obj async for obj in RoleResource(session=session).search(page_size=1)]
    assert len(requests) == 2
    assert len(objs) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kwargs",
    (
        {"page_size": 2, "limit": 2},
        {"page_size": 0},
        {"page_size": -1},
        {"page_size": "2"},
        {"page_size": True},
    ),
)
async def test_search_page_size_invalid(kwargs):
    session = Session(username="admin", password=fake.password(), host=HOST, api_version="v2")
    with pytest.raises(InvalidRequest):
        _ = [obj async for obj in RoleResource(session=session).search(**kwargs)]
