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

import copy
import os
import uuid

import mock
import pytest
from carbon.exceptions import CarbonActionError, CarbonExecuteError, \
    ScenarioError, CarbonHostError
from carbon.executors import RunnerExecutor
from carbon.orchestrators import AnsibleOrchestrator
from carbon.providers import OpenstackProvider
from carbon.provisioners import OpenstackProvisioner
from carbon.resources import Action, Execute, Host, Report, Scenario
from carbon.utils.config import Config


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


class TestHostResource(object):
    @staticmethod
    def __get_params_copy__(params):
        return copy.deepcopy(params)

    def test_create_host_with_name(self, default_host_params):
        params = self.__get_params_copy__(default_host_params)
        host = Host(name='host01', parameters=params)
        assert isinstance(host, Host)
        assert host.name == 'host01'

    def test_create_host_without_name(self, default_host_params):
        params = self.__get_params_copy__(default_host_params)
        host = Host(parameters=params)
        assert 'hst' in host.name

    def test_create_host_undefined_role(self, default_host_params):
        params = self.__get_params_copy__(default_host_params)
        params.pop('role')
        with pytest.raises(CarbonHostError) as ex:
            Host(name='host01', parameters=params)
        assert 'A role must be set for host host01.' in ex.value.args

    def test_create_host_undefined_provider(self, default_host_params):
        params = self.__get_params_copy__(default_host_params)
        params.pop('provider')
        with pytest.raises(CarbonHostError) as ex:
            Host(name='host01', parameters=params)
        assert 'A provider must be set for the host host01.' in ex.value.args

    def test_create_host_invalid_provider(self, default_host_params):
        params = self.__get_params_copy__(default_host_params)
        params['provider'] = 'null'
        with pytest.raises(CarbonHostError) as ex:
            Host(name='host01', parameters=params)
        assert 'Invalid provider for host host01.' in ex.value.args

    def test_create_host_invalid_provisioner(self, default_host_params):
        params = self.__get_params_copy__(default_host_params)
        params['provisioner'] = 'null'
        with pytest.raises(CarbonHostError) as ex:
            Host(name='host01', parameters=params)
        assert 'Invalid provisioner for host host01.' in ex.value.args

    def test_create_host_with_provisioner_set(self, default_host_params):
        params = self.__get_params_copy__(default_host_params)
        params['provisioner'] = 'openstack'
        host = Host(name='host01', parameters=params)
        assert host.provisioner is OpenstackProvisioner

    def test_create_host_undefined_credential(self, default_host_params):
        params = self.__get_params_copy__(default_host_params)
        params.pop('credential')
        with pytest.raises(CarbonHostError) as ex:
            Host(name='host01', parameters=params)
        assert 'A credential must be set for the hosts provider None.' in \
               ex.value.args

    def test_create_host_undefined_provider_creds(self, default_host_params):
        params = self.__get_params_copy__(default_host_params)
        params.pop('provider_creds')
        with pytest.raises(CarbonHostError) as ex:
            Host(name='host01', parameters=params)
        assert 'Provider credentials must be set for host host01.' in \
               ex.value.args

    def test_create_host_provider_static(self, default_host_params):
        params = self.__get_params_copy__(default_host_params)
        params['provider'] = 'static'
        params['static_ip_address'] = 'null'
        params['static_hostname'] = 'null'
        Host(name='host01', parameters=params)

    def test_create_host_missing_req_provider_param(self, default_host_params):
        params = self.__get_params_copy__(default_host_params)
        params.pop('os_image')
        with pytest.raises(CarbonHostError):
            Host(name='host01', parameters=params)

    def test_create_host_missing_req_provider_cred(self, default_host_params):
        params = self.__get_params_copy__(default_host_params)
        params['provider_creds'][0].pop('auth_url')
        with pytest.raises(CarbonHostError):
            Host(name='host01', parameters=params)

    def test_ip_address_property(self, host):
        assert host.ip_address is None

    def test_ip_address_setter(self, host):
        with pytest.raises(AttributeError) as ex:
            host.ip_address = '127.0.0.1'
        assert 'You cannot set ip address directly. Use function ' \
               '~Host.set_ip_address' in ex.value.args

    def test_set_ip_address(self, host):
        host.set_ip_address('127.0.0.1')
        assert host.ip_address == '127.0.0.1'
        assert getattr(host, 'os_ip_address', '127.0.0.1')

    def test_metadata_property(self, host):
        assert host.metadata == {}

    def test_metadata_setter(self, host):
        with pytest.raises(AttributeError) as ex:
            host.metadata = {'k': 'v'}
        assert 'You cannot set metadata directly. Use function ' \
               '~Host.set_metadata' in ex.value.args

    def test_set_metadata(self, host):
        with pytest.raises(NotImplementedError):
            host.set_metadata()

    def test_ansible_params_property(self, host):
        assert host.ansible_params == {}

    def test_ansible_params_setter(self, host):
        with pytest.raises(AttributeError) as ex:
            host.ansible_params = {'ansible_user': 'user01'}
        assert 'You cannot set the ansible parameters directly. This is set' \
               ' one time within the YAML input.' in ex.value.args

    def test_provider_property(self, host):
        assert isinstance(host.provider, OpenstackProvider)

    def test_provider_setter(self, host):
        with pytest.raises(AttributeError) as ex:
            host.provider = 'null'
        assert 'You cannot set the host provider after host class is ' \
               'instantiated.' in ex.value.args

    def test_provisioner_property(self, host):
        assert host.provisioner is OpenstackProvisioner

    def test_provisioner_setter(self, host):
        with pytest.raises(AttributeError) as ex:
            host.provisioner = 'null'
        assert 'You cannot set the host provisioner after host class ' \
               'is instantiated.' in ex.value.args

    def test_role_property(self, host):
        assert host.role == 'client'

    def test_role_setter(self, host):
        with pytest.raises(AttributeError) as ex:
            host.role = 'null'
        assert 'You cannot set the role after host class is instantiated.' in \
               ex.value.args

    def test_uuid_property(self, host):
        assert host.uid

    def test_uuid_setter(self, host):
        with pytest.raises(AttributeError) as ex:
            host.uid = 'null'
        assert 'You cannot set the uid for the host.' in ex.value.args

    def test_build_profile(self, host):
        assert isinstance(host.profile(), dict)

    def test_validate_success(self, host):
        host.provider.validate = mock.MagicMock(return_value=[])
        host.validate()

    def test_validate_failure(self, host):
        host.provider.validate = mock.MagicMock(return_value=[('a', 'b')])
        with pytest.raises(CarbonHostError) as ex:
            host.validate()
        assert 'Host host01 validation failed!' in ex.value.args

    def test_create_host_with_provider_prefix_name(self, default_host_params):
        params = self.__get_params_copy__(default_host_params)
        params['os_name'] = 'null'
        with pytest.raises(CarbonHostError) as ex:
            Host(name='host01', parameters=params)
        assert "The os_name parameter for host01 should not be set as it is " \
               "under the framework's control" in ex.value.args

