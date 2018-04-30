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
from unittest import TestCase

import os
from nose.tools import assert_equal, assert_is_instance, assert_is_not_none
from nose.tools import assert_false, raises

try:
    from test.test_support import EnvironmentVarGuard
except ImportError:
    from test.support import EnvironmentVarGuard

from carbon import Carbon, Scenario, Host
from carbon._compat import string_types
from carbon.constants import PROVISIONERS
from carbon.core import CarbonError, CarbonResource
from carbon.helpers import file_mgmt, template_render
from carbon.providers import OpenstackProvider
from carbon.resources import Action, Execute, Report
from carbon.resources.scenario import ScenarioError

scenario_description = file_mgmt('r', 'assets/scenario.yaml')
scenario_description_invalid = file_mgmt('r', 'assets/invalid_scenario.yaml')


class TestScenario(TestCase):
    """Unit tests to test carbon scenarios."""

    def setUp(self):
        self.env = EnvironmentVarGuard()
        self.env.set('CARBON_SETTINGS', os.path.join(os.getcwd(), 'assets/carbon.cfg'))
        self.cbn = Carbon(__name__, assets_path="assets")

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

    def test_copy_assets(self):
        """Test copying an asset into the data folder."""
        scenario_data = open("assets/openshift_assets.yaml")
        self.cbn.load_from_yaml(scenario_data)
        assert_equal(len(self.cbn.scenario.get_assets_list()), 1)
        self.cbn._copy_assets()
        assert_equal(os.path.exists(os.path.join(self.cbn.assets_path, "mytemplate.yaml")), 1)

    @raises(IOError)
    def test_copy_assets_invalid(self):
        """Test assets defined, but not set in the assets path."""
        scenario_data = open("assets/openshift_invalid_assets.yaml")
        self.cbn.load_from_yaml(scenario_data)
        assert_equal(len(self.cbn.scenario.get_assets_list()), 1)
        self.cbn._copy_assets()

    def test_copy_assets_no_assets(self):
        """Test assets defined, but not set in the assets path."""
        scenario_data = open("assets/scenario.yaml")
        self.cbn.load_from_yaml(scenario_data)
        assert_equal(len(self.cbn.scenario.get_assets_list()), 0)
        self.cbn._copy_assets()

    def test_get_data_folder(self):
        """Test getting data folder for carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        assert_is_instance(self.cbn.scenario.data_folder, string_types)

    @raises(ValueError)
    def test_set_data_folder(self):
        """Test setting data folder for carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        self.cbn.scenario.data_folder = '/tmp/data_folder'

    def test_get_hosts(self):
        """Test getting hosts for carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        assert_is_instance(self.cbn.scenario.hosts, list)

    @raises(ValueError)
    def test_set_hosts(self):
        """Test setting hosts for the carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        self.cbn.scenario.hosts = ['host1', 'host2']

    @raises(ValueError)
    def test_add_invalid_host(self):
        """Test adding an invalid host for the carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        self.cbn.scenario.add_hosts(CarbonResource())

    def test_add_valid_host(self):
        """Test adding a valid host for the carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")

        _cp_scenario_description = dict(scenario_description)
        _hosts_description = _cp_scenario_description.pop('provision')[0]
        _hosts_description['provider_creds'] = _cp_scenario_description.pop('credentials')
        host = Host(config=self.cbn.config, parameters=_hosts_description)
        self.cbn.scenario.add_hosts(host)
        assert_equal(len(self.cbn.scenario.hosts), 1)

    @raises(ValueError)
    def test_set_credentials(self):
        """Test setting credentials for the carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        self.cbn.scenario.credentials = {'user': 'user', 'passwd': 'passwd'}

    def test_get_actions(self):
        """Test getting actions for the carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        assert_is_instance(self.cbn.scenario.actions, list)

    @raises(ValueError)
    def test_set_actions(self):
        """Test setting actions for the carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        self.cbn.scenario.actions = ['action1', 'action2']

    @raises(ValueError)
    def test_add_invalid_action(self):
        """Test adding an invalid action for the carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        self.cbn.scenario.add_actions(CarbonResource())

    def test_add_valid_action(self):
        """Test adding a valid action for the carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        self.cbn.scenario.add_actions(Action(
            name='foo', parameters=dict(hosts=[])))
        assert_equal(len(self.cbn.scenario.actions), 1)

    def test_get_executes(self):
        """Test getting executes for the carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        assert_is_instance(self.cbn.scenario.executes, list)

    @raises(ValueError)
    def test_set_executes(self):
        """Test setting executes for the carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        self.cbn.scenario.executes = ['execute1', 'execute2']

    @raises(ValueError)
    def test_add_invalid_executes(self):
        """Test adding an invalid executes for the carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        self.cbn.scenario.add_executes(CarbonResource())

    def test_add_valid_executes(self):
        """Test adding a valid executes for the carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        self.cbn.scenario.add_executes(Execute())
        assert_equal(len(self.cbn.scenario.executes), 1)

    def test_get_reports(self):
        """Test getting reports for the carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        assert_is_instance(self.cbn.scenario.reports, list)

    @raises(ValueError)
    def test_set_reports(self):
        """Test setting reports for the carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        self.cbn.scenario.reports = ['report1', 'report2']

    @raises(ValueError)
    def test_add_invalid_reports(self):
        """Test adding an invalid reports for the carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        self.cbn.scenario.add_reports(CarbonResource())

    def test_add_valid_reports(self):
        """Test adding a valid reports for the carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        self.cbn.scenario.add_reports(Report())
        assert_equal(len(self.cbn.scenario.reports), 1)

    @raises(ValueError)
    def test_add_invalid_resource(self):
        """Test adding an invalid resource for the carbon scenario."""
        self.cbn.scenario = Scenario(config=self.cbn.config, name="MyScenario")
        self.cbn.scenario.add_resource(CarbonResource())

    def test_validate_valid_scenario_yaml(self):
        """Test validating a valid carbon scenario yaml."""
        scenario_data = template_render("assets/scenario.yaml", os.environ)
        self.cbn.load_from_yaml(scenario_data)
        self.cbn.scenario.validate()

    @raises(CarbonError)
    def test_validate_invalid_scenario_yaml(self):
        """Test validating an invalid carbon scenario yaml."""
        scenario_data = template_render("assets/invalid_scenario.yaml", os.environ)
        self.cbn.load_from_yaml(scenario_data)
        self.cbn.scenario.validate()

    def test_validate_yaml_after_substitution_pos(self):
        """Test loading an scenario that becomes valid only after substitution."""
        env = os.environ
        env["some_name"] = "mymachine"
        scenario_data = template_render("assets/invalid_scenario_substitute.yaml", env)
        self.cbn.load_from_yaml(scenario_data)
        self.cbn.scenario.validate()

    @raises(ScenarioError)
    def test_validate_yaml_after_substitution_neg(self):
        """Test loading an scenario that stays invalid after substitution."""
        env = os.environ
        env["some_name"] = "mymachine"
        scenario_data = template_render("assets/invalid_scenario_substitute_invalid.yaml", env)
        self.cbn.load_from_yaml(scenario_data)
        self.cbn.scenario.validate()

    def test_build_profile(self):
        """Test building a scenario profile with all its properties."""
        scenario_data = open("assets/scenario.yaml")
        self.cbn.load_from_yaml(scenario_data)
        assert_is_instance(self.cbn.scenario.profile(), dict)


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

    def test_host_asset(self):
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('name')
        host = Host(config=self.cbn.config, name='client1', parameters=cp_parameters)
        assert_equal(host.get_assets_list(), [])

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
        host.provisioner = 'openstack'

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
        """Test instantiating a host class with a missing key for provider
        credentials. An exception will be raised.
        """
        cp_parameters = deepcopy(self._parameters)
        cdata = next(i for i in cp_parameters['provider_creds'] if i['name']
                     == cp_parameters['credential'])
        cdata.pop('auth_url')
        cp_parameters['provider_creds'] = [cdata]
        Host(config=self.cbn.config, parameters=cp_parameters)

    @raises(Exception)
    def test_host_missing_credentials(self):
        """Test instantiating a host class with credential undeclared. An
        exception will be raised.
        """
        cp_parameters = deepcopy(self._parameters)
        cp_parameters.pop('credential')
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
