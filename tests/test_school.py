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

from dataclasses import asdict

import ldap3
import pytest
from faker import Faker

from ucsschool.kelvin.client import School, SchoolResource, Session

fake = Faker()


API_VERSION = "v1"
URL_BASE = "https://{host}/ucsschool/kelvin"
URL_TOKEN = f"{URL_BASE}/token"
URL_SCHOOL_RESOURCE = f"{URL_BASE}/{API_VERSION}/schools/"
URL_SCHOOL_COLLECTION = URL_SCHOOL_RESOURCE
URL_SCHOOL_OBJECT = f"{URL_SCHOOL_RESOURCE}{{name}}"


@pytest.mark.asyncio
async def test_search_no_name_arg(
    compare_kelvin_obj_with_test_data, new_school, kelvin_session_kwargs,
):
    school1, school2 = new_school(2)

    async with Session(**kelvin_session_kwargs) as session:
        objs = [obj async for obj in SchoolResource(session=session).search()]

    assert objs, "No Schools found."
    assert len(objs) >= 2
    assert school1.dn in [school.dn for school in objs]
    assert school2.dn in [school.dn for school in objs]
    for obj in objs:
        if obj.dn == school1.dn:
            compare_kelvin_obj_with_test_data(obj, **asdict(school1))
        if obj.dn == school2.dn:
            compare_kelvin_obj_with_test_data(obj, **asdict(school2))


@pytest.mark.asyncio
async def test_search_partial_name_arg(
    compare_kelvin_obj_with_test_data, kelvin_session_kwargs, new_school,
):
    school = new_school(1)[0]
    name_len = len(school.name)
    name_begin = school.name[: int(name_len / 2)]
    name_end = school.name[len(name_begin) :]

    async with Session(**kelvin_session_kwargs) as session:
        objs1 = [
            obj
            async for obj in SchoolResource(session=session).search(
                name=f"{name_begin}*"
            )
        ]
        objs2 = [
            obj
            async for obj in SchoolResource(session=session).search(name=f"*{name_end}")
        ]
    assert objs1, f"No School for name='{name_begin}*' found."
    assert len(objs1) >= 1
    assert school.dn in [o.dn for o in objs1]
    assert objs2, f"No School for name='*{name_end}' found."
    assert len(objs2) >= 1
    assert school.dn in [o.dn for o in objs2]


@pytest.mark.asyncio
async def test_get_from_url(
    compare_kelvin_obj_with_test_data, kelvin_session_kwargs, new_school,
):
    school = new_school(1)[0]
    url = URL_SCHOOL_OBJECT.format(host=kelvin_session_kwargs["host"], name=school.name)
    async with Session(**kelvin_session_kwargs) as session:
        obj = await SchoolResource(session=session).get_from_url(url)
    compare_kelvin_obj_with_test_data(obj, **asdict(school))


@pytest.mark.asyncio
async def test_get(
    compare_kelvin_obj_with_test_data, kelvin_session_kwargs, new_school,
):
    school = new_school(1)[0]
    async with Session(**kelvin_session_kwargs) as session:
        obj = await SchoolResource(session=session).get(name=school.name)
    compare_kelvin_obj_with_test_data(obj, **asdict(school))


@pytest.mark.asyncio
async def test_reload(
    compare_kelvin_obj_with_test_data, kelvin_session_kwargs, ldap_access, new_school,
):
    school = new_school(1)[0]
    display_name_old = school.display_name
    display_name_new = fake.text(max_nb_chars=50)

    async with Session(**kelvin_session_kwargs) as session:
        obj: School = await SchoolResource(session=session).get(name=school.name)
        assert obj.display_name == display_name_old
        await obj.reload()
        assert obj.display_name == display_name_old
        await ldap_access.modify(
            obj.dn, {"displayName": [(ldap3.MODIFY_REPLACE, [display_name_new])]}
        )
        await obj.reload()
        assert obj.display_name == display_name_new
        await ldap_access.modify(
            obj.dn, {"displayName": [(ldap3.MODIFY_REPLACE, [display_name_old])]}
        )
