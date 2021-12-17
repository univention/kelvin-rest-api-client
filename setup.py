#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup

with open("README.rst") as fp:
    readme = fp.read()
with open("HISTORY.rst") as fp:
    history = fp.read()
with open("requirements.txt") as fp:
    requirements = fp.read().splitlines()
with open("requirements_dev.txt") as fp:
    requirements_dev = fp.read().splitlines()
with open("requirements_test.txt") as fp:
    requirements_test = fp.read().splitlines()
with open("VERSION.txt") as fp:
    version = fp.read().strip()

setup(
    author="Daniel Troeder",
    author_email="troeder@univention.de",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Systems Administration :: Authentication/Directory :: LDAP",
    ],
    description="Python library to interact with the UCS@school Kelvin REST API.",
    license="GNU Affero General Public License v3",
    long_description=readme + "\n\n" + history,
    long_description_content_type="text/x-rst",
    include_package_data=True,
    keywords="Univention UCS UCS@school REST",
    name="kelvin-rest-api-client",
    packages=["ucsschool.kelvin.client"],
    install_requires=requirements,
    # setup_requires=["pytest-runner"],
    test_suite="tests",
    tests_require=requirements_dev + requirements_test,
    extras_require={"development": set(requirements + requirements_dev + requirements_test)},
    python_requires=">=3.7",
    url="https://github.com/univention/kelvin-rest-api-client",
    version=version,
)
