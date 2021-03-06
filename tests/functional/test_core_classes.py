# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Red Hat, Inc.
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

    :copyright: (c) 2020 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import copy
import random
import time
import types
import os
import glob

import mock
import pytest

from carbon.core import CarbonOrchestrator, CarbonProvider, \
    CarbonResource, CarbonTask, LoggerMixin, TimeMixin, CarbonExecutor, \
    CarbonPlugin, ProvisionerPlugin, ExecutorPlugin, ImporterPlugin, OrchestratorPlugin, FileLockMixin, \
    Inventory, NotificationPlugin
from carbon.resources import Asset
from carbon.provisioners import AssetProvisioner
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
    return AssetProvisioner(host)


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


@pytest.fixture
def provisioner_plugin_no_provider(default_host_params):
    params = copy.deepcopy(default_host_params)
    params.pop('provider')
    host = Asset(name='test', parameters=params)
    return ProvisionerPlugin(host)


@pytest.fixture
def executor_plugin(execute_resource):
    return ExecutorPlugin(execute_resource)


@pytest.fixture
def importer_plugin(report_resource):
    return ImporterPlugin(report_resource)


@pytest.fixture()
def orchestrator_plugin(action_resource):
    return OrchestratorPlugin(action_resource)


@pytest.fixture(scope='class')
def lock_mixin():
    return FileLockMixin()


@pytest.fixture(scope='function')
def create_dummy_lock_file():
    open('/tmp/cbn_xyz.lock', 'w').close()


@pytest.fixture(scope='function')
def cleanup_lock(request):
    def cleanup():
        os.remove('/tmp/cbn_test.lock')
    request.addfinalizer(cleanup)


@pytest.fixture(scope='function')
def cleanup_unique_inv(request):
    def cleanup_unique():
        for u in glob.glob('/tmp/.results/inventory/unique*'):
            os.remove(u)
    request.addfinalizer(cleanup_unique)


@pytest.fixture(scope='function')
def cleanup_master(request):
    def cleanup_master():
        os.remove('/tmp/.results/inventory/master-xyz')
    request.addfinalizer(cleanup_master)


@pytest.fixture
def inv_host(default_host_params, config):
    params = copy.deepcopy(default_host_params)
    params.update(dict(ansible_params=dict(ansible_connection='local',
                                           ansible_ssh_private_key='keys/demo'),
                       ip_address=dict(public='10.10.10.10', private='192.168.10.10')))
    config['RESULTS_FOLDER'] = '/tmp/.results'
    return Asset(
        name='host01',
        config=config,
        parameters=params
    )


@pytest.fixture
def inventory(inv_host):
    inv_host.config['INVENTORY_FOLDER'] = '/tmp/.results/inventory'
    inventory = Inventory(inv_host.config, 'xyz')
    return inventory


@pytest.fixture
def notifier_plugin(notification_default_resource):
    return NotificationPlugin(notification_default_resource)


class TestFileLockMixin(object):
    @staticmethod
    def test_default_lock_file(lock_mixin):
        assert getattr(lock_mixin, 'lock_file') == '/tmp/cbn.lock'

    @staticmethod
    def test_default_lock_timeout(lock_mixin):
        assert getattr(lock_mixin, 'lock_timeout') == 120

    @staticmethod
    def test_default_lock_sleep(lock_mixin):
        assert getattr(lock_mixin, 'lock_sleep') == 5

    @staticmethod
    def test_setting_lock_file(lock_mixin):
        setattr(lock_mixin, 'lock_file', '/tmp/cbn_test.lock')
        assert getattr(lock_mixin, 'lock_file') == '/tmp/cbn_test.lock'


    @staticmethod
    def test_setting_lock_timeout(lock_mixin):
        setattr(lock_mixin, 'lock_timeout', 2)
        assert getattr(lock_mixin, 'lock_timeout') == 2

    @staticmethod
    def test_setting_lock_sleep(lock_mixin):
        setattr(lock_mixin, 'lock_sleep', 1)
        assert getattr(lock_mixin, 'lock_sleep') == 1

    @staticmethod
    def test_default_lock_cleanup(create_dummy_lock_file, lock_mixin):
        create_dummy_lock_file
        lock_mixin.cleanup_locks()
        assert not os.path.exists('/tmp/cbn_xyz.lock')

    @staticmethod
    def test_lock_aqcuire(lock_mixin):
        lock_mixin.acquire()
        assert os.path.exists('/tmp/cbn_test.lock')

    @staticmethod
    def test_lock_release(lock_mixin):
        lock_mixin.release()
        assert not os.path.exists('/tmp/cbn_test.lock')

    @staticmethod
    def test_lock_timeout(cleanup_lock, lock_mixin):
        lock_mixin.acquire()
        with pytest.raises(CarbonError):
            lock_mixin._check_and_sleep()
        cleanup_lock


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

    @staticmethod
    def test_get_labels(carbon_resource):
        assert carbon_resource.labels == []

    @staticmethod
    def test_set_labels_single_string(carbon_resource):
        """To test if single string values get set as an array"""
        setattr(carbon_resource, 'labels',' label1')
        assert carbon_resource.labels == ['label1']

    @staticmethod
    def test_set_labels(carbon_resource):
        """To test if comma separated string get set as an array"""
        setattr(carbon_resource, 'labels', 'label1,label2')
        assert carbon_resource.labels == ['label1', 'label2']


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
    def test_contructor_provisioner_plugin(provisioner_plugin):
        assert isinstance(provisioner_plugin, ProvisionerPlugin)

    @staticmethod
    def test_constructor_executor_plugin(executor_plugin):
        assert isinstance(executor_plugin, ExecutorPlugin)

    @staticmethod
    def test_constructor_reporter_plugin(importer_plugin):
        assert isinstance(importer_plugin, ImporterPlugin)

    @staticmethod
    def test_constructor_orchestrator_plugin(orchestrator_plugin):
        assert isinstance(orchestrator_plugin, OrchestratorPlugin)

    @staticmethod
    def test_provisioner_plugin_create(provisioner_plugin):
        with pytest.raises(NotImplementedError):
            provisioner_plugin.create()

    @staticmethod
    def test_provisioner_plugin_delete(provisioner_plugin):
        with pytest.raises(NotImplementedError):
            provisioner_plugin.delete()

    @staticmethod
    def test_provisioner_plugin_authenticate(provisioner_plugin):
        with pytest.raises(NotImplementedError):
            provisioner_plugin.authenticate()

    @staticmethod
    def test_provisioner_plugin_validate(provisioner_plugin):
        with pytest.raises(NotImplementedError):
            provisioner_plugin.validate()

    @staticmethod
    def test_importer_plugin_aggregate(importer_plugin):
        with pytest.raises(NotImplementedError):
            importer_plugin.aggregate_artifacts()

    @staticmethod
    def test_importer_plugin_import(importer_plugin):
        with pytest.raises(NotImplementedError):
            importer_plugin.import_artifacts()

    @staticmethod
    def test_importer_plugin_cleanup(importer_plugin):
        with pytest.raises(NotImplementedError):
            importer_plugin.cleanup_artifacts()

    @staticmethod
    def test_executor_plugin_run(executor_plugin):
        with pytest.raises(NotImplementedError):
            executor_plugin.run()

    @staticmethod
    def test_orchestrator_plugin_run(orchestrator_plugin):
        with pytest.raises(NotImplementedError):
            orchestrator_plugin.run()

    @staticmethod
    def test_notifier_plugin_notify(notifier_plugin):
        with pytest.raises(NotImplementedError):
            notifier_plugin.notify()

    @staticmethod
    def test_notifier_plugin_validate(notifier_plugin):
        with pytest.raises(NotImplementedError):
            notifier_plugin.validate()

    @staticmethod
    def test_notifier_plugin_get_config_params(notifier_plugin):
        assert not notifier_plugin.get_config_params()

    @staticmethod
    def test_notifier_plugin_get_credential_params(notifier_plugin):
        assert notifier_plugin.get_credential_params()


