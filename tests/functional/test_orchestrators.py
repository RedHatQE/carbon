# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
    tests.test_orchestrators

    Unit tests for testing carbon orchestrator classes.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import mock
import pytest

from carbon.orchestrators import ChefOrchestrator, PuppetOrchestrator


@pytest.fixture(scope='class')
def chef_orchestrator():
    package = mock.MagicMock()
    return ChefOrchestrator(package)


@pytest.fixture(scope='class')
def puppet_orchestrator():
    package = mock.MagicMock()
    return PuppetOrchestrator(package)


class TestChefOrchestrator(object):
    @staticmethod
    def test_constructor(chef_orchestrator):
        assert isinstance(chef_orchestrator, ChefOrchestrator)

    @staticmethod
    def test_validate(chef_orchestrator):
        with pytest.raises(NotImplementedError):
            chef_orchestrator.validate()

    @staticmethod
    def test_run(chef_orchestrator):
        with pytest.raises(NotImplementedError):
            chef_orchestrator.run()


class TestPuppetOrchestrator(object):
    @staticmethod
    def test_constructor(puppet_orchestrator):
        assert isinstance(puppet_orchestrator, PuppetOrchestrator)

    @staticmethod
    def test_validate(puppet_orchestrator):
        with pytest.raises(NotImplementedError):
            puppet_orchestrator.validate()

    @staticmethod
    def test_run(puppet_orchestrator):
        with pytest.raises(NotImplementedError):
            puppet_orchestrator.run()
