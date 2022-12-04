.PHONY: clean clean-test clean-pyc clean-build docs help
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os
import sys
import webbrowser

try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re
import sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python3 -c "$$BROWSER_PYSCRIPT"
SHELL := /bin/bash

UCS_IMG = docker.software-univention.de/ucs-master-amd64-joined-ucsschool-udm-rest-api-only:stable-4.4-8
UCS_CONTAINER = $(shell . docker/common.sh && echo "$$UCS_CONTAINER")
UCS_IMG_EXISTS = . docker/common.sh && docker_img_exists "$(UCS_IMG)"
UCS_IS_RUNNING = . docker/common.sh && docker_container_running "$(UCS_CONTAINER)"
START_UCS_CONTAINER = docker run --detach --name "$(UCS_CONTAINER)" --hostname=master -p 9080:80/tcp -p 9443:443/tcp -v /tmp/udm-rest-api-log:/var/log/univention --tmpfs /run --tmpfs /run/lock "$(UCS_IMG)"
UCS_CONTAINER_IP_CMD = . docker/common.sh && docker_container_ip $(UCS_CONTAINER)
GET_OPENAPI_SCHEMA_UDM = . docker/common.sh && get_openapi_schema "$(UCS_CONTAINER)"

KELVIN_IMG = docker.software-univention.de/ucsschool-kelvin-rest-api:1.8.0
KELVIN_CONTAINER = $(shell . docker/common.sh && echo "$$KELVIN_CONTAINER")
KELVIN_API_LOG_FILE = $(shell . docker/common.sh && echo "$$KELVIN_API_LOG_FILE")
KELVIN_IMG_EXISTS = . docker/common.sh && docker_img_exists "$(KELVIN_IMG)"
KELVIN_IS_RUNNING = . docker/common.sh && docker_container_running "$(KELVIN_CONTAINER)"
START_KELVIN_CONTAINER = docker/start_kelvin_container
KELVIN_CONTAINER_IP_CMD = . docker/common.sh && docker_container_ip $(KELVIN_CONTAINER)
GET_OPENAPI_SCHEMA_KELVIN = . docker/common.sh && get_openapi_schema "$(KELVIN_CONTAINER)"

help:
	@python3 -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr docs/_build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

setup_devel_env: ## setup development environment (virtualenv)
	@if [ -d venv ]; then \
		echo "Directory 'venv' exists."; \
	else \
		python3 -m venv venv; \
	fi; \
	. venv/bin/activate && python3 -m pip install -r requirements.txt -r requirements_dev.txt -r requirements_test.txt; \
	echo "==> Run '. venv/bin/activate' to activate virtual env."

format: ## format source code (using the current Python interpreter)
	pre-commit run -a --hook-stage manual isort-edit
	pre-commit run -a --hook-stage manual black-edit

lint-isort:
	pre-commit run -a isort

lint-black:
	pre-commit run -a black

lint-flake8:
	pre-commit run -a flake8

lint-bandit:
	pre-commit run -a bandit

lint-coverage: .coverage
	coverage report --show-missing --fail-under=90

lint: lint-isort lint-black lint-flake8 lint-bandit lint-coverage ## check style with the current Python interpreter

test: ## run tests with the current Python interpreter
	python3 -m pytest -l -v

test-all: ## run tests with every supported Python version using tox
	tox

