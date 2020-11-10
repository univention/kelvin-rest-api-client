import base64
import copy
import logging
import os
import random
import string
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Tuple,
    Union,
)

import factory
import faker
import httpx
import pytest
import ruamel.yaml
import urllib3
from ldap3 import (
    ALL_ATTRIBUTES,
    AUTO_BIND_TLS_BEFORE_BIND,
    SIMPLE,
    SUBTREE,
    Connection,
    Entry,
    Server,
)
from ldap3.core.exceptions import LDAPBindError, LDAPExceptionError
from ldap3.utils.conv import escape_filter_chars
from urllib3.exceptions import InsecureRequestWarning

import docker
from docker.errors import NotFound as ContainerNotFound
from ucsschool.kelvin.client import InvalidRequest, KelvinObject, NoObject, ServerError

API_VERSION = "v1"

CA_CERT_PATH: Optional[Path] = None
TEST_SERVER_YAML_FILENAME = Path(__file__).parent / "test_server.yaml"
UCS_LDAP_PORT = 7389
URL_BASE = "https://{host}/ucsschool/kelvin"
URL_TOKEN = f"{URL_BASE}/token"
URL_CLASS_RESOURCE = f"{URL_BASE}/{API_VERSION}/classes/"
URL_CLASS_COLLECTION = f"{URL_CLASS_RESOURCE}?school={{school}}"
URL_CLASS_OBJECT = f"{URL_CLASS_RESOURCE}{{school}}/{{name}}"
URL_ROLE_RESOURCE = f"{URL_BASE}/{API_VERSION}/roles/"
URL_ROLE_COLLECTION = URL_ROLE_RESOURCE
URL_ROLE_OBJECT = f"{URL_ROLE_RESOURCE}{{name}}"
URL_SCHOOL_RESOURCE = f"{URL_BASE}/{API_VERSION}/schools/"
URL_SCHOOL_COLLECTION = URL_SCHOOL_RESOURCE
URL_SCHOOL_OBJECT = f"{URL_SCHOOL_COLLECTION}{{name}}"
URL_USER_RESOURCE = f"{URL_BASE}/{API_VERSION}/users/"
URL_USER_COLLECTION = URL_USER_RESOURCE
URL_USER_OBJECT = f"{URL_USER_COLLECTION}{{name}}"
UDM_DOCKER_CONTAINER_NAME = "udm_rest_only"
KELVIN_DOCKER_CONTAINER_NAME = "kelvin-api"

fake = faker.Faker()
logger = logging.getLogger(__name__)
_handler = logging.StreamHandler()
_handler.setLevel(logging.DEBUG)
logger.addHandler(_handler)
logger.setLevel(logging.DEBUG)
urllib3.disable_warnings(category=InsecureRequestWarning)


TestServerConfiguration = NamedTuple(
    "TestServerConfiguration",
    [
        ("host", str),
        ("username", str),
        ("user_dn", str),
        ("password", str),
        ("verify", Union[bool, str]),
    ],
)


class BadTestServerConfig(Exception):
    ...


class ContainerIpUnknown(Exception):
    ...


class NoTestServerConfig(Exception):
    ...


class TestServerConnectionError(Exception):
    __test__ = False

    def __init__(self, msg: str = None, status: int = None, reason: str = None):
        self.reason = reason
        self.status = status
        msg = msg or reason
        super().__init__(msg)


