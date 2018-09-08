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
    tests.test_resources

    Unit tests for testing carbon resources classes.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import os
import uuid

import mock
import pytest

from carbon.exceptions import CarbonActionError, CarbonExecuteError, \
    ScenarioError
from carbon.executors import RunnerExecutor
from carbon.orchestrators import AnsibleOrchestrator
from carbon.resources import Action, Execute, Report, Scenario
from carbon.utils.config import Config


@pytest.fixture(scope='class')
def action_resource():
    return Action(
        name='action',
        parameters=dict(
            description='description',
            hosts=['host01'],
            orchestrator='ansible'
        )
    )


@pytest.fixture(scope='class')
def action_resource_cleanup():
    return Action(
        name='action',
        parameters=dict(
            description='description',
            hosts=['host01'],
            orchestrator='ansible',
            cleanup=dict(
                name='cleanup_action',
                description='description',
                hosts=['host01'],
                orchestrator='ansible'
            )
        )
    )


@pytest.fixture(scope='class')
def report_resource():
    params = dict(key='value')
    return Report(parameters=params)


@pytest.fixture(scope='class')
def execute_resource():
    params = dict(description='description', hosts='host01', executor='runner')
    return Execute(name='execute', parameters=params)


@pytest.fixture(scope='class')
def scenario_resource():
    return Scenario(config=Config(), parameters={'k': 'v'})


class TestActionResource(object):
    @staticmethod
    def test_create_action_with_name():
        params = dict(
            description='description goes here.',
            hosts=['host01']
        )
        action = Action(name='action', parameters=params)
        assert isinstance(action, Action)

    @staticmethod
    def test_create_action_without_name():
        params = dict(
            description='description goes here.',
            hosts=['host01']
        )

        with pytest.raises(CarbonActionError):
            Action(parameters=params)

    @staticmethod
    def test_create_action_with_name_in_parameters():
        params = dict(
            name='action',
            description='description goes here.',
            hosts=['host01']
        )

        action = Action(parameters=params)
        assert action.name == 'action'

    @staticmethod
    def test_create_action_without_hosts():
        params = dict(
            name='action',
            description='description goes here.',
            hosts=None
        )
        with pytest.raises(CarbonActionError) as ex:
            Action(parameters=params)
        assert 'Unable to associate hosts to action: action.No hosts ' \
               'defined!' in ex.value.args

    @staticmethod
    def test_create_action_with_hosts_as_str():
        params = dict(
            description='description goes here.',
            hosts='host01, host02',
            key='value'
        )
        action = Action(name='action', parameters=params)
        assert isinstance(action.hosts, list)

    @staticmethod
    def test_create_action_with_invalid_orchestrator():
        params = dict(
            description='description goes here.',
            hosts=['host01'],
            orchestrator='abc'
        )
        with pytest.raises(CarbonActionError) as ex:
            Action(name='action', parameters=params)
        assert 'Orchestrator: abc is not supported!' in ex.value.args

    @staticmethod
    def test_orchestrator_property(action_resource):
        assert action_resource.orchestrator == AnsibleOrchestrator

    @staticmethod
    def test_orchestrator_setter(action_resource):
        with pytest.raises(AttributeError) as ex:
            action_resource.orchestrator = 'null'
        assert 'Orchestrator class property cannot be set.' in ex.value.args

    @staticmethod
    def test_build_profile_case_01(action_resource):
        assert isinstance(action_resource.profile(), dict)

    @staticmethod
    def test_build_profile_case_02(action_resource):
        host = mock.MagicMock()
        host.name = 'host01'
        action_resource.hosts = [host]
        assert isinstance(action_resource.profile(), dict)

    @staticmethod
    def test_create_action_with_cleanup_action(action_resource_cleanup):
        assert hasattr(action_resource_cleanup, 'cleanup')


class TestReportResource(object):
    @staticmethod
    def test_constructor(report_resource):
        assert isinstance(report_resource, Report)

    @staticmethod
    def test_build_profile(report_resource):
        assert isinstance(report_resource.profile(), dict)


class TestExecuteResource(object):
    @staticmethod
    def test_create_execute_with_name():
        params = dict(hosts=['host01'], key='value')
        execute = Execute(name='execute', parameters=params)
        assert isinstance(execute, Execute)

    @staticmethod
    def test_create_execute_without_name():
        with pytest.raises(CarbonExecuteError) as ex:
            Execute()
        assert 'Unable to build execute object. Name field missing!' in \
            ex.value.args

    @staticmethod
    def test_create_execute_with_invalid_executor():
        params = dict(hosts=['host01'], key='value', executor='abc')
        with pytest.raises(CarbonExecuteError) as ex:
            Execute(name='execute', parameters=params)
        assert 'Executor: abc is not supported!' in ex.value.args

    @staticmethod
    def test_create_execute_without_hosts():
        params = dict(hosts=None, key='value', executor='runner')
        with pytest.raises(CarbonExecuteError) as ex:
            Execute(name='execute', parameters=params)
        assert 'Unable to associate hosts to executor:execute. No hosts ' \
               'defined!' in ex.value.args

    @staticmethod
    def test_create_execute_with_hosts_as_str():
        params = dict(description='description', hosts='host01, host02')
        execute = Execute(name='execute', parameters=params)
        assert isinstance(execute.hosts, list)

    @staticmethod
    def test_create_execute_with_artifacts_as_str():
        params = dict(description='description', hosts='host01, host02',
                      artifacts='test.log, console.log')
        execute = Execute(name='execute', parameters=params)
        assert isinstance(execute.artifacts, list)

    @staticmethod
    def test_executor_property(execute_resource):
        assert execute_resource.executor == RunnerExecutor

    @staticmethod
    def test_executor_setter(execute_resource):
        with pytest.raises(AttributeError) as ex:
            execute_resource.executor = 'null'
        assert 'Executor class property cannot be set.' in ex.value.args

    @staticmethod
    def test_build_profile_case_01(execute_resource):
        assert isinstance(execute_resource.profile(), dict)

    @staticmethod
    def test_build_profile_case_02(execute_resource):
        host = mock.MagicMock()
        host.name = 'host01'
        execute_resource.hosts = [host]
        assert isinstance(execute_resource.profile(), dict)


class TestScenarioResource(object):
    @staticmethod
    def test_create_scenario_01():
        scenario = Scenario(config=Config(), parameters={'k': 'v'})
        assert isinstance(scenario, Scenario)

    @staticmethod
    def test_create_scenario_02():
        config = Config()
        config['DATA_FOLDER'] = '/tmp/%s' % uuid.uuid4()
        scenario = Scenario(config=config, parameters={'k': 'v'})
        assert os.path.exists(scenario.data_folder)
        os.removedirs(scenario.data_folder)

    @staticmethod
    def test_create_scenario_03():
        config = Config()
        config['DATA_FOLDER'] = '/root/%s' % uuid.uuid4()
        with pytest.raises(ScenarioError):
            Scenario(config=config, parameters={'k': 'v'})

    @staticmethod
    def test_yaml_data_property(scenario_resource):
        assert isinstance(scenario_resource.yaml_data, dict)

    @staticmethod
    def test_yaml_data_setter(scenario_resource):
        scenario_resource.yaml_data = {'name': 'scenario'}