.coverage: *.py docs/*.py ucsschool/kelvin/client/*.py tests/*.py
	coverage run --source tests,ucsschool -m pytest

coverage: .coverage ## check code coverage with the current Python interpreter
	coverage report --show-missing

coverage-html: coverage ## generate HTML coverage report
	coverage html
	$(BROWSER) htmlcov/index.html

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/modules.rst docs/ucsschool.rst docs/ucsschool.kelvin*.rst
	sphinx-apidoc -o docs/ -d 6 --doc-project modules --implicit-namespaces --separate ucsschool
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

docs-open: docs ## open generated Sphinx HTML doc in browser
	$(BROWSER) docs/_build/html/index.html

servedocs: docs ## compile the docs watching for changes
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

release: dist ## package and upload a release to pypi
	twine upload dist/*

release-test: dist ## package and upload a release to the pypi test site
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

dist: clean ## builds source and wheel package
	python3 setup.py sdist
	python3 setup.py bdist_wheel
	ls -l dist

install: clean ## install the package to the active Python's site-packages
	python3 -m pip install --editable .

download-docker-containers: ## download docker containers from Univention Docker registry (~3 GB)
	@if $(UCS_IMG_EXISTS); then \
		echo "Docker image '$(UCS_IMG)' exists."; \
	else \
	  	echo "Downloading Docker image '$(UCS_IMG)'..."; \
		docker pull $(UCS_IMG); \
	fi
	@if $(KELVIN_IMG_EXISTS); then \
		echo "Docker image '$(KELVIN_IMG)' exists."; \
	else \
	  	echo "Downloading Docker image '$(KELVIN_IMG)'..."; \
		docker pull $(KELVIN_IMG); \
	fi

start-docker-containers: download-docker-containers ## start docker containers (UDM and Kelvin REST API)
	@if $(UCS_IS_RUNNING); then \
		echo "Docker container '$(UCS_CONTAINER)' is running."; \
	else \
		echo "Starting UCS docker container..."; \
		echo "(from image $(UCS_IMG))"; \
		mkdir -p /tmp/udm-rest-api-log; \
		$(START_UCS_CONTAINER); \
	fi
	@echo "Waiting for UCS docker container to start..."
	@while ! ($(UCS_IS_RUNNING)); do echo -n "."; sleep 1; done
	@echo "Waiting for IP address of UCS container..."
	@while true; do export UCS_CONTAINER_IP=`$(UCS_CONTAINER_IP_CMD)`; [ -n "$$UCS_CONTAINER_IP" ] && break || (echo "."; sleep 1); done; \
	if [ -z "$$UCS_CONTAINER_IP" ]; then \
		echo "Cannot get IP of UCS container."; \
		exit 1; \
	fi; \
	echo -n "Waiting for UDM REST API"; \
	while ! ($(GET_OPENAPI_SCHEMA_UDM) --connect-timeout 1 >/dev/null); do echo -n "."; sleep 1; done; \
	echo; \
	echo "==> UDM REST API log file: /tmp/udm-rest-api-log/directory-manager-rest.log"; \
	echo "==> UDM REST API: http://$$UCS_CONTAINER_IP/univention/udm/"
	@if $(KELVIN_IS_RUNNING); then \
		echo "Docker container '$(KELVIN_CONTAINER)' is running."; \
	else \
		echo "Starting Kelvin docker container..."; \
		echo "(from image $(KELVIN_IMG))"; \
		$(START_KELVIN_CONTAINER); \
	fi
	@echo "Waiting for Kelvin docker container to start..."
	@while ! ($(KELVIN_IS_RUNNING)); do echo -n "."; sleep 1; done
	@echo "Waiting for IP address of Kelvin container..."
	@while true; do export KELVIN_CONTAINER_IP=`$(KELVIN_CONTAINER_IP_CMD)`; [ -n "$$KELVIN_CONTAINER_IP" ] && break || (echo "."; sleep 1); done; \
	if [ -z "$$KELVIN_CONTAINER_IP" ]; then \
		echo "Cannot get IP of Kelvin container."; \
		exit 1; \
	fi; \
	echo -n "Waiting for Kelvin API"; \
	while ! ($(GET_OPENAPI_SCHEMA_KELVIN) --connect-timeout 1 >/dev/null); do echo -n "."; sleep 1; done; \
	echo; \
	echo "Fixing log file permissions..."; \
	docker exec $(KELVIN_CONTAINER) sh -c "chmod 666 \"$(KELVIN_API_LOG_FILE)\"; chown \"$(shell id -u):$(shell id -g)\" \"$(KELVIN_API_LOG_FILE)\""; \
	echo "Setting up reverse proxy..."; \
	export UCS_CONTAINER_IP=`$(UCS_CONTAINER_IP_CMD)`; \
	docker exec udm_rest_only sh -c "echo \"ProxyPass /ucsschool/kelvin http://$$KELVIN_CONTAINER_IP:8911/ucsschool/kelvin retry=0\nProxyPassReverse /ucsschool/kelvin http://$$KELVIN_CONTAINER_IP:8911/ucsschool/kelvin\" > /etc/apache2/ucs-sites.conf.d/kelvin-api.conf; service apache2 reload"; \
	echo "==> UDM REST API log file: /tmp/udm-rest-api-log/directory-manager-rest.log"; \
	echo "==> UDM REST API: http://$$UCS_CONTAINER_IP/univention/udm/"; \
	echo "==> Kelvin API configs: /tmp/kelvin-api/configs/"; \
	echo "==> Kelvin API hooks: /tmp/kelvin-api/kelvin-hooks/"; \
	echo "==> Kelvin API log file: /tmp/kelvin-api/log/http.log"; \
	echo "==> Kelvin API: http://$$KELVIN_CONTAINER_IP:8911/ucsschool/kelvin/v1/docs"; \
	echo "==> Kelvin API: https://$$UCS_CONTAINER_IP/ucsschool/kelvin/v1/docs"

stop-and-remove-docker-containers: ## stop and remove docker containers (not images)
	docker stop --time 0 $(UCS_CONTAINER) || true
	docker stop --time 0 $(KELVIN_CONTAINER) || true
	docker rm $(UCS_CONTAINER) || true
	docker rm $(KELVIN_CONTAINER) || true
