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
    tests.test_task_classes

    Unit tests for testing carbon task classes.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import mock
import pytest

from carbon.exceptions import CarbonOrchestratorError, CarbonImporterError
from carbon.tasks import CleanupTask, ExecuteTask, OrchestrateTask, \
    ProvisionTask, ReportTask, ValidateTask

from carbon.core import CarbonProvisioner, ProvisionerPlugin, Inventory
from carbon.provisioners import AssetProvisioner, OpenstackLibCloudProvisioner
from carbon.provisioners.ext import OpenstackLibCloudProvisionerPlugin
from carbon.resources import Asset



@pytest.fixture(scope='class')
def inventory():
    return mock.MagicMock(spec=Inventory, create_master=mock.MagicMock('success'))


@pytest.fixture(scope='class')
def validate_task():
    return ValidateTask(resource=object)


@pytest.fixture(scope='class')
def report_task():
    package = mock.MagicMock()
    package.importer = mock.MagicMock()
    return ReportTask(msg='report task', package=package, name='Test-Package')


@pytest.fixture(scope='class')
def execute_task():
    package = mock.MagicMock()
    package.executor = mock.MagicMock()
    return ExecuteTask(msg='execute task', package=package, name='Test-Package')


@pytest.fixture(scope='class')
def orchestrate_task():
    package = mock.MagicMock()
    package.orchestrator = mock.MagicMock()
    return OrchestrateTask(msg='orchestrate task', package=package, name='Test-Package')

# patching the __init__ for some reason patching out the Inventory
# class as a whole was not working in py 2 but works in py3
@pytest.fixture(scope='class')
@mock.patch('carbon.core.Inventory.__init__')
def provision_task(mock_inv):
    asset = mock.MagicMock()
    asset.provisioner = mock.MagicMock()
    mock_inv.return_value = None
    return ProvisionTask(msg='provision task', asset=asset, name='Test-Asset')


@pytest.fixture(scope='class')
def cleanup_task():
    asset = mock.MagicMock()
    package = mock.MagicMock()
    return CleanupTask(msg='cleanup task', asset=asset, package=package)


class TestValidateTask(object):
    @staticmethod
    def test_constructor(validate_task):
        assert isinstance(validate_task, ValidateTask)

    @staticmethod
    def test_run(validate_task):
        validate_task.resource = mock.MagicMock()
        validate_task.run()

    @staticmethod
    @mock.patch.object(ValidateTask, 'get_formatted_traceback')
    def test_run_execute_failure(mock_method, validate_task):
        mock_method.return_value = 'Traceback'
        mock_resource = mock.MagicMock(validate=mock.MagicMock(side_effect=CarbonOrchestratorError('e')))
        validate_task.resource = mock_resource
        with pytest.raises(CarbonOrchestratorError):
            validate_task.run()


class TestReportTask(object):
    @staticmethod
    def test_constructor(report_task):
        assert isinstance(report_task, ReportTask)

    @staticmethod
    def test_run(report_task):
        report_task.run()

    @staticmethod
    @mock.patch.object(ReportTask, 'get_formatted_traceback')
    def test_run_orchestrate_failure(mock_method, report_task):
        mock_method.return_value = 'Traceback'
        mock_importer = mock.MagicMock(import_artifacts=mock.MagicMock(side_effect=CarbonImporterError('e')))
        report_task.importer = mock_importer
        with pytest.raises(CarbonImporterError):
            report_task.run()


class TestExecuteTask(object):
    @staticmethod
    def test_constructor(execute_task):
        assert isinstance(execute_task, ExecuteTask)

    @staticmethod
    def test_run(execute_task):
        execute_task.run()

    @staticmethod
    @mock.patch.object(ExecuteTask, 'get_formatted_traceback')
    def test_run_execute_failure(mock_method, execute_task):
        mock_method.return_value = 'Traceback'
        mock_executor = mock.MagicMock(run=mock.MagicMock(side_effect=CarbonOrchestratorError('e')))
        execute_task.executor = mock_executor
        with pytest.raises(CarbonOrchestratorError):
            execute_task.run()

class TestOrchestrateTask(object):
    @staticmethod
    def test_constructor(orchestrate_task):
        assert isinstance(orchestrate_task, OrchestrateTask)

    @staticmethod
    def test_run(orchestrate_task):
        orchestrate_task.run()

    @staticmethod
    @mock.patch.object(OrchestrateTask, 'get_formatted_traceback')
    def test_run_orchestrate_failure(mock_method, orchestrate_task):
        mock_method.return_value = 'Traceback'
        mock_orchestrator = mock.MagicMock(run=mock.MagicMock(side_effect=CarbonOrchestratorError('e')))
        orchestrate_task.orchestrator = mock_orchestrator
        with pytest.raises(CarbonOrchestratorError):
            orchestrate_task.run()


