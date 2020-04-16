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

BROWSER := python -c "$$BROWSER_PYSCRIPT"


help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

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
		python3.8 -m venv venv; \
	fi; \
	. venv/bin/activate && python3 -m pip install -r requirements.txt -r requirements_dev.txt -r requirements_test.txt; \
	echo "==> Run '. venv/bin/activate' to activate virtual env."

format: ## format source code (using the current Python interpreter)
	isort --apply --recursive docs setup.py tests ucsschool
	black --target-version py37 setup.py docs tests ucsschool

lint-isort:
	isort --check-only --recursive docs setup.py tests ucsschool

lint-black:
	black --check --target-version py37 docs setup.py tests ucsschool

lint-flake8:
	flake8 docs setup.py tests ucsschool

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
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

install: clean ## install the package to the active Python's site-packages
	python3 -m pip install --editable .
