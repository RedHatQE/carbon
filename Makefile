.PHONY: clean-pyc clean-tests clean docs

all: clean-pyc clean-tests clean test-functional docs

clean-all: clean-pyc clean-tests clean

test-all: test-functional test-scenario

test-functional:
	tox -e py27-unit,py36-unit

test-scenario:
	tox -e py27-scenario,py36-scenario

clean:
	rm -rf *.egg
	rm -rf *.egg-info
	rm -rf docs/_build
	rm -rf docs/.examples
	rm -rf .cache
	rm -rf .tox
	rm -rf build
	rm -rf dist

clean-tests:
	rm -rf tests/.coverage*
	rm -rf tests/.cache
	rm -rf tests/coverage
	rm -rf tests/localhost_scenario/.carbon
	rm -rf tests/localhost_scenario/.ansible
	rm -rf tests/functional/coverage
	rm -rf tests/functional/.ansible
	rm -rf tests/functional/.coverage*

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

docs:
	tox -e docs

docs-wiki:
	tox -e docs-wiki -- -D confluence_space_name='${CONF_SPACE_NAME}' -D confluence_parent_page='${CONF_PARENT_PAGE}' -D confluence_server_user='${CONF_SERVER_USER}' -D confluence_server_pass='${CONF_SERVER_PASS}'	

bump-major:
	bumpversion major --commit

bump-minor:
	bumpversion minor --commit

bump-patch:
	bumpversion patch --commit