class LDAPAccess:
    _base_dn: str = None

    def __init__(self, bind_dn: str, bind_pw: str, host: str, port: int = 7389):
        self.bind_dn = bind_dn
        self.bind_pw = bind_pw
        self.host = host
        self.port = port
        self.server = Server(host=self.host, port=self.port, get_info="ALL")

    @property
    def _connection_kwargs(self) -> Dict[str, Any]:
        return {
            "server": self.server,
            "user": self.bind_dn,
            "password": self.bind_pw,
            "auto_bind": AUTO_BIND_TLS_BEFORE_BIND,
            "authentication": SIMPLE,
            "read_only": False,
        }

    @property
    def base_dn(self) -> str:
        if not self._base_dn:
            with Connection(**self._connection_kwargs) as conn:
                res = [
                    c for c in conn.server.info.naming_contexts if c != "cn=translog"
                ]
                self.__class__._base_dn = res[0]
        return self._base_dn

    async def search(
        self,
        filter_s: str,
        attributes: List[str] = ALL_ATTRIBUTES,
        base: str = None,
        scope=SUBTREE,
        user: str = None,
        password: str = None,
    ) -> List[Entry]:
        """
        Search an LDAP directory.

        The `Entry` object has an attribute `entry_dn`, which is the DN of the object.
        The other attributes can be accessed as if it were a dict, but accessing through
        a `.value` attribute (see example below).
        `entry_attributes_as_dict` returns the all attributes as a single dict::

            results = ldap_access.search("uid=Admin*")
            for result in results:
                dn             = result.entry_dn
                uid            = result["uid"].value
                full_name      = result["displayName"].value
                all_attributes = result.entry_attributes_as_dict

        :param str filter_s: LDAP filter, must be surrounded by parenthesis
        :param list(str) attributes: list of attributes to retrieve. Special cases:
            `ldap3.ALL_ATTRIBUTES` ('*', default), `ldap3.NO_ATTRIBUTES` ('1.1'),
            `ldap3.ALL_OPERATIONAL_ATTRIBUTES` ('+')
        :param str base: DN where the search should start
        :param str scope: one of `ldap3.BASE`, `ldap3.LEVEL`, `ldap3.SUBTREE` (default)
        :param str user: DN to instead of the one given in `__init__()`
        :param str password: password to instead of the one given in `__init__()`
        :return: a list of ldap3.abstract.entry.Entry objects
        :rtype: list(ldap3.abstract.entry.Entry)
        """
        base = base or self.base_dn
        connection_kwargs = self._connection_kwargs.copy()
        if user:
            connection_kwargs["user"] = user
        if password:
            connection_kwargs["password"] = password
        try:
            with Connection(**connection_kwargs) as conn:
                conn.search(
                    search_base=base,
                    search_filter=filter_s,
                    attributes=attributes,
                    search_scope=scope,
                )
        except LDAPBindError as exc:  # pragma: no cover
            logger.error(
                "When connecting (binding) to %r with bind_dn %r: %s",
                self.server.host,
                connection_kwargs["user"],
                exc,
            )
            raise
        except LDAPExceptionError as exc:  # pragma: no cover
            logger.error(
                "When searching on %r with bind_dn %r (filter_s=%r attributes=%r "
                "base=%r scope=%r): %s",
                self.server.host,
                connection_kwargs["user"],
                filter_s,
                attributes,
                base,
                scope,
                exc,
            )
            raise
        return conn.entries

    async def modify(
        self,
        dn: str,
        changes: Dict[str, List[Tuple[str, List[str]]]],
        controls: Iterable[Tuple[str, bool, Any]] = None,
    ) -> Dict[str, Any]:
        """
        This wrapper around `Connection.modify()`. See
        https://ldap3.readthedocs.io/en/latest/modify.html

        - changes is a dictionary in the form
            {'attribute1': change), 'attribute2': [change, change, ...], ...}
        - change is (operation, [value1, value2, ...])
        - operation is 0 (MODIFY_ADD), 1 (MODIFY_DELETE), 2 (MODIFY_REPLACE),
            3 (MODIFY_INCREMENT)

        Example::

            await ldap_access.modify(
                dn,
                {"description": [(ldap3.MODIFY_REPLACE, ["something new"])]}
            )

        :param str dn: DN of object to modify
        :param dict changes: dictionary with changes
        :param list controls: see https://ldap3.readthedocs.io/en/latest/connection.html#controls
        :return:
        """
        try:
            with Connection(**self._connection_kwargs) as conn:
                conn.modify(
                    dn=dn, changes=changes, controls=controls,
                )
        except LDAPBindError as exc:  # pragma: no cover
            logger.error(
                "When connecting (binding) to %r with bind_dn %r: %s",
                self.server.host,
                self.bind_dn,
                exc,
            )
            raise
        except LDAPExceptionError as exc:  # pragma: no cover
            logger.error(
                "When modifying on %r with bind_dn %r (changes=%r): %s",
                self.server.host,
                self.bind_dn,
                changes,
                exc,
            )
            raise
        return conn.result

    async def get_dn_of_user(self, username: str) -> str:
        filter_s = f"(uid={escape_filter_chars(username)})"
        results = await self.search(filter_s, attributes=[])
        if len(results) == 1:
            return results[0].entry_dn
        elif len(results) > 1:
            raise RuntimeError(
                f"More than 1 result when searching LDAP with filter {filter_s!r}: {results!r}."
            )
        else:
            return ""


