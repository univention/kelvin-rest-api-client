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

import time
from dataclasses import asdict

import ldap3
import pytest
from faker import Faker

from ucsschool.kelvin.client import (
    InvalidRequest,
    NoObject,
    PasswordsHashes,
    Session,
    User,
    UserResource,
)

fake = Faker()


API_VERSION = "v1"
URL_BASE = "https://{host}/ucsschool/kelvin"
URL_TOKEN = f"{URL_BASE}/token"
URL_SCHOOL_RESOURCE = f"{URL_BASE}/{API_VERSION}/schools/"
URL_SCHOOL_COLLECTION = URL_SCHOOL_RESOURCE
URL_SCHOOL_OBJECT = f"{URL_SCHOOL_RESOURCE}{{name}}"
URL_USER_RESOURCE = f"{URL_BASE}/{API_VERSION}/users/"
URL_USER_COLLECTION = URL_USER_RESOURCE
URL_USER_OBJECT = f"{URL_USER_COLLECTION}{{name}}"


@pytest.mark.asyncio
async def test_search_no_name_arg(
    compare_kelvin_obj_with_test_data,
    new_school,
    kelvin_session_kwargs,
    new_school_user,
):
    school = new_school(1)[0]
    user1 = await new_school_user(school=school.name)
    user2 = await new_school_user(school=school.name)

    async with Session(**kelvin_session_kwargs) as session:
        objs = [obj async for obj in UserResource(session=session).search(school=school.name)]

    assert objs, f"No Users in school {school.name!r} found."
    assert len(objs) >= 2
    assert user1.dn in [obj.dn for obj in objs]
    assert user2.dn in [obj.dn for obj in objs]
    for obj in objs:
        if obj.dn == user1.dn:
            compare_kelvin_obj_with_test_data(obj, **asdict(user1))
        elif obj.dn == user2.dn:
            compare_kelvin_obj_with_test_data(obj, **asdict(user2))


@pytest.mark.asyncio
async def test_search_partial_name_arg(
    compare_kelvin_obj_with_test_data,
    new_school,
    kelvin_session_kwargs,
    new_school_user,
):
    school = new_school(1)[0]
    user = await new_school_user(school=school.name)
    name = user.name
    name_len = len(name)
    name_begin = name[: int(name_len / 2)]
    name_end = name[len(name_begin) :]

    async with Session(**kelvin_session_kwargs) as session:
        objs1 = [
            obj
            async for obj in UserResource(session=session).search(
                school=school.name, name=f"{name_begin}*"
            )
        ]
        objs2 = [
            obj
            async for obj in UserResource(session=session).search(
                school=school.name, name=f"*{name_end}"
            )
        ]
    assert objs1, f"No User for school={school.name!r} and name='{name_begin}*' found."
    assert len(objs1) == 1
    assert user.dn == objs1[0].dn
    assert objs2, f"No User for school={school.name!r} and name='*{name_end}' found."
    assert len(objs2) == 1
    assert user.dn == objs2[0].dn


@pytest.mark.asyncio
async def test_search_inexact_school(new_school, kelvin_session_kwargs):
    school = new_school(1)[0]
    school_name = school.name
    school_name_len = len(school_name)
    school_name_begin = school_name[: int(school_name_len / 2)]

    async with Session(**kelvin_session_kwargs) as session:
        with pytest.raises(InvalidRequest):
            assert [
                obj async for obj in UserResource(session=session).search(school=f"{school_name_begin}*")
            ]


@pytest.mark.asyncio
@pytest.mark.parametrize("attr", ["birthday", "disabled", "expiration_date", "roles"])
async def test_search_exact(
    compare_kelvin_obj_with_test_data,
    new_school,
    kelvin_session_kwargs,
    new_school_user,
    attr,
):
    user = await new_school_user()
    value = getattr(user, attr)

    async with Session(**kelvin_session_kwargs) as session:
        objs = [
            obj
            async for obj in UserResource(session=session).search(school=user.school, **{attr: value})
        ]
    assert objs, f"No User for school={user.school!r} and {attr!r}={value!r} found."
    if attr in ("roles", "disabled"):
        assert len(objs) >= 1
        assert user.dn in [o.dn for o in objs]
    else:
        assert len(objs) == 1
        assert user.dn == objs[0].dn


