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
    Unit tests to test carbon openstack provisioner module.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from carbon.provisioners import OpenstackProvisioner
from carbon import Scenario, Host
from carbon.helpers import file_mgmt
from carbon.constants import CARBON_ROOT
from copy import deepcopy
from distutils import dir_util
from nose.tools import assert_equal, assert_is_instance, assert_is_not_none
from nose.tools import raises, assert_raises_regexp, nottest
import os
import shutil

scenario_description = file_mgmt('r', 'assets/scenario.yaml')


@nottest
def scrub_os_setup(base_dir, ws_dir, ws_subdir=""):
    """ Scrub Openstack configuration setup to desired stage
    before running test. Remove passed workspace directory if exists 
    Return full workspace path 
    """
    workspace = os.path.join(base_dir, ws_dir)
    deldir = os.path.join(workspace, ws_subdir)
    if os.path.exists(deldir):
        dir_util.remove_tree(deldir)
    return workspace


class TestOpenstackProvisioner(object):

    _cp_scenario_description = dict(scenario_description)
    _parameters = _cp_scenario_description['provision'][0]
    _credentials = _cp_scenario_description.pop('credentials')[0]
    _parameters['provider_creds'] = {_credentials['name']: _credentials}
    _parameters_res2 = _cp_scenario_description['provision'][1]
    _parameters_res2['provider_creds'] = {_credentials['name']: _credentials}
    _base_path = os.path.join(CARBON_ROOT, "jobs")

    @nottest
    def test_preparation(self):
        pass

    @nottest
    def test_instantiate_openstackprovisioner(self):
        """Test instantiating an OpenstackProvisioner class and
        verifying the object created is an instance of the 
        OpenstackProvisioner class.
        """
        scrub_os_setup(self._base_path, '5678')
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='5678')
        os = OpenstackProvisioner(host.profile())
        assert_is_instance(os, OpenstackProvisioner)

    @nottest
    def test_openstack_create_count_1(self):
        """Test LinchpinProvisioner rise/up method os_count 1
        Check result successful.  
        """
        scrub_os_setup(self._base_path, '5678')
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='5678')
        os = OpenstackProvisioner(host.profile())
        os.create()

    @nottest
    def test_openstack_delete_count_1(self):
        """Test LinchpinProvisioner rise/up method os_count 1
        Check result successful.  
        """
        scrub_os_setup(self._base_path, '5678')
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='5678')
        os = OpenstackProvisioner(host.profile())
        os.create()
        os.delete()
