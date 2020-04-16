# -*- coding: utf-8 -*-

"""Test connection and utility functions in `conftest` module."""

import datetime
import tempfile

import jwt
import pytest
import ruamel.yaml
from conftest import TestServerConnectionError, retrieve_kelvin_access_token
from faker import Faker

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
    with tempfile.NamedTemporaryFile(mode="w") as fp:
        ruamel.yaml.dump(server, fp, ruamel.yaml.SafeDumper)
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
    with tempfile.NamedTemporaryFile() as fp:
        save_test_server_yaml(**server, path=fp.name)
        fp.flush()
        fp.seek(0)
        config = ruamel.yaml.load(fp, ruamel.yaml.Loader)
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
    payload = jwt.decode(token, verify=False)
    assert payload["sub"] == kelvin_session_kwargs["username"]
    expiry = datetime.datetime.fromtimestamp(payload["exp"])
    assert expiry > datetime.datetime.now()