@pytest.mark.asyncio
@pytest.mark.parametrize("attr", ["firstname", "lastname", "record_uid", "source_uid"])
async def test_search_inexact(
    compare_kelvin_obj_with_test_data,
    new_school,
    kelvin_session_kwargs,
    new_school_user,
    attr,
):
    user = await new_school_user()
    value = getattr(user, attr)
    value_len = len(value)
    value_begin = value[: int(value_len / 2)]
    value_end = value[len(value_begin) :]

    async with Session(**kelvin_session_kwargs) as session:
        objs1 = [
            obj
            async for obj in UserResource(session=session).search(
                school=user.school, **{attr: f"{value_begin}*"}
            )
        ]
        objs2 = [
            obj
            async for obj in UserResource(session=session).search(
                school=user.school, **{attr: f"*{value_end}"}
            )
        ]
    assert objs1, f"No User for school={user.school!r} and {attr!r}='{value_begin}*' found."
    assert objs2, f"No User for school={user.school!r} and {attr!r}='*{value_end}' found."
    if attr == "source_uid":
        assert len(objs1) >= 1
        assert user.dn in [o.dn for o in objs1]
        assert len(objs2) >= 1
        assert user.dn in [o.dn for o in objs2]
    else:
        assert len(objs1) == 1
        assert user.dn == objs1[0].dn
        assert len(objs2) == 1
        assert user.dn == objs2[0].dn


@pytest.mark.asyncio
async def test_get_from_url(compare_kelvin_obj_with_test_data, kelvin_session_kwargs, new_school_user):
    user = await new_school_user()
    url = URL_USER_OBJECT.format(host=kelvin_session_kwargs["host"], school=user.school, name=user.name)
    async with Session(**kelvin_session_kwargs) as session:
        obj: User = await UserResource(session=session).get_from_url(url)
    compare_kelvin_obj_with_test_data(obj, **asdict(user))


@pytest.mark.asyncio
async def test_get(compare_kelvin_obj_with_test_data, kelvin_session_kwargs, new_school_user):
    user = await new_school_user()
    async with Session(**kelvin_session_kwargs) as session:
        obj = await UserResource(session=session).get(name=user.name)
    compare_kelvin_obj_with_test_data(obj, **asdict(user))


@pytest.mark.asyncio
async def test_create(
    check_password,
    kelvin_session_kwargs,
    ldap_access,
    new_user_test_obj,
    schedule_delete_obj,
    new_workgroup,
):
    user_data = new_user_test_obj()
    wg_dn, wg_attr = await new_workgroup(school=user_data.school, users=[])
    user_data.workgroups = {wg_attr["school"]: [wg_attr["name"]]}

    async with Session(**kelvin_session_kwargs) as session:
        user_obj = User(session=session, **asdict(user_data))
        user_obj.udm_properties = {"title": fake.first_name()}
        schedule_delete_obj(object_type="user", name=user_data.name)
        await user_obj.save()
        print("Created new User: {!r}".format(user_obj.as_dict()))

    assert f"ou={user_data.school}" in user_obj.dn
    ldap_filter = f"(&(uid={user_obj.name})(objectClass=ucsschoolType))"
    ldap_objs = await ldap_access.search(filter_s=ldap_filter)
    assert len(ldap_objs) == 1
    ldap_obj = ldap_objs[0]
    assert ldap_obj.entry_dn == user_obj.dn
    assert ldap_obj["uid"].value == user_obj.name
    assert ldap_obj["givenName"].value == user_obj.firstname
    assert ldap_obj["sn"].value == user_obj.lastname
    ldap_val_schools = ldap_obj["ucsschoolSchool"].value
    if isinstance(ldap_val_schools, str):
        ldap_val_schools = [ldap_val_schools]
    assert set(ldap_val_schools) == set(user_obj.schools)
    assert ldap_obj["univentionBirthday"].value == user_obj.birthday.strftime("%Y-%m-%d")
    if user_obj.disabled is True:
        exp_shadow_expire = "1"
    elif user_obj.expiration_date:
        exp_shadow_expire = int(time.mktime(user_obj.expiration_date.timetuple()) / 3600 / 24 + 1)
    else:
        exp_shadow_expire = "0"
    assert ldap_obj["shadowExpire"].value == exp_shadow_expire
    ldap_val_ucsschool_role = ldap_obj["ucsschoolRole"].value
    if isinstance(ldap_val_ucsschool_role, str):
        ldap_val_ucsschool_role = [ldap_val_ucsschool_role]
    assert set(ldap_val_ucsschool_role) == set(user_data.ucsschool_roles)
    assert ldap_obj["ucsschoolRecordUID"] == user_data.record_uid
    assert ldap_obj["ucsschoolSourceUID"] == user_data.source_uid
    await check_password(ldap_obj.entry_dn, user_data.password)
    assert ldap_obj["title"] == user_obj.udm_properties["title"]
    # check that user was added to workgroup
    wg_ldap_filter = f"(&(cn={wg_attr['school']}-{wg_attr['name']})(objectClass=ucsschoolGroup))"
    wg_ldap_objs = await ldap_access.search(filter_s=wg_ldap_filter)
    assert len(wg_ldap_objs) == 1
    wg_ldap_obj = wg_ldap_objs[0]
    assert user_obj.dn in wg_ldap_obj.uniqueMember, wg_ldap_obj


