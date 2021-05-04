# -*- coding: utf-8 -*-

"""Test connection and utility functions in `conftest` module."""

import datetime
import tempfile

import jwt
import pytest
from conftest import TestServerConnectionError, retrieve_kelvin_access_token
from faker import Faker
from ruamel.yaml import YAML

TOKEN_HASH_ALGORITHM = "HS256"  # nosec
fake = Faker()


@pytest.fixture
def connection_data():
    def _func():
        return {
            # host=IP -> ucs_ca_file_path() will not try download of CA
            "host": f"{fake.pyint(min_value=10, max_value=250)}."
            f"{fake.pyint(min_value=10, max_value=250)}."
            f"{fake.pyint(min_value=10, max_value=250)}."
            f"{fake.pyint(min_value=10, max_value=250)}",
            "username": fake.first_name(),
            "user_dn": f"uid={fake.first_name()},cn=users,dc={fake.first_name()}",
            "password": fake.first_name(),
        }

    return _func


def test_load_test_server_yaml(load_test_server_yaml, connection_data):
    server = connection_data()
    yaml = YAML(typ="safe")
    with tempfile.NamedTemporaryFile(mode="w") as fp:
        yaml.dump(server, fp)
        fp.flush()
        config = load_test_server_yaml(fp.name)
        assert server == {
            "host": config.host,
            "username": config.username,
            "user_dn": config.user_dn,
            "password": config.password,
        }


def test_save_test_server_yaml(save_test_server_yaml, connection_data):
    server = connection_data()
    yaml = YAML(typ="safe")
    with tempfile.NamedTemporaryFile() as fp:
        save_test_server_yaml(**server, path=fp.name)
        fp.flush()
        fp.seek(0)
        config = yaml.load(fp)
        assert config == server


def test_retrieve_kelvin_access_token_fail(kelvin_session_kwargs):
    with pytest.raises(TestServerConnectionError):
        retrieve_kelvin_access_token(
            host=kelvin_session_kwargs["host"],
            username=fake.user_name(),
            password=fake.password(),
            verify=False,
        )


def test_retrieve_kelvin_access_token_success(kelvin_session_kwargs):
    token = retrieve_kelvin_access_token(**kelvin_session_kwargs)
    payload = jwt.decode(token, algorithms=[TOKEN_HASH_ALGORITHM], options={"verify_signature": False})
    exp_payload_sub = {
        "username": kelvin_session_kwargs["username"],
        "kelvin_admin": True,
        "schools": [],
        "roles": [],
    }
    assert payload["sub"] == exp_payload_sub
    expiry = datetime.datetime.fromtimestamp(payload["exp"])
    assert expiry > datetime.datetime.now()
