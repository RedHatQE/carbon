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
import os
from copy import deepcopy
from nose.tools import assert_equal, assert_is_instance, assert_is_not_none
from nose.tools import assert_not_equal, assert_false, raises
from unittest import TestCase

try:
    from test.test_support import EnvironmentVarGuard
except ImportError:
    from test.support import EnvironmentVarGuard

from carbon import Carbon, Scenario, Host
from carbon.constants import PROVISIONERS
from carbon.helpers import file_mgmt
from carbon.providers import OpenstackProvider

scenario_description = file_mgmt('r', 'assets/scenario.yaml')
scenario_description_invalid = file_mgmt('r', 'assets/invalid_scenario.yaml')


class TestScenario(TestCase):
    """Unit tests to test carbon scenarios."""

    def setUp(self):
        self.env = EnvironmentVarGuard()
        self.env.set('CARBON_SETTINGS', os.path.join(os.getcwd(), 'assets/carbon.cfg'))
        self.cbn = Carbon(__name__)

    def test_new_scenario_from_yaml(self):
        """Test creating a new scenario object from a data structure read in
        from a yaml file.
        """
        self.cbn.scenario = Scenario(config=self.cbn.config, name='MyScenario')
        assert_is_instance(self.cbn.scenario, Scenario)
        assert_equal(len(self.cbn.scenario.hosts), 0)

    def test_new_attribute(self):
        """Test setting a new scenario object attribute."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        self.cbn.scenario.newattribute = 'value'
        assert_equal(self.cbn.scenario.newattribute, str('value'))


class TestHost(TestCase):
    """Unit tests to test carbon host."""

    _cp_scenario_description = dict(scenario_description)
    _cp_scenario_description_invalid = dict(scenario_description_invalid)
    _hosts_description = _cp_scenario_description.pop('provision')
    _hosts_description_invalid = _cp_scenario_description_invalid.pop('PROVISION')
    _invalid_parameters = _hosts_description_invalid[2]
    _parameters = _hosts_description[0]
    _parameters2 = _hosts_description[1]
    _parameters3 = _hosts_description[2]
    _credentials = _cp_scenario_description.pop('credentials')
    _parameters['provider_creds'] = _credentials
    _parameters3['provider_creds'] = _parameters2['provider_creds'] = _parameters['provider_creds']
    _invalid_parameters['provider_creds'] = _parameters['provider_creds']

    def setUp(self):
        self.env = EnvironmentVarGuard()
        self.env.set('CARBON_SETTINGS', os.path.join(os.getcwd(), 'assets/carbon.cfg'))
        self.cbn = Carbon(__name__)

    def test_instantiate_host(self):
        """Test instantiating a host class and verify the object created is
        an instance of the host class.
        """
        cp_parameters = deepcopy(self._parameters)
        host = Host(config=self.cbn.config, parameters=cp_parameters)
        assert_is_instance(host, Host)

    def test_set_name(self):
        """Test setting the host name when instantiating the host class."""
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('name')
        host = Host(config=self.cbn.config, name='client1', parameters=cp_parameters)
        assert_equal(host.name, 'client1')

    def test_set_random_name(self):
        """Test setting a random host name when no name declared for a host."""
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('name')
        host = Host(config=self.cbn.config, parameters=cp_parameters)
        assert_is_not_none(host.name)

    @raises(AttributeError)
    def test_update_name(self):
        """Test setting the host name after host class was instantiated. An
        exception will be raised since you cannot update the name after host
        object was created.
        """
        cp_parameters = deepcopy(self._parameters)
        host = Host(config=self.cbn.config, parameters=cp_parameters)
        host.name = 'my_machine1'

    def test_get_role(self):
        """Test getting the host role from created host object."""
        cp_parameters = deepcopy(self._parameters)
        host = Host(config=self.cbn.config, parameters=cp_parameters)
        assert_equal(host.role, 'w_client')

    @raises(AttributeError)
    def test_set_role(self):
        """Test setting the host role after host class was instantiated. An
        exception will be raised since you cannot update the role after host
        object was created.
        """
        cp_parameters = deepcopy(self._parameters)
        host = Host(config=self.cbn.config, parameters=cp_parameters)
        host.role = "client1"

    @raises(AttributeError)
    def test_set_provider(self):
        """Test setting the host provider after host class was instantiated.
        An exception will be raised since you cannot update the provider
        after host object was created.
        """
        cp_parameters = deepcopy(self._parameters)
        host = Host(config=self.cbn.config, parameters=cp_parameters)
        host.provider = 'openstack'

    def test_get_provider(self):
        """Test getting the host provider from created host object. It will
        check if the provider is an instance of the provider class.
        """
        cp_parameters = deepcopy(self._parameters)
        host = Host(config=self.cbn.config, parameters=cp_parameters)
        assert_is_instance(host.provider, OpenstackProvider)

    def test_set_provisioner_valid(self):
        """Test a valid setting of the provisioner.
        """
        cp_parameters = deepcopy(self._parameters)
        host = Host(config=self.cbn.config, parameters=cp_parameters)
        assert_equal(host.provisioner.__provisioner_name__, self._parameters["provisioner"])

    @raises(Exception)
    def test_set_provisioner_invalid(self):
        """Test an invalid setting of the provisioner.  The provisioner
        is still set to a valid provisioner, but rejects the input.
        """
        cp_parameters = deepcopy(self._invalid_parameters)
        host = Host(config=self.cbn.config, parameters=cp_parameters)

    def test_provisioner_notset(self):
        """Test not setting a provisioner.  The provisioner
        uses the constants to set the provisioner.
        """
        cp_parameters = deepcopy(self._parameters3)
        host = Host(config=self.cbn.config, parameters=cp_parameters)
        assert_is_not_none(host.provisioner)
        assert_false("provisioner" in self._parameters3)
        assert_equal(host.provisioner.__provisioner_name__, PROVISIONERS[self._parameters3["provider"]])

    @raises(AttributeError)
    def test_set_provisioner(self):
        """Test setting the host provisioner after host class was instantiated.
        An exception will be raised since you cannot update the provisioner
        after host object was created.
        """
        cp_parameters = deepcopy(self._parameters)
        host = Host(config=self.cbn.config, parameters=cp_parameters)
        host.provisioner = 'linchpin'

    @raises(Exception)
    def test_role_undeclared(self):
        """Test instantiating a host class with role undeclared. An exception
        will be raised.
        """
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('role')
        Host(config=self.cbn.config, parameters=cp_parameters)

    @raises(Exception)
    def test_provider_undeclared(self):
        """Test instantiating a host class with provider undeclared. An
        exception will be raised.
        """
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('provider')
        Host(config=self.cbn.config, parameters=cp_parameters)

    @raises(Exception)
    def test_invalid_provider(self):
        """Test instantiating a host class with an invalid provider. An
        exception will be raised.
        """
        cp_parameters = deepcopy(self._parameters)
        cp_parameters['provider'] = 'provider123'
        Host(config=self.cbn.config, parameters=cp_parameters)

    @raises(Exception)
    def test_provider_creds_undeclared(self):
        """Test instantiating a host class with provider credentials
        undeclared. An exception will be raised.
        """
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('provider_creds')
        Host(config=self.cbn.config, parameters=cp_parameters)

    @raises(Exception)
    def test_provider_miss_cred_param(self):
        """Test instantiating a host class with a mising key for provider
        credentials. An exception will be raised.
        """
        cp_parameters = deepcopy(self._parameters)
        cp_parameters['provider_creds'][cp_parameters['credential']].\
            pop('auth_url')
        Host(config=self.cbn.config, parameters=cp_parameters)

    @raises(Exception)
    def test_provider_miss_param(self):
        """Test instantiating a host class with a missing mandatory parameter
        for the provider. An exception will be raised.
        """
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('os_image')
        Host(config=self.cbn.config, parameters=cp_parameters)

    def test_profile(self):
        """Test creating a host profile data structure from the host object. It
        will check if the profile data structure is an dictionary.
        """
        cp_parameters = deepcopy(self._parameters)
        host = Host(config=self.cbn.config, parameters=cp_parameters)
        profile = host.profile()
        assert_is_instance(profile, dict)
