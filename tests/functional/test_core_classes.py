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
    tests.test_core_classes

    Unit tests for testing carbon core classes.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import copy
import random
import time
import types

import mock
import pytest

from carbon.core import CarbonOrchestrator, CarbonProvider, CarbonProvisioner, \
    CarbonResource, CarbonTask, LoggerMixin, TimeMixin, CarbonExecutor, \
    CarbonPlugin, ProvisionerPlugin, ExecutorPlugin, ImporterPlugin, OrchestratorPlugin
from carbon.exceptions import CarbonError, LoggerMixinError


@pytest.fixture(scope='class')
def time_mixin():
    return TimeMixin()


@pytest.fixture(scope='class')
def logger_mixin():
    return LoggerMixin()


@pytest.fixture(scope='class')
def carbon_task_unamed():
    return CarbonTask()


@pytest.fixture(scope='class')
def carbon_task_named():
    return CarbonTask(name='orchestrate')


@pytest.fixture(scope='class')
def carbon_resource():
    return CarbonResource(name='action', config={})


@pytest.fixture
def carbon_provisioner(host):
    return CarbonProvisioner(host)


@pytest.fixture(scope='class')
def carbon_provider():
    return CarbonProvider()


@pytest.fixture(scope='class')
def carbon_orchestrator():
    return CarbonOrchestrator()


@pytest.fixture(scope='class')
def carbon_executor():
    return CarbonExecutor()

@pytest.fixture(scope='class')
def carbon_plugin():
    return CarbonPlugin()

@pytest.fixture(scope='class')
def report_profile():
    profile = dict(name='test.xml',
                   description='testing',
                   importer='polarion',
                   data_folder='/tmp',
                   workspace='/tmp',
                   artifacts=[],
                   provider_credentials={},
                   config_params={},
                   provider={'name': 'test'})
    return profile

@pytest.fixture
def provisioner_plugin(host):
    return ProvisionerPlugin(host)

@pytest.fixture(scope='class')
def executor_plugin():
    return ExecutorPlugin()

@pytest.fixture(scope='class')
def importer_plugin(report_profile):
    return ImporterPlugin(report_profile)

@pytest.fixture(scope='class')
def orchestrator_plugin():
    return OrchestratorPlugin()


class TestTimeMixin(object):
    @staticmethod
    def test_default_start_time(time_mixin):
        assert getattr(time_mixin, '_start_time') is None

    @staticmethod
    def test_default_end_time(time_mixin):
        assert getattr(time_mixin, '_end_time') is None

    @staticmethod
    def test_default_hours(time_mixin):
        assert getattr(time_mixin, '_hours') == 0

    @staticmethod
    def test_default_minutes(time_mixin):
        assert getattr(time_mixin, '_minutes') == 0

    @staticmethod
    def test_default_seconds(time_mixin):
        assert getattr(time_mixin, '_secounds') == 0

    @staticmethod
    def test_start_time(time_mixin):
        initial_start_time = time_mixin.start_time
        time_mixin.start()
        assert time_mixin.start_time != initial_start_time

    @staticmethod
    def test_end_time(time_mixin):
        time_mixin.start()
        time.sleep(1)
        time_mixin.end()
        assert time_mixin.start_time != time_mixin.end_time

    @staticmethod
    def test_start_time_setter(time_mixin):
        with pytest.raises(CarbonError):
            setattr(time_mixin, 'start_time', 0)

    @staticmethod
    def test_end_time_setter(time_mixin):
        with pytest.raises(CarbonError):
            setattr(time_mixin, 'end_time', 0)

    @staticmethod
    def test_properties(time_mixin):
        assert type(time_mixin.hours) is float
        assert type(time_mixin.minutes) is float
        assert type(time_mixin.seconds) is float


class TestCarbonTask(object):
    @staticmethod
    def test_constructor_wo_name(carbon_task_unamed):
        with pytest.raises(AttributeError):
            print(carbon_task_unamed.name)

    @staticmethod
    def test_constructor_w_name(carbon_task_named):
        assert carbon_task_named.name == 'orchestrate'

    @staticmethod
    def test_run(carbon_task_named):
        carbon_task_named.run()

    @staticmethod
    def test_str(carbon_task_named):
        assert carbon_task_named.__str__() == 'orchestrate'