def _get_ip_of_container(container_name: str) -> str:
    docker_client = docker.from_env()
    container = docker_client.containers.get(container_name)
    for k, v in container.attrs["NetworkSettings"]["Networks"].items():
        try:
            return v["IPAddress"]
        except KeyError:  # pragma: no cover
            pass
    raise ContainerIpUnknown(
        f"Could not get IP address from container {container_name!r}."
    )  # pragma: no cover


def _start_stopped_container(container_name: str):
    docker_client = docker.from_env()
    container = docker_client.containers.get(container_name)
    if container.status != "running":  # pragma: no cover
        logger.info(
            f"Found stopped Docker container {container_name!r}. "
            f"Trying to start and continue."
        )  # pragma: no cover
        container.start()


@pytest.fixture(scope="session")
def running_test_container():
    """
    :raises: ContainerIpUnknown
    :raises: ContainerNotFound
    """

    def _func() -> TestServerConfiguration:
        for container_name in (UDM_DOCKER_CONTAINER_NAME, KELVIN_DOCKER_CONTAINER_NAME):
            _start_stopped_container(container_name)
        ip = _get_ip_of_container(UDM_DOCKER_CONTAINER_NAME)
        server = TestServerConfiguration(
            host=ip,
            username="Administrator",
            user_dn="uid=Administrator,cn=users,dc=ucs-test,dc=intranet",
            password="univention",
            verify=False,
        )
        logger.info(
            f"Using Docker containers '{KELVIN_DOCKER_CONTAINER_NAME!r}' and "
            f"{UDM_DOCKER_CONTAINER_NAME}."
        )
        return server

    return _func


@pytest.fixture(scope="session")
def ldap_credentials(test_server_configuration) -> Dict[str, Any]:
    return {
        "bind_dn": test_server_configuration.user_dn,
        "bind_pw": test_server_configuration.password,
        "host": test_server_configuration.host,
        "port": UCS_LDAP_PORT,
    }


@pytest.fixture(scope="session")
def ldap_access(ldap_credentials):
    return LDAPAccess(**ldap_credentials)


@pytest.fixture(scope="session")
def base_dn(ldap_access):
    return ldap_access.base_dn


@pytest.fixture(scope="session")
def load_test_server_yaml(ucs_ca_file_path):
    def _func(
        path: Union[str, Path] = TEST_SERVER_YAML_FILENAME
    ) -> TestServerConfiguration:
        """
        :raises: FileNotFoundError
        :raises: TypeError
        """
        with open(path, "r") as fp:
            config = ruamel.yaml.load(fp, ruamel.yaml.RoundTripLoader)
        verify = ucs_ca_file_path(config["host"])
        return TestServerConfiguration(verify=verify, **config)

    return _func


@pytest.fixture(scope="session")
def save_test_server_yaml():
    """
    This is here only to make things simpler for developers. It's not actually
    needed in the tests.
    """

    def _func(
        host: str,
        username: str,
        user_dn: str,
        password: str,
        path: Union[str, Path] = TEST_SERVER_YAML_FILENAME,
    ) -> None:
        """
        :raises: OSError (PermissionError etc)
        """
        with open(path, "w") as fp:
            ruamel.yaml.dump(
                {
                    "host": host,
                    "username": username,
                    "user_dn": user_dn,
                    "password": password,
                },
                fp,
                ruamel.yaml.RoundTripDumper,
                indent=4,
            )

    return _func


def retrieve_kelvin_access_token(
    host: str, username: str, password: str, verify: bool
) -> str:
    try:
        resp = httpx.post(
            URL_TOKEN.format(host=host),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"username": username, "password": password},
            verify=verify,
        )
    except httpx.NetworkError as exc:
        raise TestServerConnectionError(
            f"Error retrieving token from Kelvin REST API: {exc}"
        )
    if resp.status_code != 200:
        raise TestServerConnectionError(  # pragma: no cover
            f"Error retrieving token from Kelvin REST API: [{resp.status_code}] {resp.reason_phrase}",
            reason=resp.reason_phrase,
            status=resp.status_code,
        )
    json_resp = resp.json()
    return json_resp["access_token"]


