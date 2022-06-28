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

from ucsschool.kelvin.client import InvalidRequest, NoObject, Session, WorkGroup, WorkGroupResource

fake = Faker()


API_VERSION = "v1"
URL_BASE = "https://{host}/ucsschool/kelvin"
URL_TOKEN = f"{URL_BASE}/token"
URL_WORKGROUP_RESOURCE = f"{URL_BASE}/{API_VERSION}/workgroups/"
URL_WORKGROUP_COLLECTION = f"{URL_WORKGROUP_RESOURCE}?school={{school}}"
URL_WORKGROUP_OBJECT = f"{URL_WORKGROUP_RESOURCE}{{school}}/{{name}}"
URL_SCHOOL_RESOURCE = f"{URL_BASE}/{API_VERSION}/schools/"
URL_SCHOOL_COLLECTION = URL_SCHOOL_RESOURCE
URL_SCHOOL_OBJECT = f"{URL_SCHOOL_COLLECTION}{{name}}"


@pytest.mark.asyncio
async def test_search_no_name_arg(
    compare_kelvin_obj_with_test_data,
    new_school,
    kelvin_session_kwargs,
    new_workgroup,
):
    school = new_school(1)[0]
    school_name = school.name
    sc1_dn, sc1_attr = await new_workgroup(school=school_name)
    sc2_dn, sc2_attr = await new_workgroup(school=school_name)

    async with Session(**kelvin_session_kwargs) as session:
        objs = [obj async for obj in WorkGroupResource(session=session).search(school=school_name)]

    assert objs, f"No WorkGroup in school {school!r} found."
    assert len(objs) >= 2
    assert sc1_dn in [sc.dn for sc in objs]
    assert sc2_dn in [sc.dn for sc in objs]
    for obj in objs:
        if obj.dn == sc1_dn:
            compare_kelvin_obj_with_test_data(obj, **sc1_attr)
        if obj.dn == sc2_dn:
            compare_kelvin_obj_with_test_data(obj, **sc2_attr)


@pytest.mark.asyncio
async def test_search_partial_name_arg(
    compare_kelvin_obj_with_test_data,
    new_school,
    kelvin_session_kwargs,
    new_workgroup,
):
    school = new_school(1)[0]
    school_name = school.name
    # don't use usual name starting with 'test.', as leftovers of previous
    # tests will also match 'test.*'
    name = f"{fake.first_name()}{fake.first_name()}"
    sc1_dn, sc1_attr = await new_workgroup(school=school_name, name=name)
    name_len = len(name)
    name_begin = name[: int(name_len / 2)]
    name_end = name[len(name_begin) :]

    async with Session(**kelvin_session_kwargs) as session:
        objs1 = [
            obj
            async for obj in WorkGroupResource(session=session).search(
                school=school_name, name=f"{name_begin}*"
            )
        ]
        objs2 = [
            obj
            async for obj in WorkGroupResource(session=session).search(
                school=school_name, name=f"*{name_end}"
            )
        ]
    assert objs1, f"No WorkGroup for school={school_name!r} and name='{name_begin}*' found."
    assert len(objs1) == 1
    assert sc1_dn == objs1[0].dn
    assert objs2, f"No WorkGroup for school={school_name!r} and name='*{name_end}' found."
    assert len(objs2) == 1
    assert sc1_dn == objs2[0].dn


@pytest.mark.asyncio
async def test_search_inexact_school(new_school, kelvin_session_kwargs):
    school = new_school(1)[0]
    school_name = school.name
    school_name_len = len(school_name)
    school_name_begin = school_name[: int(school_name_len / 2)]

    async with Session(**kelvin_session_kwargs) as session:
        with pytest.raises(InvalidRequest):
            assert [
                obj
                async for obj in WorkGroupResource(session=session).search(
                    school=f"{school_name_begin}*"
                )
            ]


