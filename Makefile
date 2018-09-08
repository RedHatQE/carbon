.PHONY: clean-pyc clean-tests clean docs

all: clean-pyc clean-tests clean test-functional docs

clean-all: clean-pyc clean-tests clean

test-all: test-functional

test-functional:
	tox -e py27,py36

clean:
	rm -rf *.egg
	rm -rf *.egg-info
	rm -rf docs/_build
	rm -rf .cache
	rm -rf .tox
	rm -rf build
	rm -rf dist

clean-tests:
	rm -rf tests/.coverage*
	rm -rf tests/.cache
	rm -rf tests/coverage

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

docs:
	tox -e docs

bump-major:
	bumpversion major --commit

bump-minor:
	bumpversion minor --commit

bump-patch:
	bumpversion patch --commit