class TestLoggerMixin(object):
    @staticmethod
    def test_create_logger(logger_mixin, config):
        logger_mixin.create_logger(name=__name__, config=config)

    @staticmethod
    def test_skip_create_logger(logger_mixin, config):
        count = 0
        while True:
            logger_mixin.create_logger(name=__name__, config=config)
            count += 1
            if count == 2:
                break

    @staticmethod
    def test_get_logger(logger_mixin, config):
        logger_mixin.create_logger(name=__name__, config=config)
        assert logger_mixin.logger.name == __name__

    @staticmethod
    def test_create_logger_dir(logger_mixin, config):
        logger_mixin.logger.handlers = []
        cfg = copy.copy(config)
        cfg['DATA_FOLDER'] = '/tmp/%s' % random.randint(0, 1000)
        logger_mixin.create_logger(name=__name__, config=cfg)

    @staticmethod
    def test_create_logger_dir_permission_denied(logger_mixin, config):
        with pytest.raises(LoggerMixinError):
            logger_mixin.logger.handlers = []
            cfg = copy.copy(config)
            cfg['DATA_FOLDER'] = '/root'
            logger_mixin.create_logger(name=__name__, config=cfg)


class TestCarbonResource(object):
    @staticmethod
    def test_constructor():
        carbon_resource = CarbonResource()
        assert isinstance(carbon_resource, CarbonResource)

    @staticmethod
    def test_name_property(carbon_resource):
        assert carbon_resource.name == 'action'

    @staticmethod
    def test_name_setter(carbon_resource):
        with pytest.raises(AttributeError):
            carbon_resource.name = 'execute'

    @staticmethod
    def test_config_property(carbon_resource, config):
        assert carbon_resource.config == {}

    @staticmethod
    def test_config_setter(carbon_resource):
        with pytest.raises(AttributeError):
            carbon_resource.config = 'null'

    @staticmethod
    def test_description_property(carbon_resource):
        assert carbon_resource.description is None

    @staticmethod
    def test_description_setter(carbon_resource):
        with pytest.raises(AttributeError):
            carbon_resource.description = 'null'

    @staticmethod
    def test_workspace_property(config):
        carbon_resource = CarbonResource(config=config)
        assert carbon_resource.workspace == config['WORKSPACE']

    @staticmethod
    def test_workspace_setter(carbon_resource):
        with pytest.raises(AttributeError):
            carbon_resource.workspace = 'null'

    @staticmethod
    def test_data_folder_property(config):
        carbon_resource = CarbonResource(config=config)
        assert carbon_resource.data_folder == config['DATA_FOLDER']

    @staticmethod
    def test_data_folder_setter(carbon_resource):
        with pytest.raises(AttributeError):
            carbon_resource.data_folder = 'null'

    @staticmethod
    def test_validate(carbon_resource):
        carbon_resource.validate()

    @staticmethod
    def test_dump(carbon_resource):
        carbon_resource.dump()

    @staticmethod
    def test_profile(carbon_resource):
        with pytest.raises(NotImplementedError):
            carbon_resource.profile()

    @staticmethod
    def test_get_tasks(carbon_resource):
        assert carbon_resource.get_tasks() == []


class TestCarbonProvisioner(object):
    @staticmethod
    def test_create(carbon_provisioner):
        with pytest.raises(NotImplementedError):
            carbon_provisioner.create()

    @staticmethod
    def test_delete(carbon_provisioner):
        with pytest.raises(NotImplementedError):
            carbon_provisioner.delete()

    @staticmethod
    def test_name_property(carbon_provisioner):
        assert carbon_provisioner.name is None

    @staticmethod
    def test_name_setter(carbon_provisioner):
        with pytest.raises(AttributeError) as ex:
            carbon_provisioner.name = 'null'
        assert 'You cannot set name for the provisioner.' in ex.value.args


