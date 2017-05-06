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
        """Test creating a new scenario object from a data structure read in
        from a yaml file.
        """
        scenario = Scenario(scenario_description)
        assert_is_instance(scenario, Scenario)
        assert_equal(len(scenario.hosts), 0)

    @staticmethod
    def test_new_attribute():
        """Test setting a new scenario object attribute."""
        scenario = Scenario(scenario_description)
        scenario.newattribute = 'value'
        assert_equal(scenario.newattribute, str('value'))


class TestHost(object):
    """Unit tests to test carbon host."""

    _cp_scenario_description = dict(scenario_description)
    _parameters = _cp_scenario_description.pop('provision')[0]
    _credentials = _cp_scenario_description.pop('credentials')[0]
    _parameters['provider_creds'] = {_credentials.pop('name'): _credentials}

    def test_instantiate_host(self):
        """Test instantiating a host class and verify the object created is
        an instance of the host class.
        """
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        assert_is_instance(host, Host)

    def test_set_name(self):
        """Test setting the host name when instantiating the host class."""
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('name')
        host = Host('client1', parameters=cp_parameters, scenario_id='1234')
        assert_equal(host.name, 'client1')

    def test_set_random_name(self):
        """Test setting a random host name when no name declared for a host."""
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('name')
        host = Host(parameters=cp_parameters, scenario_id='1234')
        assert_is_not_none(host.name)

    @raises(AttributeError)
    def test_update_name(self):
        """Test setting the host name after host class was instantiated. An
        exception will be raised since you cannot update the name after host
        object was created.
        """
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        host.name = 'my_machine1'

    def test_get_role(self):
        """Test getting the host role from created host object."""
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        assert_equal(host.role, 'w_client')

    @raises(AttributeError)
    def test_set_role(self):
        """Test setting the host role after host class was instantiated. An
        exception will be raised since you cannot update the role after host
        object was created.
        """
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        host.role = "client1"

    def test_get_scenario_id(self):
        """Test geting the host scenario id from created host object."""
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        assert_equal(host.scenario_id, '1234')

    @raises(AttributeError)
    def test_set_scenario_id(self):
        """Test setting the host scenario id after host class was instaniated.
        An exception will be raised since you cannot update the scenario id
        after host object was created.
        """
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        host.scenario_id = '1234'

    @raises(AttributeError)
    def test_set_provider(self):
        """Test setting the host provider after host class was instantiated.
        An exception will be raised since you cannot update the provider
        after host object was created.
        """
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        host.provider = 'openstack'

    def test_get_provider(self):
        """Test getting the host provider from created host object. It will
        check if the provider is an instance of the provider class.
        """
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        assert_is_instance(host.provider, OpenstackProvider)

    @raises(Exception)
    def test_role_undeclared(self):
        """Test instantiating a host class with role undeclared. An exception
        will be raised.
        """
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('role')
        Host(parameters=cp_parameters, scenario_id='1234')

    @raises(Exception)
    def test_provider_undeclared(self):
        """Test instantiating a host class with provider undeclared. An
        exception will be raised.
        """
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('provider')
        Host(parameters=cp_parameters, scenario_id='1234')

    @raises(Exception)
    def test_invalid_provider(self):
        """Test instantiating a host class with an invalid provider. An
        exception will be raised.
        """
        cp_parameters = deepcopy(self._parameters)
        cp_parameters['provider'] = 'provider123'
        Host(parameters=cp_parameters, scenario_id='1234')

    @raises(Exception)
    def test_provider_creds_undeclared(self):
        """Test instantiating a host class with provider credentials
        undeclared. An exception will be raised.
        """
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('provider_creds')
        Host(parameters=cp_parameters, scenario_id='1234')

    @raises(Exception)
    def test_provider_miss_cred_param(self):
        """Test instantiating a host class with a mising key for provider
        credentials. An exception will be raised.
        """
        cp_parameters = deepcopy(self._parameters)
        cp_parameters['provider_creds'][cp_parameters['credential']].\
            pop('auth_url')
        Host(parameters=cp_parameters, scenario_id='1234')

    @raises(Exception)
    def test_provider_miss_param(self):
        """Test instantiating a host class with a missing mandatory parameter
        for the provider. An exception will be raised.
        """
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('os_image')
        Host(parameters=cp_parameters, scenario_id='1234')

    def test_profile(self):
        """Test creating a host profile data structure from the host object. It
        will check if the profile data structure is an dictionary.
        """
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        profile = host.profile()
        assert_is_instance(profile, dict)
