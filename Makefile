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

test-integration: install-oc-client
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
	rm -rf *.egg
	rm -rf *.egg-info
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

build-image-devel:
	docker build -t carbon-framework:devel .
	docker images --filter=reference='carbon-framework:devel'
	docker tag carbon-framework:devel docker-registry.engineering.redhat.com/carbon/carbon-framework:devel
	docker images --filter=reference='docker-registry.engineering.redhat.com/carbon/carbon-framework:devel'

build-image-latest:
	docker build -t carbon-framework:latest .
	docker images --filter=reference='carbon-framework:latest'
	docker tag carbon-framework:latest docker-registry.engineering.redhat.com/carbon/carbon-framework:latest
	docker images --filter=reference='docker-registry.engineering.redhat.com/carbon/carbon-framework:latest'

deploy-image-devel:
	docker login -u $$USER docker-registry.engineering.redhat.com
	docker push docker-registry.engineering.redhat.com/carbon/carbon-framework:devel

deploy-image-latest:
	docker login -u $$USER docker-registry.engineering.redhat.com
	docker push docker-registry.engineering.redhat.com/carbon/carbon-framework:latest

install-oc-client:
	wget -O oc.tar.gz https://github.com/openshift/origin/releases/download/\
	v1.5.0/openshift-origin-client-tools-v1.5.0-031cbe4-linux-64bit.tar.gz
	tar xvf oc.tar.gz
	rm oc.tar.gz
	mv openshift-*/oc /home/$$USER/.local/bin
	rm -rf openshift-*
