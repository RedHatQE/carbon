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

from carbon._compat import ConfigParser
from carbon.exceptions import CarbonActionError, CarbonExecuteError, \
    ScenarioError, CarbonError, CarbonReportError
from carbon.executors import RunnerExecutor
from carbon.orchestrators import AnsibleOrchestrator
from carbon.providers import OpenstackProvider
from carbon.provisioners import OpenstackLibCloudProvisioner, HostProvisioner
from carbon.provisioners.ext import OpenstackLibCloudProvisionerPlugin, LinchpinWrapperProvisionerPlugin
from carbon.resources import Action, Execute, Host, Report, Scenario
from carbon.utils.config import Config


@pytest.fixture(scope='class')
def feature_toggle_config():
    config_file = '../assets/carbon.cfg'
    cfgp = ConfigParser()
    cfgp.read(config_file)
    cfgp.set('feature_toggles:host','plugin_implementation','True')
    with open(config_file, 'w') as cf:
        cfgp.write(cf)
    os.environ['CARBON_SETTINGS'] = config_file
    config = Config()
    config.load()
    return config


@pytest.fixture
def default_report_params():
    params = dict(description='description', executes='execute',
                  provider=dict(name='polarion',
                                credential='polarion'
                                ))
    return params

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

    @staticmethod
    def test_create_report_with_name(default_report_params, config):
        # params = dict(executes=['execute1'], key='value')
        report = Report(name='test.xml', parameters=default_report_params, config=config)
        assert isinstance(report, Report)

    @staticmethod
    def test_create_report_without_name():
        with pytest.raises(CarbonReportError) as ex:
            Report()
        assert 'Unable to build report object. Name field missing!' in \
               ex.value.args

    @staticmethod
    def test_create_report_without_executes(default_report_params, config):
        # params = dict(executes=None, key='value')
        default_report_params['executes'] = None
        with pytest.raises(CarbonReportError) as ex:
            Report(name='test.xml', parameters=default_report_params, config=config)
        assert 'Unable to associate executes to report artifact:test.xml. No executes ' \
               'defined!' in ex.value.args

    @staticmethod
    def test_create_report_with_executes_as_str(default_report_params, config):
        # params = dict(description='description', executes='execute01, execute02')
        default_report_params['executes'] = 'execute01, execute02'
        report = Report(name='test.xml', parameters=default_report_params, config=config)
        assert isinstance(report.executes, list)

    @staticmethod
    def test_build_report_profile_case_01(report_resource):
        assert isinstance(report_resource.profile(), dict)

    @staticmethod
    def test_build_report_profile_case_02(report_resource):
        execute = mock.MagicMock()
        execute.name = 'execute02'
        report_resource.executes = [execute]
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
    @mock.patch.object(os, 'makedirs')
    @pytest.mark.filterwarnings('ignore::DeprecationWarning')
    def test_create_scenario_04(mock_method):
        config = Config()
        config['DATA_FOLDER'] = '/tmp/%s' % uuid.uuid4()
        with pytest.raises(ScenarioError):
            mock_method.side_effect = OSError()
            mock_method.side_effect.errno = 0
            Scenario(config=config, parameters={'k': 'v'})

    @staticmethod
    def test_yaml_data_property(scenario_resource):
        assert isinstance(scenario_resource.yaml_data, dict)

    @staticmethod
    def test_yaml_data_setter(scenario_resource):
        scenario_resource.yaml_data = {'name': 'scenario'}

    @staticmethod
    def test_add_host_resource(scenario_resource, host):
        scenario_resource.add_resource(host)

    @staticmethod
    def test_add_action_resource(scenario_resource, action_resource):
        scenario_resource.add_resource(action_resource)

    @staticmethod
    def test_add_execute_resource(scenario_resource, execute_resource):
        scenario_resource.add_resource(execute_resource)

    @staticmethod
    def test_add_report_resource(scenario_resource, report_resource):
        scenario_resource.add_resource(report_resource)

    @staticmethod
    def test_add_invalid_resource(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.add_resource(mock.MagicMock())

    @staticmethod
    def test_initialize_host_resource(scenario_resource, host):
        scenario_resource.initialize_resource(host)
        assert scenario_resource.hosts.__len__() == 0

    @staticmethod
    def test_initialize_action_resource(scenario_resource, action_resource):
        scenario_resource.initialize_resource(action_resource)
        assert scenario_resource.actions.__len__() == 0

    @staticmethod
    def test_initialize_execute_resource(scenario_resource, execute_resource):
        scenario_resource.initialize_resource(execute_resource)
        assert scenario_resource.executes.__len__() == 0

    @staticmethod
    def test_initialize_report_resource(scenario_resource, report_resource):
        scenario_resource.initialize_resource(report_resource)
        assert scenario_resource.reports.__len__() == 0

    @staticmethod
    def test_initialize_invalid_resource(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.initialize_resource(mock.MagicMock())

    @staticmethod
    def test_hosts_property(scenario_resource):
        assert isinstance(scenario_resource.hosts, list)

    @staticmethod
    def test_hosts_setter(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.hosts = ['host']

    @staticmethod
    def test_add_invalid_hosts(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.add_hosts(mock.MagicMock())

    @staticmethod
    def test_actions_property(scenario_resource):
        assert isinstance(scenario_resource.actions, list)

    @staticmethod
    def test_actions_setter(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.actions = ['action']

    @staticmethod
    def test_add_invalid_action(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.add_actions(mock.MagicMock())

    @staticmethod
    def test_executes_property(scenario_resource):
        assert isinstance(scenario_resource.executes, list)

    @staticmethod
    def test_executes_setter(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.executes = ['execute']

    @staticmethod
    def test_add_invalid_execute(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.add_executes(mock.MagicMock())

    @staticmethod
    def test_reports_property(scenario_resource):
        assert isinstance(scenario_resource.reports, list)

    @staticmethod
    def test_reports_setter(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.reports = ['report']

    @staticmethod
    def test_add_invalid_report(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.add_reports(mock.MagicMock())

    @staticmethod
    def test_profile_uc01(scenario):
        profile = scenario.profile()
        assert isinstance(profile, dict)


class TestHostResource(object):
    @staticmethod
    def __get_params_copy__(params):
        return copy.deepcopy(params)

    def test_create_host_with_name(self, default_host_params, config):
        params = self.__get_params_copy__(default_host_params)
        host = Host(name='host01', config=config, parameters=params)
        assert isinstance(host, Host)
        assert host.name == 'host01'

    def test_create_host_without_name(self, default_host_params, config):
        params = self.__get_params_copy__(default_host_params)
        host = Host(parameters=params, config=config)
        assert 'hst' in host.name

    def test_create_host_undefined_role_or_groups(self, default_host_params):
        params = self.__get_params_copy__(default_host_params)
        params.pop('role')
        with pytest.raises(SystemExit):
            Host(name='host01', parameters=params)

    def test_create_host_undefined_provider(self, default_host_params):
        params = self.__get_params_copy__(default_host_params)
        params.pop('provider')
        with pytest.raises(SystemExit):
            Host(name='host01', parameters=params)

    def test_create_host_invalid_provider(self, default_host_params):
        params = self.__get_params_copy__(default_host_params)
        params['provider']['name'] = 'null'
        with pytest.raises(SystemExit):
            Host(name='host01', parameters=params)

    def test_create_host_invalid_provisioner(
            self, default_host_params, config):
        params = self.__get_params_copy__(default_host_params)
        params['provisioner'] = 'null'
        with pytest.raises(SystemExit):
            Host(name='host01', parameters=params, config=config)

    def test_create_host_with_provisioner_set(
            self, default_host_params, config):
        params = self.__get_params_copy__(default_host_params)
        params['provisioner'] = 'openstack-libcloud'
        host = Host(name='host01', parameters=params, config=config)
        assert host.provisioner is OpenstackLibCloudProvisioner

    def test_create_host_undefined_credential(self, default_host_params):
        params = self.__get_params_copy__(default_host_params)
        params['provider'].pop('credential')
        with pytest.raises(SystemExit):
            Host(name='host01', parameters=params)

    def test_create_host_provider_static(self, default_host_params):
        params = self.__get_params_copy__(default_host_params)
        params.pop('provider')
        params['ip_address'] = '127.0.0.1'
        Host(name='host01', parameters=params)

    def test_ip_address_property(self, host):
        assert host.ip_address is None

    def test_ip_address_setter(self, host):
        host.ip_address = '127.0.0.1'
        assert host.ip_address == '127.0.0.1'

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
        assert host.provisioner is OpenstackLibCloudProvisioner

    def test_provisioner_setter(self, host):
        with pytest.raises(AttributeError) as ex:
            host.provisioner = 'null'
        assert 'You cannot set the host provisioner after host class ' \
               'is instantiated.' in ex.value.args

    def test_role_property(self, host):
        assert host.role[-1] == 'client'

    def test_role_setter(self, host):
        with pytest.raises(AttributeError) as ex:
            host.role = 'null'
        assert 'You cannot set the role after host class is instantiated.' in \
               ex.value.args

    def test_build_profile_uc01(self, host):
        assert isinstance(host.profile(), dict)

    def test_build_profile_uc02(self, host):
        static_host = copy.copy(host)
        setattr(static_host, 'ip_address', '127.0.0.1')
        assert isinstance(static_host.profile(), dict)

    def test_validate_success(self, host):
        host.validate()

    def test_provisioner_plugin_property(self, default_host_params, feature_toggle_config):
        params = self.__get_params_copy__(default_host_params)
        host = Host(name='host01', parameters=params, config=feature_toggle_config)
        assert host.provisioner_plugin is LinchpinWrapperProvisionerPlugin

    def test_provisioner_plugin_setter(self, default_host_params, feature_toggle_config):
        params = self.__get_params_copy__(default_host_params)
        host = Host(name='host01', parameters=params, config=feature_toggle_config)
        with pytest.raises(AttributeError) as ex:
            host.provisioner_plugin = 'null'
        assert 'You cannot set the host provisioner plugin after host class ' \
               'is instantiated.' in ex.value.args

    def test_create_host_that_loads_host_provisioner_interface(
            self, default_host_params, feature_toggle_config):
        params = self.__get_params_copy__(default_host_params)
        host = Host(name='host01', parameters=params, config=feature_toggle_config)
        assert host.provisioner is HostProvisioner

    def test_create_host_with_provisioner_set_loads_provisioner_plugin(
            self, default_host_params, feature_toggle_config):
        params = self.__get_params_copy__(default_host_params)
        params['provisioner'] = 'openstack-libcloud'
        host = Host(name='host01', parameters=params, config=feature_toggle_config)
        assert host.provisioner_plugin is OpenstackLibCloudProvisionerPlugin

    def test_create_host_invalid_provisioner_plugin(
            self, default_host_params, feature_toggle_config):
        params = self.__get_params_copy__(default_host_params)
        params['provisioner'] = 'null'
        with pytest.raises(SystemExit):
            Host(name='host01', parameters=params, config=feature_toggle_config)

    def test_group_property(self, default_host_params, config):
        params = self.__get_params_copy__(default_host_params)
        params.pop('role')
        params.update(dict(groups=['group1']))
        host = Host(name='host01', parameters=params, config=config)
        assert host.groups[-1] == 'group1'