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

import pytest

from ucsschool.kelvin.client.role import Role
from ucsschool.kelvin.client.school import School
from ucsschool.kelvin.client.school_class import SchoolClass
from ucsschool.kelvin.client.user import User


@pytest.mark.parametrize("kelvin_object", [Role, School, SchoolClass, User])
def test_init_with_unknown_keyword_argument(kelvin_object):
    kelvin_object(
        name="test", school="test_school", schools=["test_school"], roles=[], notanargument=None
    )
