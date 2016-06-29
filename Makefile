.PHONY: clean-pyc clean test tox-test test-with-mem docs audit

all: clean-pyc clean-reports clean tox-test

clean-all: clean-pyc clean-reports clean

test:
	py.test tests

tox-test:
	tox

release:
	python scripts/make-release.py

clean:
	rm -rf *.egg
	rm -rf *.egg-info
	rm -rf docs/_build
	rm -rf .cache
	rm -rf .tox
	rm -rf build
	rm -rf dist

clean-reports:
	rm -rf tests/report
	rm -rf flake8-report.txt 
	rm -rf junit-report.xml

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

docs:
	$(MAKE) -C docs html