@pytest.fixture(scope="session")
def kelvin_token(test_server_configuration) -> str:
    return retrieve_kelvin_access_token(
        host=test_server_configuration.host,
        username=test_server_configuration.username,
        password=test_server_configuration.password,
        verify=test_server_configuration.verify,
    )


@pytest.fixture(scope="session")
def json_headers(kelvin_token) -> Dict[str, str]:
    return {
        "accept": "application/json",
        "Authorization": f"Bearer {kelvin_token}",
        "Content-Type": "application/json",
    }


def _test_a_server_configuration(server_config: TestServerConfiguration) -> None:
    logger.info("Testing auth with Kelvin REST API...")
    retrieve_kelvin_access_token(
        host=server_config.host,
        username=server_config.username,
        password=server_config.password,
        verify=server_config.verify,
    )
    logger.info("OK: auth with Kelvin REST API.")


@pytest.fixture(scope="session")  # noqa: C901
def test_server_configuration(
    load_test_server_yaml, running_test_container
) -> TestServerConfiguration:
    """
    Get data of server used to run tests.

    :raises: BadTestServerConfig
    :raises: NoTestServerConfig
    """
    logger.info(
        "Trying to load test server config from %r...", str(TEST_SERVER_YAML_FILENAME)
    )
    try:
        server_configuration = load_test_server_yaml()
        _test_a_server_configuration(server_configuration)
    except FileNotFoundError:  # pragma: no cover
        logger.error("File not found: %r.", str(TEST_SERVER_YAML_FILENAME))
    except TypeError as exc:  # pragma: no cover
        raise BadTestServerConfig(
            f"Error in '{TEST_SERVER_YAML_FILENAME!s}': {exc!s}"
        ) from exc
    except TestServerConnectionError as exc:  # pragma: no cover
        pytest.exit(
            f"Error connecting to test server using credentials "
            f"from '{TEST_SERVER_YAML_FILENAME!s}': [{exc.status}] {exc.reason}.\n"
            f"Maybe remove/rename {TEST_SERVER_YAML_FILENAME.name!r} and try "
            f"the Docker solution?"
        )
    else:
        return server_configuration

    logger.info(
        "Trying to use running Docker container %r...", KELVIN_DOCKER_CONTAINER_NAME
    )
    try:
        res = running_test_container()
        _test_a_server_configuration(res)
    except ContainerNotFound:
        logger.error("Container not found.")
    except ContainerIpUnknown as exc:
        raise BadTestServerConfig(str(exc)) from exc
    except TestServerConnectionError as exc:
        pytest.exit(
            f"Error connecting to test server using credentials for Docker "
            f"Docker container {KELVIN_DOCKER_CONTAINER_NAME!r}: [{exc.status}] {exc!s}"
        )
    else:
        return res

    raise NoTestServerConfig("No test server configuration found.")  # pragma: no cover


@pytest.fixture(scope="session")
def kelvin_session_kwargs(test_server_configuration) -> Dict[str, str]:
    return {
        "username": test_server_configuration.username,
        "password": test_server_configuration.password,
        "host": test_server_configuration.host,
        "verify": test_server_configuration.verify,
    }


@dataclass
class TestSchool:
    name: str
    display_name: str
    administrative_servers: List[str] = None
    class_share_file_server: str = None
    dc_name: str = None
    dc_name_administrative: str = None
    educational_servers: List[str] = None
    home_share_file_server: str = None
    ucsschool_roles: List[str] = None
    dn: str = None
    url: str = None


# class SchoolFactory(factory.Factory):
#     class Meta:
#         model = TestSchool
#
#     name = factory.LazyFunction(lambda: f"test{fake.user_name()}")
#     display_name = factory.Faker("text", max_nb_chars=50)
#     administrative_servers = factory.List([])
#     class_share_file_server = factory.LazyAttribute(lambda o: f"dc{o.name.lower()}-01")
#     dc_name = None
#     dc_name_administrative = None
#     educational_servers: List[str] = factory.LazyAttribute(
#         lambda o: o.class_share_file_server
#     )
#     home_share_file_server = factory.LazyAttribute(lambda o: o.class_share_file_server)
#     ucsschool_roles = factory.List([])
#     dn = ""
#     url = ""
#
#
# @pytest.fixture
# def new_school_test_obj() -> Callable[[], TestSchool]:
#     return lambda: SchoolFactory()