@pytest.mark.asyncio
async def test_get_from_url(compare_kelvin_obj_with_test_data, kelvin_session_kwargs, new_workgroup):
    sc1_dn, sc1_attr = await new_workgroup()
    school = sc1_attr["school"]
    name = sc1_attr["name"]
    url = URL_WORKGROUP_OBJECT.format(host=kelvin_session_kwargs["host"], school=school, name=name)
    async with Session(**kelvin_session_kwargs) as session:
        obj = await WorkGroupResource(session=session).get_from_url(url)
    compare_kelvin_obj_with_test_data(obj, dn=sc1_dn, **sc1_attr)


@pytest.mark.asyncio
async def test_get_no_users(
    compare_kelvin_obj_with_test_data,
    kelvin_session_kwargs,
    new_school,
    new_workgroup,
):
    sc_dn, sc_attr = await new_workgroup()
    async with Session(**kelvin_session_kwargs) as session:
        obj = await WorkGroupResource(session=session).get(
            school=sc_attr["school"], name=sc_attr["name"]
        )
    compare_kelvin_obj_with_test_data(obj, dn=sc_dn, **sc_attr)


@pytest.mark.asyncio
async def test_get_with_users(
    compare_kelvin_obj_with_test_data,
    kelvin_session_kwargs,
    new_school,
    new_workgroup,
    new_school_user,
):
    user1 = await new_school_user()
    user2 = await new_school_user(school=user1.school)
    sc_dn, sc_attr = await new_workgroup(school=user1.school, users=[user1.name, user2.name])
    async with Session(**kelvin_session_kwargs) as session:
        obj = await WorkGroupResource(session=session).get(
            school=sc_attr["school"], name=sc_attr["name"]
        )
    assert set(obj.users) == {user1.name, user2.name}
    compare_kelvin_obj_with_test_data(obj, dn=sc_dn, **sc_attr)


@pytest.mark.parametrize("create_share", [True, False])
@pytest.mark.asyncio
async def test_create(
    compare_kelvin_obj_with_test_data,
    kelvin_session_kwargs,
    ldap_access,
    mail_domain,
    new_workgroup_test_obj,
    schedule_delete_obj,
    new_school_user,
    test_server_configuration,
    create_share,
):
    sc_data = new_workgroup_test_obj()
    user1 = await new_school_user(school=sc_data.school)
    user2 = await new_school_user(school=sc_data.school)
    sc_data.users = [user1.name, user2.name]
    sc_data.create_share = create_share
    async with Session(**kelvin_session_kwargs) as session:
        sc_kwargs = asdict(sc_data)
        sc_obj = WorkGroup(session=session, **sc_kwargs)
        schedule_delete_obj(object_type="workgroup", school=sc_data.school, name=sc_data.name)
        await sc_obj.save()
        print("Created new WorkGroup: {!r}".format(sc_obj.as_dict()))

    ldap_filter = f"(&(cn={sc_data.school}-{sc_data.name})(objectClass=ucsschoolGroup))"
    ldap_objs = await ldap_access.search(filter_s=ldap_filter)
    assert len(ldap_objs) == 1
    ldap_obj = ldap_objs[0]
    assert ldap_obj.entry_dn == sc_obj.dn
    assert ldap_obj["cn"].value == f"{sc_data.school}-{sc_data.name}"
    assert ldap_obj["ucsschoolRole"].value == f"workgroup:school:{sc_data.school}"
    assert ldap_obj["description"].value == sc_obj.description
    assert set(ldap_obj["uniqueMember"].value) == {user1.dn, user2.dn}
    share_ldap_filter = f"(&(cn={sc_data.school}-{sc_data.name})(objectClass=ucsschoolShare))"
    share_ldap_objs = await ldap_access.search(filter_s=share_ldap_filter)
    if create_share:
        assert len(share_ldap_objs) == 1
        share_ldap_obj = share_ldap_objs[0]
        assert share_ldap_obj["cn"].value == f"{sc_data.school}-{sc_data.name}"
    else:
        assert len(share_ldap_objs) == 0


