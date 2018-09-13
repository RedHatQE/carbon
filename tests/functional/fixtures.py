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
    tests.fixtures

    Module containing commonly used pytest fixtures.

    How to add a new common fixture for use by all pytests?
        1. Add your fixture to this module
        2. Import the fixture in the conftest module
        3. Inside your test module, you will be able to access the fixture
        (no need to import fixture - conftest handles everything)

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import copy

import pytest
from carbon.resources import Action, Execute, Host, Report, Scenario
from carbon.utils.config import Config


@pytest.fixture
def default_host_params():
    return dict(
        role='client',
        provider='openstack',
        credential='openstack',
        provider_creds=[
            {'name': 'openstack', 'auth_url': 'url', 'username': 'user',
             'password': 'password', 'tenant_name': 'tenant'}
        ],
        os_flavor='small',
        os_networks='network',
        os_image='image'
    )


@pytest.fixture
def scenario_resource():
    return Scenario(config=Config(), parameters={'k': 'v'})


@pytest.fixture
def action_resource():
    return Action(
        name='action',
        parameters=dict(
            description='description',
            hosts=['host01'],
            orchestrator='ansible'
        )
    )


@pytest.fixture
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


@pytest.fixture
def host(default_host_params):
    return Host(
        name='host01',
        config={'DATA_FOLDER': '/tmp', 'WORKSPACE': '/tmp/ws'},
        parameters=copy.deepcopy(default_host_params)
    )


@pytest.fixture
def execute_resource():
    params = dict(description='description', hosts='host01', executor='runner')
    return Execute(name='execute', parameters=params)


@pytest.fixture
def report_resource():
    params = dict(key='value')
    return Report(parameters=params)


@pytest.fixture
def scenario(action_resource, host, execute_resource, report_resource,
             scenario_resource):
    scenario_resource.add_hosts(host)
    scenario_resource.add_actions(action_resource)
    scenario_resource.add_executes(execute_resource)
    scenario_resource.add_reports(report_resource)
    return scenario_resource