@pytest.fixture
def demoschool_data(
    json_headers, kelvin_session_kwargs, test_server_configuration
) -> List[Dict[str, Any]]:
    response = httpx.get(
        URL_SCHOOL_COLLECTION.format(host=test_server_configuration.host),
        headers=json_headers,
        verify=test_server_configuration.verify,
    )
    json_resp = response.json()
    if not {"DEMOSCHOOL", "DEMOSCHOOL2"}.issubset({obj["name"] for obj in json_resp}):
        raise AssertionError(  # pragma: no cover
            "To run the tests properly you need to have two schools named "
            "'DEMOSCHOOL' and 'DEMOSCHOOL2' at the moment! Execute *on the "
            "host*: "
            "/usr/share/ucs-school-import/scripts/create_ou DEMOSCHOOL; "
            "/usr/share/ucs-school-import/scripts/create_ou DEMOSCHOOL2"
        )
    return json_resp


@pytest.fixture
def new_school(base_dn, demoschool_data):
    """Create a new OU (not really, simply returns DEMOSCHOOL and DEMOSCHOOL2)."""

    demoschool1_data = [dd for dd in demoschool_data if dd["name"] == "DEMOSCHOOL"][0]
    demoschool2_data = [dd for dd in demoschool_data if dd["name"] == "DEMOSCHOOL2"][0]

    def _create_random_schools(amount: int) -> List[TestSchool]:
        assert amount <= 2, "At the moment only one or two schools can be requested."
        demo_school = TestSchool(**demoschool1_data)
        demo_school_2 = TestSchool(**demoschool2_data)
        schools = [demo_school, demo_school_2]
        random.shuffle(schools)
        return schools[:amount]

    return _create_random_schools


@dataclass
class TestSchoolClass:
    name: str
    school: str
    description: str = None
    users: List[str] = None
    ucsschool_roles: List[str] = None
    dn: str = None
    url: str = None


class SchoolClassFactory(factory.Factory):
    class Meta:
        model = TestSchoolClass

    name = factory.LazyFunction(lambda: f"test.{fake.user_name()}")
    school = "DEMOSCHOOL"
    description = factory.Faker("text", max_nb_chars=50)
    users = factory.List([])
    ucsschool_roles = factory.List([])
    dn = ""
    url = ""


@pytest.fixture
def new_school_class_test_obj() -> Callable[[], TestSchoolClass]:
    return lambda: SchoolClassFactory()


@pytest.fixture
async def new_school_class(
    new_school,
    kelvin_session_kwargs,
    ldap_access,
    new_school_class_test_obj,
    http_request,
    schedule_delete_obj,
):
    """Create a new school class"""

    host = kelvin_session_kwargs["host"]
    collection_url = URL_CLASS_RESOURCE.format(host=host)

    async def _func(**kwargs) -> Tuple[str, Dict[str, Any]]:
        if "name" not in kwargs:
            kwargs["name"] = f"test.{fake.first_name()}"
        name = kwargs["name"]
        if "school" not in kwargs:
            test_school = new_school(1)[0]
            kwargs["school"] = test_school.name
        school = kwargs["school"]
        sc_data = new_school_class_test_obj()
        for k, v in kwargs.items():
            setattr(sc_data, k, v)
        data = asdict(sc_data)
        del data["dn"]
        del data["ucsschool_roles"]
        del data["url"]
        json_data = copy.deepcopy(data)
        json_data["school"] = URL_SCHOOL_OBJECT.format(host=host, name=school)
        json_data["users"] = [
            URL_USER_OBJECT.format(host=host, name=user_name)
            for user_name in json_data["users"]
        ]
        schedule_delete_obj(object_type="class", school=school, name=name)
        obj = http_request("post", url=collection_url, json=json_data,)
        dn = obj["dn"]
        logger.info("Created new SchoolClass: %r", obj)

        dn0, _ = dn.split(",", 1)
        assert dn0 == f"cn={school}-{name}"
        ldap_objs = await ldap_access.search(
            filter_s=f"(&({dn0})(objectClass=ucsschoolGroup))"
        )
        assert len(ldap_objs) == 1
        ldap_obj = ldap_objs[0]
        assert ldap_obj.entry_dn == dn
        assert ldap_obj["cn"].value == f"{school}-{name}"
        assert "ucsschoolGroup" in ldap_obj["objectClass"]
        assert ldap_obj["ucsschoolRole"].value == f"school_class:school:{school}"

        return dn, data

    yield _func


