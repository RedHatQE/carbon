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
    Unit tests to test carbon resources.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from copy import deepcopy
from nose.tools import assert_equal, assert_is_instance, assert_is_not_none
from nose.tools import raises

from carbon import Scenario, Host
from carbon.helpers import file_mgmt
from carbon.providers import OpenstackProvider

scenario_description = file_mgmt('r', 'assets/scenario.yaml')


class TestScenario(object):
    """Unit tests to test carbon scenarios."""

    @staticmethod
    def test_new_scenario_from_yaml():
        scenario = Scenario(scenario_description)
        assert isinstance(scenario, Scenario)
        assert len(scenario.hosts) == 0

    @staticmethod
    def test_new_attribute():
        scenario = Scenario(scenario_description)
        scenario.newattribute = 'value'
        assert scenario.newattribute == str('value')


class TestHost(object):
    """Unit tests to test carbon host."""

    _cp_scenario_description = dict(scenario_description)
    _parameters = _cp_scenario_description.pop('provision')[0]
    _credentials = _cp_scenario_description.pop('credentials')[0]
    _parameters['provider_creds'] = {_credentials.pop('name'): _credentials}

    def test_instantiate_host(self):
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        assert_is_instance(host, Host)

    def test_set_name(self):
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('name')
        host = Host('client1', parameters=cp_parameters, scenario_id='1234')
        assert_equal(host.name, 'client1')

    def test_set_random_name(self):
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('name')
        host = Host(parameters=cp_parameters, scenario_id='1234')
        assert_is_not_none(host.name)

    @raises(AttributeError)
    def test_update_name(self):
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        host.name = 'my_machine1'

    def test_get_role(self):
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        assert_equal(host.role, 'w_client')

    @raises(AttributeError)
    def test_set_role(self):
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        host.role = "client1"

    def test_get_scenario_id(self):
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        assert_equal(host.scenario_id, '1234')

    @raises(AttributeError)
    def test_set_scenario_id(self):
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        host.scenario_id = '1234'

    @raises(AttributeError)
    def test_set_provider(self):
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        host.provider = 'openstack'

    def test_get_provider(self):
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        assert_is_instance(host.provider, OpenstackProvider)

    @raises(Exception)
    def test_role_undeclared(self):
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('role')
        Host(parameters=cp_parameters, scenario_id='1234')

    @raises(Exception)
    def test_provider_undeclared(self):
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('provider')
        Host(parameters=cp_parameters, scenario_id='1234')

    @raises(Exception)
    def test_invalid_provider(self):
        cp_parameters = deepcopy(self._parameters)
        cp_parameters['provider'] = 'provider123'
        Host(parameters=cp_parameters, scenario_id='1234')

    @raises(Exception)
    def test_provider_creds_undeclared(self):
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('provider_creds')
        Host(parameters=cp_parameters, scenario_id='1234')

    @raises(Exception)
    def test_provider_miss_cred_param(self):
        cp_parameters = deepcopy(self._parameters)
        cp_parameters['provider_creds'][cp_parameters['credential']].\
            pop('auth_url')
        Host(parameters=cp_parameters, scenario_id='1234')

    @raises(Exception)
    def test_provider_miss_param(self):
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('os_image')
        Host(parameters=cp_parameters, scenario_id='1234')

    def test_profile(self):
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        profile = host.profile()
        assert_is_instance(profile, dict)
