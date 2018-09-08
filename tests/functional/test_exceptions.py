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
    tests.test_exceptions

    Unit tests for testing carbon custom exceptions.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import pytest

from carbon.exceptions import CarbonError, CarbonTaskError, \
    CarbonResourceError, CarbonProvisionerError, CarbonProviderError, \
    CarbonOrchestratorError, HelpersError, LoggerMixinError, \
    CarbonActionError, CarbonExecuteError, CarbonHostError, CarbonReportError, \
    ScenarioError, BeakerProvisionerError, OpenstackProviderError, \
    OpenshiftProvisionerError, ArchiveArtifactsError


def test_carbon_error():
    with pytest.raises(CarbonError):
        raise CarbonError('error message')


def test_carbon_task_error():
    with pytest.raises(CarbonTaskError):
        raise CarbonTaskError('error message')


def test_carbon_resource_error():
    with pytest.raises(CarbonResourceError):
        raise CarbonResourceError('error message')


def test_carbon_provisioner_error():
    with pytest.raises(CarbonProvisionerError):
        raise CarbonProvisionerError('error message')


def test_carbon_provider_error():
    with pytest.raises(CarbonProviderError):
        raise CarbonProviderError('error message')


def test_carbon_orchestrator_error():
    with pytest.raises(CarbonOrchestratorError):
        raise CarbonOrchestratorError('error message')


def test_carbon_helpers_error():
    with pytest.raises(HelpersError):
        raise HelpersError('error message')


def test_carbon_logger_mixin_error():
    with pytest.raises(LoggerMixinError):
        raise LoggerMixinError('error message')


def test_carbon_action_error():
    with pytest.raises(CarbonActionError):
        raise CarbonActionError('error message')


def test_carbon_execute_error():
    with pytest.raises(CarbonExecuteError):
        raise CarbonExecuteError('error message')


def test_carbon_host_error():
    with pytest.raises(CarbonHostError):
        raise CarbonHostError('error message')


def test_carbon_report_error():
    with pytest.raises(CarbonReportError):
        raise CarbonReportError('error message')


def test_scenario_error():
    with pytest.raises(ScenarioError):
        raise ScenarioError('error message')


def test_beaker_provisioner_error():
    with pytest.raises(BeakerProvisionerError):
        raise BeakerProvisionerError('error message')


def test_openstack_provider_error():
    with pytest.raises(OpenstackProviderError):
        raise OpenstackProviderError('error message')


def test_openshift_provisioner_error():
    with pytest.raises(OpenshiftProvisionerError):
        raise OpenshiftProvisionerError('error message')


def test_archive_artifacts_error():
    with pytest.raises(ArchiveArtifactsError):
        raise ArchiveArtifactsError('error message')
