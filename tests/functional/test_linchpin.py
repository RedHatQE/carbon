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
import os
from copy import deepcopy
from distutils import dir_util
from unittest import TestCase

try:
    from test.test_support import EnvironmentVarGuard
except ImportError:
    from test.support import EnvironmentVarGuard

from carbon import Host
from carbon.constants import CARBON_ROOT
from carbon.helpers import file_mgmt
# from carbon.provisioners import LinchpinProvisioner

from nose.tools import assert_equal, assert_is_instance
from nose.tools import assert_raises_regexp, nottest


scenario_description = file_mgmt('r', 'assets/scenario.yaml')


@nottest
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


class TestLinchpinProvisioner(TestCase):

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
    def test_instantiate_linchpinprovisioner(self):
        """Test instantiating a LinchpinProvisioner class and
        verifying the object created is an instance of the
        LinchpinProvisioner class.
        """
        scrub_lp_setup(self._base_path, '1234')
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        lp = LinchpinProvisioner(host.profile())
        assert_is_instance(lp, LinchpinProvisioner)

    @nottest
    def test_instantiate_linchpinprovisioner_lp_structure_exists(self):
        """Test instantiating a LinchpinProvisioner class and
        linch-pin structre exists. Verifying correct exception and
        message is thrown.
        """
        scrub_lp_setup(self._base_path, '1234', 'topologies')
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        with assert_raises_regexp(Exception, "Directory.*already exists"):
            lp = LinchpinProvisioner(host.profile())

    @nottest
    def test_linchpin_init(self):
        """ Test linch-pin setup. Instantiate LinchpinProvisioner class.
        Verify linchpin directory structure exists under workspace scenario.
        Directories, topologies, layouts, inventories and File PinFile
        """
        workspace = scrub_lp_setup(self._base_path, '1234')
        cp_parameters = deepcopy(self._parameters)
        host = Host(parameters=cp_parameters, scenario_id='1234')
        lp = LinchpinProvisioner(host.profile())
        assert_is_instance(lp, LinchpinProvisioner)
        assert_equal(os.path.exists(workspace + '/topologies'), True)
        assert_equal(os.path.exists(workspace + '/layouts'), True)
        assert_equal(os.path.exists(workspace + '/inventories'), True)
        assert_equal(os.path.exists(workspace + '/PinFile'), True)

    @nottest
    def test_create_openstack_topology(self):
        pass

    @nottest
    def test_create_beaker_topology(self):
        pass

    @nottest
    def test_create_openshift_topology(self):
        pass

    @nottest
    def test_create_layout_file(self):
        pass

    @nottest
    def test_create_pinfile_file(self):
        pass

    @nottest
    def test_create_openstack_credentials(self):
        pass

    @nottest
    def test_create_beaker_credentials(self):
        pass

    @nottest
    def test_create_openshift_credentials(self):
        pass
