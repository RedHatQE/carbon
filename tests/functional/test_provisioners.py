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
    Unit tests to test carbon provisioners.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import os
from nose.tools import assert_is_instance, nottest, raises
from unittest import TestCase

from carbon import Carbon
from carbon._compat import is_py3
from carbon.helpers import file_mgmt
from carbon.provisioners.openshift import OpenshiftProvisioner
from carbon.provisioners.openshift import OpenshiftProvisionerException
from carbon.resources import Host

try:
    from test.test_support import EnvironmentVarGuard
except ImportError:
    from test.support import EnvironmentVarGuard


CARBON_CFG = None
CARBON_CFGS = [
    os.path.join(os.getcwd(), 'assets/carbon.cfg'),
    os.path.join(os.getcwd(), '../assets/carbon.cfg')
]
SCENARIO_CFG = None
SCENARIO_CFGS = [
    os.path.join(os.getcwd(), 'assets/scenario.yaml'),
    os.path.join(os.getcwd(), '../assets/scenario.yaml')
]


class TestOpenshiftProvisioner(TestCase):
    """Unit tests to test carbon provisioner ~ openshift."""

    @nottest
    def setUp(self):
        """Actions to be performed before each test case."""
        global CARBON_CFG, CARBON_CFGS
        global SCENARIO_CFG, SCENARIO_CFGS

        # Determine abs path to carbon config
        for f in CARBON_CFGS:
            if os.path.exists(f):
                CARBON_CFG = f

        # Determine abs path to scenario config
        for f in SCENARIO_CFGS:
            if os.path.exists(f):
                SCENARIO_CFG = f

        # Set carbon settings env variable
        self.env = EnvironmentVarGuard()
        self.env.set('CARBON_SETTINGS', CARBON_CFG)

        # Create carbon object
        self.cbn = Carbon(__name__, assets_path="assets")

        # Load scenario data
        self.data = file_mgmt('r', SCENARIO_CFG)
        params = self.data.pop('provision')[3]
        params['provider_creds'] = self.data.pop('credentials')
        self.host = Host(config=self.cbn.config, parameters=params)

    def test_create_object(self):
        """Create a openshift provisioner object."""
        obj = OpenshiftProvisioner(self.host)
        assert_is_instance(obj, OpenshiftProvisioner)
        obj.stop_container(obj.name)
        obj.remove_container(obj.name)

    @raises(AttributeError)
    def test_set_container_name(self):
        """Test setting the name for the container after the openshift
        provisioner class was instantiated.
        """
        try:
            obj = OpenshiftProvisioner(self.host)
            obj.name = 'container123'
        finally:
            obj.stop_container(obj.name)
            obj.remove_container(obj.name)

    @raises(AttributeError)
    def test_set_label(self):
        """Test setting the label for the application after the openshift
        provisioner class was instantiated.
        """
        try:
            obj = OpenshiftProvisioner(self.host)
            obj.label = 'label1'
        finally:
            obj.stop_container(obj.name)
            obj.remove_container(obj.name)

    def test_setup_label(self):
        """Test the setup_label method to create the list of labels to be
        assigned to the application when created.
        """
        obj = OpenshiftProvisioner(self.host)
        obj.setup_label()
        obj.stop_container(obj.name)
        obj.remove_container(obj.name)
        assert_is_instance(obj.label, list)

    @nottest
    def test_passwd_authentication(self):
        """Test authentication using username/password to openshift."""
        if is_py3:
            self.cbn.logger.warn('Skipping test due to Ansible support with '
                                 'Python3.')
            return True

        obj = OpenshiftProvisioner(self.host)
        obj.authenticate()
        obj.stop_container(obj.name)
        obj.remove_container(obj.name)

    @nottest
    @raises(OpenshiftProvisionerException)
    def test_invalid_authentication(self):
        """Test invalid authentication."""
        if is_py3:
            self.cbn.logger.warn('Skipping test due to Ansible support with '
                                 'Python3.')
            raise OpenshiftProvisionerException

        obj = OpenshiftProvisioner(self.host)
        obj.host.provider._credentials['token'] = 'token'
        obj.authenticate()

    @nottest
    @raises(OpenshiftProvisionerException)
    def test_authentication_missing_keys(self):
        """Test authentication with missing keys."""
        if is_py3:
            self.cbn.logger.warn('Skipping test due to Ansible support with '
                                 'Python3.')
            raise OpenshiftProvisionerException

        obj = OpenshiftProvisioner(self.host)
        obj.host.provider._credentials.pop('password')
        obj.authenticate()

    @nottest
    def test_select_project(self):
        """Test the select project method to choose which project to create
        applications within.
        """
        if is_py3:
            self.cbn.logger.warn('Skipping test due to Ansible support with '
                                 'Python3.')
            return True

        obj = OpenshiftProvisioner(self.host)
        obj.authenticate()
        obj.select_project()

    @nottest
    @raises(OpenshiftProvisionerException)
    def test_select_invalid_project(self):
        """Test the select project method to choose an invalid project to
        create applications within.
        """
        if is_py3:
            self.cbn.logger.warn('Skipping test due to Ansible support with '
                                 'Python3.')
            raise OpenshiftProvisionerException

        obj = OpenshiftProvisioner(self.host)
        obj.host.provider._credentials['project'] = 'invalid_project'
        obj.authenticate()
        obj.select_project()


class TestOpenstackProvisioner(TestCase):
    """Unit tests to test carbon provisioner ~ openstack."""
    pass