@pytest.mark.asyncio
async def test_modify(
    compare_kelvin_obj_with_test_data,
    kelvin_session_kwargs,
    mail_domain,
    new_workgroup,
    new_workgroup_test_obj,
    test_server_configuration,
):
    sc1_dn, sc1_attr = await new_workgroup()
    new_data = asdict(new_workgroup_test_obj())
    school = sc1_attr["school"]
    name = sc1_attr["name"]
    async with Session(**kelvin_session_kwargs) as session:
        sc_resource = WorkGroupResource(session=session)
        obj: WorkGroup = await sc_resource.get(school=school, name=name)
        compare_kelvin_obj_with_test_data(obj, dn=sc1_dn, **sc1_attr)
        for k, v in new_data.items():
            if k not in ("school", "name", "dn", "url", "ucsschool_roles"):
                setattr(obj, k, v)
        new_obj: WorkGroup = await obj.save()
        assert new_obj is obj
        assert new_obj.as_dict() == obj.as_dict()
        # load fresh object
        fresh_obj: WorkGroup = await sc_resource.get(school=school, name=name)
        assert fresh_obj.as_dict() == new_obj.as_dict()
        compare_kelvin_obj_with_test_data(fresh_obj, **obj.as_dict())


@pytest.mark.asyncio
async def test_move_change_school(
    compare_kelvin_obj_with_test_data,
    new_school,
    kelvin_session_kwargs,
    new_workgroup,
    schedule_delete_obj,
):
    sc1_dn, sc1_attr = await new_workgroup()
    old_school = sc1_attr["school"]
    school1, school2 = new_school(2)
    ou1, ou2 = school1.name, school2.name
    name = sc1_attr["name"]
    new_school_ = ou1 if old_school == ou2 else ou2
    assert old_school != new_school_
    async with Session(**kelvin_session_kwargs) as session:
        sc_resource = WorkGroupResource(session=session)
        obj: WorkGroup = await sc_resource.get(school=old_school, name=name)
        assert obj.school == old_school
        compare_kelvin_obj_with_test_data(obj, dn=sc1_dn, **sc1_attr)
        obj.school = new_school_
        schedule_delete_obj(object_type="workgroup", school=new_school_, name=name)

        with pytest.raises(InvalidRequest) as exc_info:
            await obj.save()
        assert "Moving a workgroup to another school is not allowed" in exc_info.value.args[0]


@pytest.mark.asyncio
async def test_delete(kelvin_session_kwargs, new_workgroup):
    sc1_dn, sc1_attr = await new_workgroup()
    school = sc1_attr["school"]
    name = sc1_attr["name"]
    async with Session(**kelvin_session_kwargs) as session:
        obj = await WorkGroupResource(session=session).get(school=school, name=name)
        assert obj
        res = await obj.delete()
        assert res is None

    async with Session(**kelvin_session_kwargs) as session:
        with pytest.raises(NoObject):
            await WorkGroupResource(session=session).get(school=school, name=name)


@pytest.mark.asyncio
async def test_reload(
    compare_kelvin_obj_with_test_data,
    kelvin_session_kwargs,
    ldap_access,
    new_workgroup,
):
    sc1_dn, sc1_attr = await new_workgroup()
    school = sc1_attr["school"]
    name = sc1_attr["name"]
    description_old = sc1_attr["description"]
    description_new = fake.text(max_nb_chars=50)

    async with Session(**kelvin_session_kwargs) as session:
        obj: WorkGroup = await WorkGroupResource(session=session).get(school=school, name=name)
        assert obj.description == description_old
        await obj.reload()
        assert obj.description == description_old
        await ldap_access.modify(obj.dn, {"description": [(ldap3.MODIFY_REPLACE, [description_new])]})
        await obj.reload()
        assert obj.description == description_new