@pytest.mark.asyncio
@pytest.mark.parametrize("attr_value", [None, "", "omit"], ids=lambda x: repr(x))
@pytest.mark.parametrize(
    "attr_key,expected_message",
    [("name", "No username was created"), ("record_uid", "source_uid or record_uid are not set")],
    ids=lambda x: repr(x),
)
async def test_create_user_raises_invalid_request_for_missing_username_and_record_uid(
    kelvin_session_kwargs,
    ldap_access,
    new_user_test_obj,
    attr_value,
    attr_key,
    expected_message,
):
    """
    Passing None, "" or leaving out the attribute should lead to an InvalidRequest on the
    server side. We have tests for the Kelvin server (test_create_without_username)
    which uses custom kelvin.json files.
    This test assumes that there is no schema defined on the Kelvin server.
    """
    user_data = new_user_test_obj()
    user_data_dict = asdict(user_data)
    user_data_dict[attr_key] = attr_value
    if attr_value == "omit":
        user_data_dict.pop(attr_key)
    async with Session(**kelvin_session_kwargs) as session:
        user_obj = User(session=session, **user_data_dict)
        with pytest.raises(InvalidRequest) as exc:
            await user_obj.save()
            assert expected_message in exc.value


@pytest.mark.asyncio
@pytest.mark.parametrize("attr_value", [None, "", "omit"], ids=lambda x: repr(x))
async def test_create_user_email_allows_empty_non_required_attrs(
    kelvin_session_kwargs,
    ldap_access,
    new_user_test_obj,
    attr_value,
    schedule_delete_obj,
):
    """
    passing None, "" or leaving out the email attribute should __not__ lead to an InvalidRequest on the
    server side.
    This test assumes that there is no schema defined on the Kelvin server.
    """
    attr_key = "email"
    user_data = new_user_test_obj()
    user_data_dict = asdict(user_data)
    user_data_dict[attr_key] = attr_value
    if attr_value == "omit":
        user_data_dict.pop(attr_key)
    async with Session(**kelvin_session_kwargs) as session:
        user_obj = User(session=session, **user_data_dict)
        schedule_delete_obj(object_type="user", name=user_data.name)
        user = await user_obj.save()
        assert user.email is None


@pytest.mark.asyncio
async def test_create_with_password_hashes(
    check_password,
    kelvin_session_kwargs,
    password_hash,
    new_user_test_obj,
    schedule_delete_obj,
):
    user_data = new_user_test_obj()
    password, password_hashes = await password_hash()
    assert user_data.password != password
    user_data.password = None
    user_data.kelvin_password_hashes = PasswordsHashes(**asdict(password_hashes))

    async with Session(**kelvin_session_kwargs) as session:
        user_obj = User(session=session, **asdict(user_data))
        schedule_delete_obj(object_type="user", name=user_data.name)
        await user_obj.save()
        print("Created new User: {!r}".format(user_obj.as_dict()))
    await check_password(user_obj.dn, password)


@pytest.mark.asyncio
async def test_modify(
    check_password,
    compare_kelvin_obj_with_test_data,
    kelvin_session_kwargs,
    new_school_user,
    new_user_test_obj,
    new_workgroup,
    ldap_access,
):
    user = await new_school_user()
    wg_dn, wg_attr = await new_workgroup(school=user.school, users=[])
    new_data = asdict(
        new_user_test_obj(
            name=user.name,
            roles=user.roles,
            school=user.school,
            schools=user.schools,
            ucsschool_roles=user.ucsschool_roles,
            udm_properties={"title": fake.first_name()},
            workgroups={wg_attr["school"]: [wg_attr["name"]]},
        )
    )
    async with Session(**kelvin_session_kwargs) as session:
        user_resource = UserResource(session=session)
        obj: User = await user_resource.get(school=user.school, name=user.name)
        compare_kelvin_obj_with_test_data(obj, **asdict(user))
        await check_password(obj.dn, user.password)
        for k, v in new_data.items():
            if k not in ("dn", "url"):
                setattr(obj, k, v)
        new_obj: User = await obj.save()
        assert new_obj is obj
        compare_kelvin_obj_with_test_data(new_obj, **obj.as_dict())
        # load fresh object
        fresh_obj: User = await user_resource.get(school=user.school, name=user.name)
        compare_kelvin_obj_with_test_data(fresh_obj, **new_obj.as_dict())
        compare_kelvin_obj_with_test_data(fresh_obj, **obj.as_dict())
        await check_password(fresh_obj.dn, new_data["password"])
        # check that user was added to workgroup
        wg_ldap_filter = f"(&(cn={wg_attr['school']}-{wg_attr['name']})(objectClass=ucsschoolGroup))"
        wg_ldap_objs = await ldap_access.search(filter_s=wg_ldap_filter)
        assert len(wg_ldap_objs) == 1
        wg_ldap_obj = wg_ldap_objs[0]
        assert obj.dn in wg_ldap_obj.uniqueMember


