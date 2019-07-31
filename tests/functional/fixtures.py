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
import os

import pytest
from carbon.resources import Action, Execute, Asset, Report, Scenario
from carbon.utils.config import Config
from carbon._compat import ConfigParser

os.environ['CARBON_SETTINGS'] = '../assets/carbon.cfg'


@pytest.fixture
def config():
    config_file = '../assets/carbon.cfg'
    cfgp = ConfigParser()
    cfgp.read(config_file)
    if cfgp.get('feature_toggles:host','plugin_implementation') != 'False':
        cfgp.set('feature_toggles:host','plugin_implementation','False')
        with open(config_file, 'w') as cf:
            cfgp.write(cf)
    if cfgp.get('task_concurrency','provision') != 'False':
        cfgp.set('task_concurrency','provision','False')
        with open(config_file, 'w') as cf:
            cfgp.write(cf)
    config = Config()
    config.load()
    return config


@pytest.fixture
def default_host_params():
    return dict(
        role='client',
        provider=dict(
            name='openstack',
            credential='openstack',
            image='image',
            flavor='small',
            networks=['network']
        )
    )


@pytest.fixture
def scenario_resource():
    return Scenario(config=Config(), parameters={'k': 'v'})

@pytest.fixture
def scenario_resource1(config):
    return Scenario(config=config, parameters={'k': 'v'})


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
def host(default_host_params, config):
    return Asset(
        name='host01',
        config=config,
        parameters=copy.deepcopy(default_host_params)
    )


@pytest.fixture
def asset1(default_host_params, config):
    return Asset(
        name='host_0',
        config=config,
        parameters=copy.deepcopy(default_host_params)
    )

@pytest.fixture
def asset2(default_host_params, config):
    param =copy.deepcopy(default_host_params)
    param.update(role='test')
    return Asset(
        name='host_1',
        config=config,
        parameters=param
    )

@pytest.fixture
def asset3(default_host_params, config):
    param =copy.deepcopy(default_host_params)
    param.pop('role')
    param.update(groups='group_test')
    return Asset(
        name='host_3',
        config=config,
        parameters=param
    )

@pytest.fixture
def action1():
    return Action(
        name='action',
        parameters=dict(
            description='description',
            hosts=['host'],
            orchestrator='ansible'
        )
    )


@pytest.fixture
def execute1():
    params = dict(description='description', hosts='test', executor='runner')
    return Execute(name='execute1', parameters=params)

@pytest.fixture
def execute2():
    params = dict(description='description', hosts='group_test', executor='runner')
    return Execute(name='execute2', parameters=params)


@pytest.fixture
def scenario1(asset1, action1, scenario_resource1, execute1):
    scenario_resource1.add_assets(asset1)
    scenario_resource1.add_actions(action1)
    scenario_resource1.add_executes(execute1)
    return scenario_resource1


@pytest.fixture
def execute_resource():
    params = dict(description='description', hosts='host01', executor='runner')
    return Execute(name='execute', parameters=params)


@pytest.fixture
def report_resource(config):
    params = dict(description='description', executes='execute',
                  provider=dict(name='polarion',
                                credential='polarion'
                                ))
    return Report(name='text.xml', parameters=params, config=config)


@pytest.fixture
def scenario(action_resource, host, execute_resource, report_resource,
             scenario_resource):
    scenario_resource.add_assets(host)
    scenario_resource.add_actions(action_resource)
    scenario_resource.add_executes(execute_resource)
    scenario_resource.add_reports(report_resource)
    return scenario_resource


@pytest.fixture
def master_child_scenario(action_resource, host, execute_resource, report_resource,
                          scenario_resource, default_host_params, config):
    child_scenario = Scenario(config=Config(), parameters={'k': 'v'})
    host2 = Asset(
        name='host02',
        config=config,
        parameters=copy.deepcopy(default_host_params)
    )
    execute_res2 = Execute(name='execute02', parameters=dict(description='description', hosts='host02', executor='runner'))
    child_scenario.add_assets(host2)
    child_scenario.add_executes(execute_res2)
    scenario_resource.add_child_scenario(child_scenario)
    scenario_resource.add_assets(host)
    scenario_resource.add_actions(action_resource)
    scenario_resource.add_executes(execute_resource)
    scenario_resource.add_reports(report_resource)
    return scenario_resource
