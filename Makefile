.PHONY: clean-pyc clean-tests clean docs

ATTENTION = \033[0;31m
COLORLESS = \033[0m
WARNING = \033[0;33m

all: clean-pyc clean-tests clean test-functional

clean-all: clean-pyc clean-tests clean

test-all:
	@echo -e "$(ATTENTION)**** ATTENTION: CREDENTIALS REQUIRED ****"
	@echo -e "$(WARNING)"
	@echo -e "Please view each module under carbon.tests to see"
	@echo -e "which environment variables need to be set to run tests"
	@echo -e "$(COLORLESS)"
	@echo
	@echo -e "**** CARBON ALL TESTS ****"
	tox -e py27-functional,py36-functional,py27-integration

test-functional:
	@echo "**** CARBON FUNCTIONAL TESTS ****"
	tox -e py27-functional,py36-functional

test-integration:
	@echo -e "$(ATTENTION)**** ATTENTION: CREDENTIALS REQUIRED ****"
	@echo -e "$(WARNING)"
	@echo -e "Please view each module under carbon.tests to see"
	@echo -e "which environment variables need to be set to run tests."
	@echo -e "$(COLORLESS)"
	@echo
	@echo "**** CARBON INTEGRATION TESTS ****"
	tox -e py27-integration

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

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

docs:
	python setup.py build_sphinx