@pytest.mark.asyncio
async def test_modify_password_hashes(
    check_password,
    kelvin_session_kwargs,
    password_hash,
    new_school_user,
):
    user = await new_school_user()
    password, password_hashes = await password_hash()
    assert user.password != password
    async with Session(**kelvin_session_kwargs) as session:
        user_resource = UserResource(session=session)
        obj: User = await user_resource.get(school=user.school, name=user.name)
        await check_password(obj.dn, user.password)
        obj.password = None
        obj.kelvin_password_hashes = PasswordsHashes(**asdict(password_hashes))
        await obj.save()
        fresh_obj: User = await user_resource.get(school=user.school, name=user.name)
        await check_password(fresh_obj.dn, password)


@pytest.mark.asyncio
async def test_move_change_name(
    compare_kelvin_obj_with_test_data,
    kelvin_session_kwargs,
    new_school_user,
    schedule_delete_obj,
):
    user = await new_school_user()
    old_name = user.name
    new_name = fake.first_name()
    assert old_name != new_name
    async with Session(**kelvin_session_kwargs) as session:
        user_resource = UserResource(session=session)
        obj: User = await user_resource.get(school=user.school, name=old_name)
        assert obj.name == old_name
        compare_kelvin_obj_with_test_data(obj, **asdict(user))
        obj.name = new_name
        old_url = obj.url
        schedule_delete_obj(object_type="user", name=new_name)

        new_obj: User = await obj.save()
        assert new_obj is obj
        assert new_obj.name == new_name
        assert f"uid={new_name}" in new_obj.dn
        assert new_obj.url != old_url
        # load fresh object
        fresh_obj: User = await user_resource.get(school=user.school, name=new_name)
        assert fresh_obj.name == new_name
        assert fresh_obj.url != old_url
        compare_kelvin_obj_with_test_data(fresh_obj, **new_obj.as_dict())


@pytest.mark.asyncio
async def test_move_change_school(
    compare_kelvin_obj_with_test_data,
    new_school,
    kelvin_session_kwargs,
    new_school_user,
    schedule_delete_obj,
):
    user = await new_school_user()
    old_school = user.school
    school1, school2 = new_school(2)
    ou1, ou2 = school1.name, school2.name
    new_school_ = ou1 if old_school == ou2 else ou2
    assert old_school != new_school_
    async with Session(**kelvin_session_kwargs) as session:
        user_resource = UserResource(session=session)
        obj: User = await user_resource.get(school=old_school, name=user.name)
        assert obj.school == old_school
        compare_kelvin_obj_with_test_data(obj, **asdict(user))
        obj.school = new_school_
        obj.schools = [new_school_]
        old_url = obj.url
        schedule_delete_obj(object_type="user", name=user.name)

        new_obj: User = await obj.save()
        assert new_obj is obj
        assert new_obj.name == user.name
        assert new_obj.school == new_school_
        assert f"ou={new_school_}" in new_obj.dn
        assert new_obj.url == old_url
        # load fresh object
        fresh_obj: User = await user_resource.get(school=new_school_, name=user.name)
        assert fresh_obj.name == user.name
        assert fresh_obj.school == new_school_
        assert fresh_obj.schools == [new_school_]
        assert fresh_obj.url == old_url
        compare_kelvin_obj_with_test_data(fresh_obj, **new_obj.as_dict())


@pytest.mark.asyncio
async def test_delete(kelvin_session_kwargs, new_school_user):
    user = await new_school_user()
    async with Session(**kelvin_session_kwargs) as session:
        obj = await UserResource(session=session).get(school=user.school, name=user.name)
        assert obj
        res = await obj.delete()
        assert res is None

    async with Session(**kelvin_session_kwargs) as session:
        with pytest.raises(NoObject):
            await UserResource(session=session).get(school=user.school, name=user.name)


@pytest.mark.asyncio
async def test_reload(
    kelvin_session_kwargs,
    ldap_access,
    new_school_user,
):
    user = await new_school_user()
    first_name_old = user.firstname
    first_name_new = fake.first_name()

    async with Session(**kelvin_session_kwargs) as session:
        obj: User = await UserResource(session=session).get(school=user.school, name=user.name)
        assert obj.firstname == first_name_old
        await obj.reload()
        assert obj.firstname == first_name_old
        await ldap_access.modify(obj.dn, {"givenName": [(ldap3.MODIFY_REPLACE, [first_name_new])]})
        await obj.reload()
        assert obj.firstname == first_name_new