class TestCarbonProvider(object):
    @staticmethod
    def test_constructor(carbon_provider):
        assert isinstance(carbon_provider, CarbonProvider)

    @staticmethod
    def test_str(carbon_provider):
        with pytest.raises(AssertionError):
            assert carbon_provider.__str__() is None

    @staticmethod
    def test_name_property(carbon_provider):
        assert carbon_provider.name is None

    @staticmethod
    def test_name_setter(carbon_provider):
        with pytest.raises(AttributeError) as ex:
            carbon_provider.name = 'null'
        assert 'You cannot set provider name.' in ex.value.args

    @staticmethod
    def test_credentials_property(carbon_provider):
        assert isinstance(carbon_provider.credentials, dict)

    @staticmethod
    def test_credentials_setter(carbon_provider):
        with pytest.raises(ValueError) as ex:
            carbon_provider.credentials = 'null'
        assert 'You cannot set provider credentials directly. Use ' \
               'function ~CarbonProvider.set_credentials' in ex.value.args

    @staticmethod
    def test_set_credentials(carbon_provider):
        provider = copy.deepcopy(carbon_provider)
        provider.req_credential_params = [('name', [str])]
        provider.opt_credential_params = [('region', [str])]
        provider.set_credentials({'name': 'v1', 'region': 'v1'})

    @staticmethod
    def test_get_mandatory_parameters(carbon_provider):
        assert isinstance(carbon_provider.req_params, list)

    @staticmethod
    def test_get_mandatory_credentials_parameters(carbon_provider):
        assert isinstance(carbon_provider.req_credential_params, list)

    @staticmethod
    def test_get_optional_parameters(carbon_provider):
        assert isinstance(carbon_provider.opt_params, list)

    @staticmethod
    def test_get_optional_credentials_parameters(carbon_provider):
        assert isinstance(carbon_provider.opt_credential_params, list)


class TestCarbonOrchestrator(object):
    @staticmethod
    def test_constructor(carbon_orchestrator):
        assert isinstance(carbon_orchestrator, CarbonOrchestrator)

    @staticmethod
    def test_validate(carbon_orchestrator):
        with pytest.raises(NotImplementedError):
            carbon_orchestrator.validate()

    @staticmethod
    def test_run(carbon_orchestrator):
        with pytest.raises(NotImplementedError):
            carbon_orchestrator.run()

    @staticmethod
    def test_name_property(carbon_orchestrator):
        assert carbon_orchestrator.name is None

    @staticmethod
    def test_name_setter(carbon_orchestrator):
        with pytest.raises(AttributeError) as ex:
            carbon_orchestrator.name = 'null'
        assert 'You cannot set name for the orchestrator.' in ex.value.args

    @staticmethod
    def test_action_property(carbon_orchestrator):
        assert carbon_orchestrator.action is None

    @staticmethod
    def tests_action_setter(carbon_orchestrator):
        with pytest.raises(AttributeError) as ex:
            carbon_orchestrator.action = 'null'
        assert 'You cannot set the action the orchestrator will perform.' in \
            ex.value.args

    @staticmethod
    def test_hosts_property(carbon_orchestrator):
        assert carbon_orchestrator.hosts is None

    @staticmethod
    def test_hosts_setter(carbon_orchestrator):
        with pytest.raises(AttributeError) as ex:
            carbon_orchestrator.hosts = 'null'
        assert 'Hosts cannot be set once the object is created.' in \
               ex.value.args

    @staticmethod
    def test_get_mandatory_parameters(carbon_orchestrator):
        data = carbon_orchestrator.get_mandatory_parameters()
        assert isinstance(data, types.GeneratorType)

    @staticmethod
    def test_get_optional_parameters(carbon_orchestrator):
        data = carbon_orchestrator.get_optional_parameters()
        assert isinstance(data, types.GeneratorType)

    @staticmethod
    def test_get_all_parameters(carbon_orchestrator):
        data = carbon_orchestrator.get_all_parameters()
        assert isinstance(data, types.GeneratorType)

    @staticmethod
    @mock.patch.object(CarbonOrchestrator, 'get_all_parameters')
    def test_build_profile(mock_01, carbon_orchestrator):
        mock_01.return_value = ('name',)
        action = mock.MagicMock()
        profile = carbon_orchestrator.build_profile(action)
        assert isinstance(profile, dict)