class TestInventory(object):

    @staticmethod
    def test_inventory(inventory):
        assert isinstance(inventory, Inventory)

    @staticmethod
    def test_create_master_inv(inventory, inv_host):
        # using inventory folder as the default created by carbon
        inventory.create_master(all_hosts=[inv_host])
        assert os.path.exists('/tmp/.results/inventory/master-xyz')

    @staticmethod
    def test_delete_master_inv(inventory):
        inventory.delete_master()
        assert not os.path.exists('/tmp/.results/inventory/master-xyz')

    @staticmethod
    def test_create_master_inv_err(inventory, inv_host, cleanup_master):
        inventory.create_master(all_hosts=[inv_host])
        with pytest.raises(Exception):
            inventory.create_master(all_hosts=[inv_host])
        cleanup_master

    @staticmethod
    def test_create_master_inv_warn(inventory):
        inventory.delete_master()

    @staticmethod
    def test_static_dir_create_master_inv(inv_host):
        inv_host_2 = Asset(name='dummy', parameters=dict(ip_address=['1.3.5.7', '2.4.5.6'],
                                                         role='dummy-role'))
        inv_host_3 = Asset(name='nummy', parameters=dict(ip_address='2.4.5.6',
                                                         role='nummy-role'))
        #inv = Inventory(inv_host.config['RESULTS_FOLDER'], inv_host.config['INVENTORY_FOLDER'], 'm6fmviqq51')
        inv = Inventory(inv_host.config, 'm6fmviqq51')
        inv.create_master(all_hosts=[inv_host, inv_host_2, inv_host_3] )
        assert os.path.exists('/tmp/inventory/master-m6fmviqq51')

    @staticmethod
    def test_static_dir_delete_master_inv(inv_host):
        #inv = Inventory(inv_host.config['RESULTS_FOLDER'], inv_host.config['INVENTORY_FOLDER'], 'm6fmviqq51')
        inv = Inventory(inv_host.config, 'm6fmviqq51')
        inv.delete_master()
        assert not os.path.exists('/tmp/inventory/master-m6fmviqq51')


    @staticmethod
    def test_create_master_inv_with_dump_layout(inv_host):
        # inv = Inventory(inv_host.config['RESULTS_FOLDER'], inv_host.config['INVENTORY_FOLDER'], 'm6fmviqq51',
        #                 inv_dump="""
        #                 [example]
        #                 10.0.154.237 hostname=10.0.154.237 ansible_ssh_private_key_file=/tmp/demo
        #
        #                 [all]
        #                 10.0.154.237 hostname=10.0.154.237 ansible_ssh_private_key_file=/tmp/demo
        #                 """)
        inv = Inventory(inv_host.config, 'm6fmviqq51',
                        inv_dump="""
                        [example]
                        10.0.154.237 hostname=10.0.154.237 ansible_ssh_private_key_file=/tmp/demo

                        [all]
                        10.0.154.237 hostname=10.0.154.237 ansible_ssh_private_key_file=/tmp/demo
                        """)
        inv.create_master(all_hosts=[])
        for i in glob.glob('/tmp/inventory/master-*'):
            with open(i) as f:
                data = f.read()
        assert data.find('example') != -1
        inv.delete_master()




