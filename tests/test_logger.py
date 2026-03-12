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


async def search_school(new_school, kelvin_session_kwargs):
    new_school(1)

    async with Session(**kelvin_session_kwargs) as session:
        SchoolResource(session=session).search()


@pytest.mark.parametrize(
    "log_level",
    [
        pytest.param(logging.CRITICAL, id="log_CRITICAL"),
        pytest.param(logging.ERROR, id="log_ERROR"),
        pytest.param(logging.WARNING, id="log_WARNING"),
        pytest.param(logging.INFO, id="log_INFO"),
        pytest.param(logging.DEBUG, id="log_DEBUG"),
        pytest.param(logging.NOTSET, id="log_NOTSET"),
    ],
)
@pytest.mark.asyncio
async def test_log_mask_credentials(caplog, new_school, kelvin_session_kwargs, log_level):
    filters = {
        "Authorization": "'Authorization': '**********'",
        "username": f"'username': '{kelvin_session_kwargs['username']}'",
        "password": "'password': '**********'",
    }

    with caplog.at_level(log_level):
        await search_school(new_school, kelvin_session_kwargs)
        for line in caplog.text.split("\n"):
            for key, value in filters.items():
                if key in line:
                    assert value in line
                # exclude the username from masking
                if key in kelvin_session_kwargs and key != "username":
                    assert kelvin_session_kwargs[key] not in line
