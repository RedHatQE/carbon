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
    tests.test_task_classes

    Unit tests for testing carbon task classes.

    :copyright: (c) 2020 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import mock
import pytest

from carbon.exceptions import CarbonOrchestratorError, CarbonImporterError, CarbonNotifierError
from carbon.tasks import CleanupTask, ExecuteTask, OrchestrateTask, \
    ProvisionTask, ReportTask, ValidateTask, NotificationTask
from carbon.core import ProvisionerPlugin
from carbon.provisioners import AssetProvisioner
from carbon.orchestrators import ActionOrchestrator
from carbon.resources import Asset, Action


@pytest.fixture(scope='class')
def validate_task():
    return ValidateTask(resource=object)


@pytest.fixture(scope='class')
def report_task():
    report = mock.MagicMock()
    with mock.patch('carbon.tasks.report.ArtifactImporter'):
        return ReportTask(msg='report task', package=report, name='Test-Report')


@pytest.fixture(scope='class')
def execute_task():
    package = mock.MagicMock()
    package.executor = mock.MagicMock()
    return ExecuteTask(msg='execute task', package=package, name='Test-Package')


@pytest.fixture(scope='class')
def orchestrate_task():
    package = mock.MagicMock()
    with mock.patch('carbon.tasks.orchestrate.ActionOrchestrator'):
        return OrchestrateTask(msg='orchestrate task', package=package, name='Test-Package')


@pytest.fixture(scope='class')
def provision_task():
    asset = mock.MagicMock()
    asset.provisioner = mock.MagicMock()
    return ProvisionTask(msg='provision task', asset=asset, name='Test-Asset')


@pytest.fixture(scope='class')
def cleanup_task():
    asset = mock.MagicMock()
    package = mock.MagicMock()
    return CleanupTask(msg='cleanup task', asset=asset, package=package)


@pytest.fixture(scope='class')
def notification_task():
    note = mock.MagicMock()
    package = mock.MagicMock()
    return NotificationTask(msg='triggering notification', resource=note)


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

    @staticmethod
    def test_run(provision_task):
        host_res = provision_task.run()
        assert host_res is None

    @staticmethod
    def test_run_with_provisioner(provision_task):
        mock_provisioner = mock.MagicMock(spec=AssetProvisioner,
                                          create=mock.MagicMock(return_value='Test Create Success'))
        provision_task.provision = True
        provision_task.provisioner = mock_provisioner
        host_res = provision_task.run()
        mock_provisioner.create.assert_called()
        assert host_res is 'Test Create Success'

    @staticmethod
    @mock.patch.object(ProvisionTask, 'get_formatted_traceback')
    def test_run_provision_failure(mock_method, provision_task):
        mock_method.return_value = 'Traceback'
        mock_provisioner = mock.MagicMock(spec=AssetProvisioner,
                                          create=mock.MagicMock(side_effect=CarbonOrchestratorError('e')))
        provision_task.provision = True
        provision_task.provisioner = mock_provisioner
        with pytest.raises(CarbonOrchestratorError):
            provision_task.run()


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

    # TODO this needs to be canged with asset provisioner changes
    # @staticmethod
    # @mock.patch.object(AssetProvisioner, 'delete')
    # def test_run_with_asset_provisioner_plugin(mock_method, cleanup_task):
    #     asset = mock.MagicMock(spec=Asset, provisioner_plugin=ProvisionerPlugin, provisioner=AssetProvisioner,
    #                           provider_params='test-provider-param')
    #     cleanup_task.asset = asset
    #     mock_method.return_value = mock.MagicMock('Test Delete Success')
    #     cleanup_task.run()
    #     mock_method.assert_called()


    @staticmethod
    @mock.patch.object(ProvisionerPlugin, 'delete')
    def test_run_cleanup_with_asset(mock_method, cleanup_task):
        asset = mock.MagicMock(spec=Asset, provisioner=ProvisionerPlugin,
                               is_static=False,
                               provider_params='test-provider-param')
        cleanup_task.asset = asset
        mock_method.return_value = mock.MagicMock('Test Delete Success')
        cleanup_task.run()
        mock_method.assert_called()

    @staticmethod
    @mock.patch.object(ProvisionerPlugin, 'delete')
    def test_run_cleanup_with_static_asset(mock_method, cleanup_task):
        asset = mock.MagicMock(spec=Asset, provisioner=ProvisionerPlugin,
                               is_static=True,
                               provider_params='test-provider-param')
        cleanup_task.asset = asset
        cleanup_task.run()
        mock_method.assert_not_called()


class TestNotificationTask(object):

    @staticmethod
    def test_constructor(notification_task):
        assert isinstance(notification_task, NotificationTask)

    @staticmethod
    def test_run(notification_task):
        notification_task.run()

    @staticmethod
    @mock.patch.object(NotificationTask, 'get_formatted_traceback')
    def test_run_notify_failure(mock_method, notification_task):
        mock_method.return_value = 'Traceback'
        mock_notifier = mock.MagicMock(notify=mock.MagicMock(side_effect=CarbonNotifierError('e')))
        notification_task.notifier = mock_notifier
        with pytest.raises(CarbonNotifierError):
            notification_task.run()