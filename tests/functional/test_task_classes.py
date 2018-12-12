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

from carbon.exceptions import CarbonOrchestratorError
from carbon.tasks import CleanupTask, ExecuteTask, OrchestrateTask, \
    ProvisionTask, ReportTask, ValidateTask

from carbon.core import CarbonProvisioner, ProvisionerPlugin
from carbon.provisioners import HostProvisioner, OpenstackLibCloudProvisioner
from carbon.provisioners.ext import OpenstackLibCloudProvisionerPlugin
from carbon.resources import Host



@pytest.fixture(scope='class')
def validate_task():
    return ValidateTask(resource=object)


@pytest.fixture(scope='class')
def report_task():
    return ReportTask(msg='report task')


@pytest.fixture(scope='class')
def execute_task():
    package = mock.MagicMock()
    package.executor = mock.MagicMock()
    return ExecuteTask(msg='execute task', package=package)


@pytest.fixture(scope='class')
def orchestrate_task():
    package = mock.MagicMock()
    package.orchestrator = mock.MagicMock()
    return OrchestrateTask(msg='orchestrate task', package=package)


@pytest.fixture(scope='class')
def provision_task():
    host = mock.MagicMock()
    host.provisioner = mock.MagicMock()
    return ProvisionTask(msg='provision task', host=host)


@pytest.fixture(scope='class')
def cleanup_task():
    host = mock.MagicMock()
    package = mock.MagicMock()
    return CleanupTask(msg='cleanup task', host=host, package=package)


class TestValidateTask(object):
    @staticmethod
    def test_constructor(validate_task):
        assert isinstance(validate_task, ValidateTask)

    @staticmethod
    def test_run(validate_task):
        validate_task.resource = mock.MagicMock()
        validate_task.run()


class TestReportTask(object):
    @staticmethod
    def test_constructor(report_task):
        assert isinstance(report_task, ReportTask)

    @staticmethod
    def test_run(report_task):
        report_task.run()


class TestExecuteTask(object):
    @staticmethod
    def test_constructor(execute_task):
        assert isinstance(execute_task, ExecuteTask)

    @staticmethod
    def test_run(execute_task):
        execute_task.run()


class TestOrchestrateTask(object):
    @staticmethod
    def test_constructor(orchestrate_task):
        assert isinstance(orchestrate_task, OrchestrateTask)

    @staticmethod
    def test_run(orchestrate_task):
        orchestrate_task.run()


class TestProvisionTask(object):
    @staticmethod
    def test_constructor(provision_task):
        assert isinstance(provision_task, ProvisionTask)

    @staticmethod
    def test_run(provision_task):
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
        host = mock.MagicMock(spec=Host, is_static=False, provisioner_plugin=None, provisioner=CarbonProvisioner,
                              provider_params='test-provider-param')
        pt = ProvisionTask('provision task', host=host)
        assert pt.provision

    @staticmethod
    def test_create_with_provisioner_gateway():
        host = mock.MagicMock(spec=Host, is_static=False, provisioner_plugin=ProvisionerPlugin, provisioner=HostProvisioner,
                              provider_params='test-provider-param')
        pt = ProvisionTask('provision task', host=host)
        assert pt.provision


class TestCleanupTask(object):
    @staticmethod
    def test_constructor(cleanup_task):
        assert isinstance(cleanup_task, CleanupTask)

    @staticmethod
    def test_run(cleanup_task):
        cleanup_task.host.provisioner = mock.MagicMock()
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
    def test_run_cleanup_with_host_provisioner(mock_method, cleanup_task):
        host = mock.MagicMock(spec=Host, provisioner_plugin=None, provisioner=CarbonProvisioner,
                              provider_params='test-provider-param')
        cleanup_task.host = host
        mock_method.return_value = mock.MagicMock('Test Delete Success')
        cleanup_task.run()
        mock_method.assert_called()

    @staticmethod
    @mock.patch.object(HostProvisioner, 'delete')
    def test_run_cleanup_with_host_provisioner_plugin(mock_method, cleanup_task):
        host = mock.MagicMock(spec=Host, provisioner_plugin=ProvisionerPlugin, provisioner=HostProvisioner,
                              provider_params='test-provider-param')
        cleanup_task.host = host
        mock_method.return_value = mock.MagicMock('Test Delete Success')
        cleanup_task.run()
        mock_method.assert_called()

