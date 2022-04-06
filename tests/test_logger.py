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

import logging

import pytest
from faker import Faker

from ucsschool.kelvin.client import SchoolResource, Session

fake = Faker()
logger = logging.getLogger(__name__)
filters = {'Authorization': "'Authorization': '**********'", 'username': "'username': '**********'",
           'password': "'password': '**********'", }


async def get_school_object(new_school, kelvin_session_kwargs):
    school1, school2 = new_school(2)

    async with Session(**kelvin_session_kwargs) as session:
        objs = [obj async for obj in SchoolResource(session=session).search()]
        return objs


@pytest.mark.asyncio
async def test_log_level_critical(caplog, new_school, kelvin_session_kwargs):

    with caplog.at_level(logging.CRITICAL):
        await get_school_object(new_school, kelvin_session_kwargs)
        for line in caplog.text.split("\n"):
            for key in filters:
                if key in line:
                    assert filters[key] in line
                if key in kelvin_session_kwargs:
                    assert kelvin_session_kwargs[key] not in line


@pytest.mark.asyncio
async def test_log_level_error(caplog, new_school, kelvin_session_kwargs):

    with caplog.at_level(logging.ERROR):
        await get_school_object(new_school, kelvin_session_kwargs)
        for line in caplog.text.split("\n"):
            for key in filters:
                if key in line:
                    assert filters[key] in line
                if key in kelvin_session_kwargs:
                    assert kelvin_session_kwargs[key] not in line


@pytest.mark.asyncio
async def test_log_level_warning(caplog, new_school, kelvin_session_kwargs):

    with caplog.at_level(logging.WARNING):
        await get_school_object(new_school, kelvin_session_kwargs)
        for line in caplog.text.split("\n"):
            for key in filters:
                if key in line:
                    assert filters[key] in line
                if key in kelvin_session_kwargs:
                    assert kelvin_session_kwargs[key] not in line


@pytest.mark.asyncio
async def test_log_level_info(caplog, new_school, kelvin_session_kwargs):

    with caplog.at_level(logging.INFO):
        await get_school_object(new_school, kelvin_session_kwargs)
        for line in caplog.text.split("\n"):
            for key in filters:
                if key in line:
                    assert filters[key] in line
                if key in kelvin_session_kwargs:
                    assert kelvin_session_kwargs[key] not in line


@pytest.mark.asyncio
async def test_log_level_debug(caplog, new_school, kelvin_session_kwargs):

    with caplog.at_level(logging.DEBUG):
        await get_school_object(new_school, kelvin_session_kwargs)
        for line in caplog.text.split("\n"):
            for key in filters:
                if key in line:
                    assert filters[key] in line
                if key in kelvin_session_kwargs:
                    assert kelvin_session_kwargs[key] not in line


@pytest.mark.asyncio
async def test_log_level_notset(caplog, new_school, kelvin_session_kwargs):

    with caplog.at_level(logging.NOTSET):
        await get_school_object(new_school, kelvin_session_kwargs)
        for line in caplog.text.split("\n"):
            for key in filters:
                if key in line:
                    assert filters[key] in line
                if key in kelvin_session_kwargs:
                    assert kelvin_session_kwargs[key] not in line