@dataclass
class TestUserPasswordsHashes:
    user_password: List[str]
    samba_nt_password: str
    krb_5_key: List[str]
    krb5_key_version_number: int
    samba_pwd_last_set: int


@dataclass
class TestUser:
    name: str
    school: str
    schools: List[str]
    firstname: str
    lastname: str
    birthday: str = None
    disabled: bool = False
    email: str = None
    password: str = None
    record_uid: str = None
    roles: List[str] = None
    school_classes: Dict[str, List[str]] = None
    source_uid: str = None
    udm_properties: Dict[str, Any] = None
    ucsschool_roles: List[str] = None
    dn: str = None
    url: str = None
    kelvin_password_hashes: TestUserPasswordsHashes = None


class UserFactory(factory.Factory):
    class Meta:
        model = TestUser

    name = factory.Faker("user_name")
    school = ""
    schools = factory.List([])
    firstname = factory.Faker("first_name")
    lastname = factory.Faker("last_name")
    birthday = factory.LazyFunction(
        lambda: fake.date_of_birth(minimum_age=6, maximum_age=65).strftime("%Y-%m-%d")
    )
    disabled = False
    email = None
    password = factory.Faker("password", length=20)
    record_uid = factory.LazyAttribute(lambda o: o.name)
    roles = factory.List([])
    school_classes = factory.Dict({})
    source_uid = "TESTID"
    udm_properties = factory.Dict({})
    ucsschool_roles = factory.List([])
    dn = ""
    url = ""
    kelvin_password_hashes = None


@pytest.fixture  # noqa: C901
def new_user_test_obj(new_school):  # noqa: C901
    role_choices = ("staff", "student", "teacher", "teacher_and_staff")

    def _func(**kwargs) -> TestUser:
        if "roles" not in kwargs:
            try:
                role = kwargs.pop("role")
            except KeyError:
                role = random.choice(role_choices)
            if role in ("staff", "student", "teacher"):
                kwargs["roles"] = [role]
            elif role == "teacher_and_staff":
                kwargs["roles"] = ["staff", "teacher"]
            else:
                raise ValueError(  # pragma: no cover
                    f"Argument 'role' to new_user_test_obj() must be one of "
                    f"{', '.join(role_choices)}."
                )
        if "school" not in kwargs and "schools" not in kwargs:
            test_school = new_school(1)[0]
            kwargs["school"] = test_school.name
            kwargs["schools"] = [kwargs["school"]]
        if "school" not in kwargs:
            kwargs["school"] = sorted(kwargs["schools"])[0]  # pragma: no cover
        if "schools" not in kwargs:
            kwargs["schools"] = [kwargs["school"]]
        if "ucsschool_roles" not in kwargs:
            kwargs["ucsschool_roles"] = [
                f"{role}:school:{school}"
                for role in kwargs["roles"]
                for school in kwargs["schools"]
            ]
        user: TestUser = UserFactory(**kwargs)
        # ensure half names in test_user.test_search_inexact() are long enough
        if "firstname" not in kwargs and len(user.firstname) < 6:  # pragma: no cover
            user.firstname = f"{user.firstname}{fake.first_name()}"
        if "lastname" not in kwargs and len(user.lastname) < 6:  # pragma: no cover
            user.firstname = f"{user.lastname}{fake.last_name()}"
        user.name = user.name[:15]
        return user

    return _func


