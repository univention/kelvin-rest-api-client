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

import random

import pytest
from faker import Faker

from ucsschool.kelvin.client import RoleResource, Session

fake = Faker()


API_VERSION = "v1"
URL_BASE = "https://{host}/ucsschool/kelvin"
URL_TOKEN = f"{URL_BASE}/token"
URL_ROLE_RESOURCE = f"{URL_BASE}/{API_VERSION}/roles/"
URL_ROLE_COLLECTION = URL_ROLE_RESOURCE
URL_ROLE_OBJECT = f"{URL_ROLE_RESOURCE}{{name}}"


@pytest.mark.asyncio
async def test_search_no_name_arg(compare_kelvin_obj_with_test_data, kelvin_session_kwargs):
    async with Session(**kelvin_session_kwargs) as session:
        objs = [obj async for obj in RoleResource(session=session).search()]

    assert objs, "No roles found."
    assert len(objs) == 3
    for obj in objs:
        assert not hasattr(obj, "dn")
        assert not hasattr(obj, "ucsschool_roles")
    assert {"staff", "student", "teacher"} == {obj.name for obj in objs}


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["staff", "student", "teacher"])
async def test_get_from_url(compare_kelvin_obj_with_test_data, kelvin_session_kwargs, role):
    url = URL_ROLE_OBJECT.format(host=kelvin_session_kwargs["host"], name=role)
    async with Session(**kelvin_session_kwargs) as session:
        obj = await RoleResource(session=session).get_from_url(url)
    assert obj.name == role


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["staff", "student", "teacher"])
async def test_get(compare_kelvin_obj_with_test_data, kelvin_session_kwargs, role):
    async with Session(**kelvin_session_kwargs) as session:
        obj = await RoleResource(session=session).get(name=role)
    assert obj.name == role


@pytest.mark.asyncio
async def test_role_attrs(compare_kelvin_obj_with_test_data, kelvin_session_kwargs):
    role = random.choice(("staff", "student", "teacher"))
    async with Session(**kelvin_session_kwargs) as session:
        obj = await RoleResource(session=session).get(name=role)
    assert obj.name == role
    assert set(obj._kelvin_attrs) == {"name", "display_name"}
    assert set(obj.as_dict().keys()) == {"name", "display_name", "url"}
