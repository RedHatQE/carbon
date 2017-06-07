.PHONY: clean-pyc clean-tests clean docs

all: clean-pyc clean-tests clean test

clean-all: clean-pyc clean-tests clean

test:
	tox

release:
	python scripts/make-release.py

clean:
	rm -rf src/*.egg
	rm -rf src/*.egg-info
	rm -rf docs/_build
	rm -rf .cache
	rm -rf .tox
	rm -rf build
	rm -rf dist

clean-tests:
	rm -rf tests/coverage-report*
	rm -rf tests/.coverage*
	rm -rf tests/.workspace
	rm -rf tests/__pycache__
	rm -rf tests/cover
	rm -rf tests/coverage.xml
	rm -rf tests/nosetests.xml

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

docs:
	$(MAKE) -C docs html