@pytest.fixture
def new_school_user(
    kelvin_session_kwargs,
    ldap_access,
    http_request,
    new_user_test_obj,
    schedule_delete_obj,
):
    """Create a new school user"""

    host = kelvin_session_kwargs["host"]
    collection_url = URL_USER_COLLECTION.format(host=host)

    async def _func(**kwargs) -> TestUser:  # Tuple[str, Dict[str, Any]]:
        user_obj: TestUser = new_user_test_obj(**kwargs)
        data = asdict(user_obj)
        del data["dn"]
        del data["ucsschool_roles"]
        del data["url"]
        json_data = copy.deepcopy(data)
        json_data["roles"] = [
            URL_ROLE_OBJECT.format(host=host, name=role) for role in json_data["roles"]
        ]
        json_data["school"] = URL_SCHOOL_OBJECT.format(
            host=host, name=json_data["school"]
        )
        json_data["schools"] = [
            URL_SCHOOL_OBJECT.format(host=host, name=school)
            for school in json_data["schools"]
        ]
        schedule_delete_obj(object_type="user", name=user_obj.name)
        obj = http_request("post", url=collection_url, json=json_data)
        dn = obj["dn"]
        logger.info("Created new User, API response: %r", obj)
        dn0, _ = dn.split(",", 1)
        assert dn0 == f"uid={user_obj.name}"
        ldap_objs = await ldap_access.search(
            filter_s=f"(&({dn0})(objectClass=ucsschoolType))"
        )
        assert len(ldap_objs) == 1
        ldap_obj = ldap_objs[0]
        assert ldap_obj.entry_dn == dn
        assert ldap_obj["uid"].value == user_obj.name
        assert "ucsschoolType" in ldap_obj["objectClass"]
        roles = [url.rsplit("/", 1)[-1] for url in user_obj.roles]
        ldap_val = ldap_obj["ucsschoolRole"].value
        if isinstance(ldap_val, str):
            ldap_val = {ldap_val}
        elif isinstance(ldap_val, Iterable):
            ldap_val = set(ldap_val)
        assert ldap_val == {
            f"{role}:school:{school.rsplit('/', 1)[-1]}"
            for role in roles
            for school in user_obj.schools
        }
        # role/school urls to names
        obj["school"] = obj["school"].rsplit("/", 1)[-1]
        for attr in ("roles", "schools"):
            obj[attr] = [url.rsplit("/", 1)[-1] for url in obj[attr]]
        obj["password"] = user_obj.password
        return TestUser(**obj)

    yield _func


@pytest.fixture
def schedule_delete_obj(http_request, json_headers, test_server_configuration):
    kelvin_objs: List[Tuple[str, Dict[str, Any]]] = []
    url_templates = {
        "class": URL_CLASS_OBJECT,
        "school": URL_SCHOOL_OBJECT,
        "user": URL_USER_OBJECT,
    }

    def _func(object_type: str, **search_args,) -> None:
        kelvin_objs.append((object_type, search_args))

    yield _func

    for kelvin_type, obj_search_args in kelvin_objs:
        logger.info("Deleting %r object with %r...", kelvin_type, obj_search_args)

        url_template = url_templates[kelvin_type]
        obj_url = url_template.format(
            host=test_server_configuration.host, **obj_search_args
        )
        try:
            http_request(
                "delete", url=obj_url, return_json=False,
            )
        except NoObject:
            logger.info(
                "Object does not exist (anymore): kelvin_type=%r obj_search_args=%r.",
                kelvin_type,
                obj_search_args,
            )
            continue


@pytest.fixture  # noqa: C901
def http_request(json_headers, kelvin_session_kwargs):  # noqa: C901
    def _func(
        http_method: str, url: str, return_json: bool = True, **kwargs
    ) -> Union[str, Dict[str, Any]]:
        if "headers" not in kwargs:
            kwargs["headers"] = json_headers
        if "verify" not in kwargs:
            kwargs["verify"] = kelvin_session_kwargs["verify"]
        if "timeout" not in kwargs:
            kwargs["timeout"] = 10.0
        req_method = getattr(httpx, http_method)
        response: httpx.Response = req_method(url, **kwargs)
        logger.debug(
            "%s %r (**%r) -> %r (%r)",
            http_method.upper(),
            url,
            kwargs,
            response.status_code,
            response.reason_phrase,
        )
        if 200 <= response.status_code <= 299:
            if return_json:
                return response.json()
            else:
                return response.text
        elif response.status_code == 404:
            raise NoObject(
                f"Object not found ({http_method.upper()} {url!r}).",
                reason=response.reason_phrase,
                status=response.status_code,
                url=url,
            )
        elif 400 <= response.status_code <= 499:  # pragma: no cover
            try:
                resp_json = response.json()
                if "detail" in resp_json:
                    resp_json = resp_json["detail"]
            except ValueError:
                resp_json = ""
            raise InvalidRequest(
                f"Kelvin REST API returned status {response.status_code}, reason "
                f"{response.reason_phrase!r}{f' ({resp_json})' if resp_json else ''} for "
                f"{http_method.upper()} {url!r}.",
                reason=response.reason_phrase,
                status=response.status_code,
                url=url,
            )
        else:
            raise ServerError(
                reason=response.reason_phrase, status=response.status_code, url=url
            )  # pragma: no cover

    return _func


