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
import os
from copy import deepcopy
from distutils import dir_util
from nose.tools import assert_is_instance, nottest

from carbon import __name__ as carbon_name
from carbon import Host
from carbon.constants import CARBON_ROOT
from carbon.core import LoggerMixin
from carbon.helpers import file_mgmt
from carbon.provisioners import OpenstackProvisioner

scenario_description = file_mgmt('r', 'assets/scenario.yaml')


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
    """Unit tests to test carbon provisioner ~ openstack."""

    _cp_scenario_description = dict(scenario_description)
    _parameters = _cp_scenario_description['provision'][0]
    _credentials = _cp_scenario_description.pop('credentials')[0]
    _parameters['provider_creds'] = {_credentials['name']: _credentials}
    _parameters_res2 = _cp_scenario_description['provision'][1]
    _parameters_res2['provider_creds'] = {_credentials['name']: _credentials}
    _base_path = os.path.join(CARBON_ROOT, "jobs")

    def setUp(self):
        """Tasks to be performed before each test case."""
        # Setup carbon logger
        LoggerMixin.create_carbon_logger(carbon_name, 'debug')

        # Call scrub_os_setup function
        scrub_os_setup(self._base_path, '5678')

    @nottest
    def test_instantiate_provisioner(self):
        """Test instantiating an OpenstackProvisioner class and
        verifying the object created is an instance of the
        OpenstackProvisioner class.
        """
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='5678')
        obj = OpenstackProvisioner(host.profile())
        assert_is_instance(obj, OpenstackProvisioner)

    @nottest
    def test_openstack_create_count_1(self):
        """Test LinchpinProvisioner rise/up method os_count 1
        Check result successful.
        """
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='5678')
        obj = OpenstackProvisioner(host.profile())
        obj.create()

    @nottest
    def test_openstack_delete_count_1(self):
        """Test LinchpinProvisioner rise/up method os_count 1
        Check result successful.
        """
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='5678')
        obj = OpenstackProvisioner(host.profile())
        obj.create()
        obj.delete()
