.PHONY: clean-pyc clean-tests clean test tox-test docs audit

all: clean-pyc clean-tests clean tox-test

clean-all: clean-pyc clean-tests clean

test:
	cd tests; pytest -v

tox-test:
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
	rm -rf tests/coverage-report
	rm -rf tests/.coverage*
	rm -rf tests/__pycache__
	rm -rf tests/junit-report.xml
	rm -rf tests/flake8-report.txt

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

docs:
	$(MAKE) -C docs html