@pytest.fixture(scope="session")
def ucs_ca_file_path():  # pragma: no cover
    global CA_CERT_PATH
    ucs_ca_ori_filename = "ucs-root-ca.crt"
    ip_chars = string.digits + "."

    def _func(host) -> Union[bool, str]:
        global CA_CERT_PATH
        if all(s in ip_chars for s in host):
            # need a hostname (not IP address) to verify SSL certificate
            return False
        resp = httpx.get(f"https://{host}/{ucs_ca_ori_filename}", verify=False)
        if resp.status_code != 200:
            return False
        CA_CERT_PATH = Path("/tmp/", f"{os.getpid()}_{host}_{ucs_ca_ori_filename}")
        with CA_CERT_PATH.open("w") as fp:
            fp.write(resp.text)
        return str(CA_CERT_PATH)

    yield _func
    if CA_CERT_PATH:
        CA_CERT_PATH.unlink()


@pytest.fixture
def compare_kelvin_obj_with_test_data(kelvin_session_kwargs):
    def _func(kelvin_obj: KelvinObject, **test_data):
        for test_data_attr, test_data_value in test_data.items():
            if test_data_attr == "password":
                # use check_password() to check this
                continue
            kelvin_obj_value = getattr(kelvin_obj, test_data_attr)
            if isinstance(test_data_value, list):
                assert set(kelvin_obj_value) == set(test_data_value)
            else:
                assert kelvin_obj_value == test_data_value

    return _func


@pytest.fixture
def check_password(ldap_access):
    async def _func(bind_dn: str, bind_pw: str) -> None:
        search_kwargs = {
            "filter_s": f"({bind_dn.split(',')[0]})",
            "attributes": ["uid"],
            "user": bind_dn,
            "password": bind_pw,
        }
        logger.info("Testing login (making LDAP search) with: %r", search_kwargs)
        try:
            results = await ldap_access.search(**search_kwargs)
        except LDAPBindError as exc:
            raise AssertionError(
                f"Login fail with user={bind_dn!r} and password={bind_pw!r}: {exc!s}"
            ) from exc
        logger.info("Login success.")
        assert len(results) == 1
        result = results[0]
        expected_uid = bind_dn.split(",")[0].split("=")[1]
        assert expected_uid == result["uid"].value

    return _func


@pytest.fixture
def password_hash(check_password, ldap_access, new_school_user):
    async def _func(password: str = None) -> Tuple[str, TestUserPasswordsHashes]:
        password = password or fake.password(length=20)
        user = await new_school_user(password=password)
        await check_password(user.dn, user.password)
        # get hashes of user
        filter_s = f"(uid={user.name})"
        attributes = [
            "userPassword",
            "sambaNTPassword",
            "krb5Key",
            "krb5KeyVersionNumber",
            "sambaPwdLastSet",
        ]
        ldap_results = await ldap_access.search(
            filter_s=filter_s, attributes=attributes
        )
        if len(ldap_results) == 1:
            ldap_result = ldap_results[0]
        else:
            raise RuntimeError(
                f"More than 1 result when searching LDAP with filter {filter_s!r}: {ldap_results!r}."
            )
        user_password = ldap_result["userPassword"].value
        if not isinstance(user_password, list):
            user_password = [user_password]
        user_password = [pw.decode("ascii") for pw in user_password]
        krb_5_key = [
            base64.b64encode(v).decode("ascii") for v in ldap_result["krb5Key"].value
        ]
        return (
            password,
            TestUserPasswordsHashes(
                user_password=user_password,
                samba_nt_password=ldap_result["sambaNTPassword"].value,
                krb_5_key=krb_5_key,
                krb5_key_version_number=ldap_result["krb5KeyVersionNumber"].value,
                samba_pwd_last_set=ldap_result["sambaPwdLastSet"].value,
            ),
        )

    return _func
