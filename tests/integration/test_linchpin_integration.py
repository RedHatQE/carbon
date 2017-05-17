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
    Unit tests to test carbon linchpin provisioner module.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from carbon.provisioners import LinchpinProvisioner
from carbon import Scenario, Host
from carbon.helpers import file_mgmt
from carbon.constants import CARBON_ROOT
from copy import deepcopy
from distutils import dir_util
from nose.tools import assert_equal, assert_is_instance, assert_is_not_none
from nose.tools import raises, assert_raises_regexp
import os
import shutil

scenario_description = file_mgmt('r', 'assets/scenario.yaml')


def scrub_lp_setup(base_dir, ws_dir, ws_subdir=""):
    """ Scrub Linch-pin configuration setup to desired stage
    before running test. Remove passed workspace directory if exists 
    Return full workspace path 
    """
    workspace = os.path.join(base_dir, ws_dir)
    deldir = os.path.join(workspace, ws_subdir)
    if os.path.exists(deldir):
        dir_util.remove_tree(deldir)
    return workspace


class TestLinchpinProvisionerIntegration(object):

    _cp_scenario_description = dict(scenario_description)
    _parameters = _cp_scenario_description['provision'][0]
    _credentials = _cp_scenario_description.pop('credentials')[0]
    _parameters['provider_creds'] = {_credentials['name']: _credentials}
    _parameters_res2 = _cp_scenario_description['provision'][1]
    _parameters_res2['provider_creds'] = {_credentials['name']: _credentials}
    _base_path = os.path.join(CARBON_ROOT, "jobs")

    def test_linchpin_rise_count_1(self):
        """Test LinchpinProvisioner rise/up method os_count 1
        Check result successful.  
        """
        scrub_lp_setup(self._base_path, '1234')
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        lp = LinchpinProvisioner(host.profile())
        lp.create()

    def test_linchpin_rise_count_3(self):
        """Test LinchpinProvisioner rise/up method os_count > 1
        Check result successful.  
        """
        scrub_lp_setup(self._base_path, '1234')
        cp_parameters = deepcopy(self._parameters_res2)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        lp = LinchpinProvisioner(host.profile())
        lp.create()

    def test_linchpin_rise_error(self):
        """Test LinchpinProvisioner rise/up method
        Use Invalid password for auth. Linchpin returns error.
        Check results show error.  
        """
        scrub_lp_setup(self._base_path, '1234')
        parameters_err = deepcopy(self._parameters_res2)
        parameters_err['provider_creds'][self._parameters_res2['credential']]['password'] = 'laskdjls'
        cp_parameters = deepcopy(parameters_err)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        lp = LinchpinProvisioner(host.profile())
        with assert_raises_regexp(Exception, "Failed to provision resources. Check logs or job resources status's"):
            lp.create()

    def test_linchpin_drop(self):
        """Test LinchpinProvisioner delete/teardown method
        Check result successful.  
        """
        scrub_lp_setup(self._base_path, '1234')
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        lp = LinchpinProvisioner(host.profile())
        lp.delete()

    def test_linchpin_drop_error(self):
        """Test LinchpinProvisioner drop method
        Use Invalid password for auth. Linchpin returns error.
        Check results show error.  
        """
        scrub_lp_setup(self._base_path, '1234')
        parameters_err = deepcopy(self._parameters_res2)
        parameters_err['provider_creds'][self._parameters_res2['credential']]['password'] = 'laskdjls'
        parameters_err['provider_creds'][self._parameters_res2['credential']]['password'] = 'laskdjls'
        cp_parameters = deepcopy(parameters_err)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        lp = LinchpinProvisioner(host.profile())
        with assert_raises_regexp(
                Exception,
                "Failed to tear down all provisioned resources. Check logs or job resources status's"):
            lp.delete()