class TestCarbonExecutor(object):
    @staticmethod
    def test_constructor(carbon_executor):
        assert isinstance(carbon_executor, CarbonExecutor)

    @staticmethod
    def test_validate(carbon_executor):
        with pytest.raises(NotImplementedError):
            carbon_executor.validate()

    @staticmethod
    def test_run(carbon_executor):
        with pytest.raises(NotImplementedError):
            carbon_executor.run()

    @staticmethod
    def test_name_property(carbon_executor):
        assert carbon_executor.name is None

    @staticmethod
    def test_name_setter(carbon_executor):
        with pytest.raises(AttributeError) as ex:
            carbon_executor.name = 'null'
        assert 'You cannot set name for the executor.' in ex.value.args

    @staticmethod
    def test_execute_property(carbon_executor):
        assert carbon_executor.execute is None

    @staticmethod
    def tests_execute_setter(carbon_executor):
        with pytest.raises(AttributeError) as ex:
            carbon_executor.execute = 'null'
        assert 'You cannot set the execute to run.' in ex.value.args

    @staticmethod
    def test_hosts_property(carbon_executor):
        assert carbon_executor.hosts is None

    @staticmethod
    def test_hosts_setter(carbon_executor):
        with pytest.raises(AttributeError) as ex:
            carbon_executor.hosts = 'null'
        assert 'Hosts cannot be set once the object is created.' in \
               ex.value.args

    @staticmethod
    def test_get_mandatory_parameters(carbon_executor):
        data = carbon_executor.get_mandatory_parameters()
        assert isinstance(data, types.GeneratorType)

    @staticmethod
    def test_get_optional_parameters(carbon_executor):
        data = carbon_executor.get_optional_parameters()
        assert isinstance(data, types.GeneratorType)

    @staticmethod
    def test_get_all_parameters(carbon_executor):
        data = carbon_executor.get_all_parameters()
        assert isinstance(data, types.GeneratorType)

    @staticmethod
    @mock.patch.object(CarbonExecutor, 'get_all_parameters')
    def test_build_profile(mock_01, carbon_executor):
        mock_01.return_value = ('name',)
        execute = mock.MagicMock()
        profile = carbon_executor.build_profile(execute)
        assert isinstance(profile, dict)

class TestCarbonCorePlugins(object):

    @staticmethod
    def test_constructor(carbon_plugin):
        assert isinstance(carbon_plugin, CarbonPlugin)

    @staticmethod
    def test_contructor_provisioner_gw(provisioner_plugin):
        assert isinstance(provisioner_plugin, ProvisionerPlugin)

    @staticmethod
    def test_constructor_executor_gw(executor_plugin):
        assert isinstance(executor_plugin, ExecutorPlugin)

    @staticmethod
    def test_constructor_reporter_gw(importer_plugin):
        assert isinstance(importer_plugin, ImporterPlugin)

    @staticmethod
    def test_constructor_orchestrator_gw(orchestrator_plugin):
        assert isinstance(orchestrator_plugin, OrchestratorPlugin)

    @staticmethod
    def test_provisioner_gw_create(provisioner_plugin):
        with pytest.raises(NotImplementedError):
            provisioner_plugin.create()

    @staticmethod
    def test_provisioner_gw_delete(provisioner_plugin):
        with pytest.raises(NotImplementedError):
            provisioner_plugin.delete()

    @staticmethod
    def test_provisioner_gw_authenticate(provisioner_plugin):
        with pytest.raises(NotImplementedError):
            provisioner_plugin.authenticate()

    @staticmethod
    def test_importer_gw_aggregate(importer_plugin):
        with pytest.raises(NotImplementedError):
            importer_plugin.aggregate_artifacts()

    @staticmethod
    def test_importer_gw_push(importer_plugin):
        with pytest.raises(NotImplementedError):
            importer_plugin.import_artifacts()

    @staticmethod
    def test_importer_gw_cleanup(importer_plugin):
        with pytest.raises(NotImplementedError):
            importer_plugin.cleanup_artifacts()

    @staticmethod
    def test_executor_gw_run(executor_plugin):
        with pytest.raises(NotImplementedError):
            executor_plugin.run()

    @staticmethod
    def test_orchestrator_gw_run(orchestrator_plugin):
        with pytest.raises(NotImplementedError):
            orchestrator_plugin.run()