class TestProvisionTask(object):
    @staticmethod
    def test_constructor(provision_task):
        assert isinstance(provision_task, ProvisionTask)

    # Need to replace the inventory object here
    # because I'm patching the Inventory __init__ in the
    # fixture
    @staticmethod
    def test_run(provision_task, inventory):
        provision_task.inv = inventory
        provision_task.run()

    @staticmethod
    def test_run_with_provisioner(provision_task):
        mock_provisioner = mock.MagicMock(spec=CarbonProvisioner, create=mock.MagicMock(return_value='Test Create Success'))
        provision_task.provision = True
        provision_task.provisioner = mock_provisioner
        provision_task.run()
        mock_provisioner.create.assert_called()

    @staticmethod
    def test_create_with_provisioner_no_plugin():
        asset = mock.MagicMock(spec=Asset, is_static=False, provisioner_plugin=None, provisioner=CarbonProvisioner,
                              provider_params='test-provider-param')
        with mock.patch('carbon.core.Inventory.__init__') as mock_inv:
            mock_inv.return_value = None
            pt = ProvisionTask('provision task', asset=asset)
            assert pt.provision

    @staticmethod
    def test_create_with_provisioner_plugin():
        asset = mock.MagicMock(spec=Asset, is_static=False, provisioner_plugin=ProvisionerPlugin, provisioner=AssetProvisioner,
                              provider_params='test-provider-param')
        with mock.patch('carbon.core.Inventory.__init__') as mock_inv:
            mock_inv.return_value = None
            pt = ProvisionTask('provision task', asset=asset)
            assert pt.provision

    @staticmethod
    @mock.patch.object(ProvisionTask, 'get_formatted_traceback')
    def test_run_provision_failure(mock_method, provision_task):
        mock_method.return_value = 'Traceback'
        mock_provisioner = mock.MagicMock(spec=CarbonProvisioner, create=mock.MagicMock(side_effect=CarbonOrchestratorError('e')))
        provision_task.provision = True
        provision_task.provisioner = mock_provisioner
        with pytest.raises(CarbonOrchestratorError):
            provision_task.run()

    @staticmethod
    def test_run_create_inventory_failure(host, inventory):
        inventory.create_master.side_effect = OSError('Failed to get permissions on the file')
        mock_provisioner = mock.MagicMock(spec=CarbonProvisioner, create=mock.MagicMock(return_value='Test Create Success'))
        with mock.patch('carbon.core.Inventory.__init__') as mock_inv:
            mock_inv.return_value = None
            pt = ProvisionTask(msg='Test Provision Task', asset=host)
            pt.provision = True
            pt.provisioner = mock_provisioner
            pt.inv = inventory
            with pytest.raises(OSError):
                pt.run()

class TestCleanupTask(object):
    @staticmethod
    def test_constructor(cleanup_task):
        assert isinstance(cleanup_task, CleanupTask)

    @staticmethod
    def test_run(cleanup_task):
        cleanup_task.asset.provisioner = mock.MagicMock()
        cleanup_task.run()

    @staticmethod
    @mock.patch.object(CleanupTask, '_get_orchestrator_instance')
    def test_run_cleanup_failure(mock_method, cleanup_task):
        orchestrator = mock.MagicMock()
        orchestrator.run.side_effect = CarbonOrchestratorError('e')
        mock_method.return_value = orchestrator
        cleanup_task.run()

    @staticmethod
    @mock.patch.object(CarbonProvisioner, 'delete')
    def test_run_cleanup_with_asset_provisioner(mock_method, cleanup_task):
        asset = mock.MagicMock(spec=Asset, provisioner_plugin=None, provisioner=CarbonProvisioner,
                              provider_params='test-provider-param')
        cleanup_task.asset = asset
        mock_method.return_value = mock.MagicMock('Test Delete Success')
        cleanup_task.run()
        mock_method.assert_called()

    @staticmethod
    @mock.patch.object(AssetProvisioner, 'delete')
    def test_run_cleanup_with_asset_provisioner_plugin(mock_method, cleanup_task):
        asset = mock.MagicMock(spec=Asset, provisioner_plugin=ProvisionerPlugin, provisioner=AssetProvisioner,
                              provider_params='test-provider-param')
        cleanup_task.asset = asset
        mock_method.return_value = mock.MagicMock('Test Delete Success')
        cleanup_task.run()
        mock_method.assert_called()

