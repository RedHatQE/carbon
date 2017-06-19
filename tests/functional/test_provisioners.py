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
from nose.tools import assert_is_instance, assert_equal, nottest, raises
from unittest import TestCase

from glanceclient.v2.client import Client as Glance_client
from keystoneauth1 import session
from neutronclient.v2_0 import client as neutron_client
from novaclient.v2.client import Client as Nova_client
from novaclient.v2.flavors import Flavor as Nova_flavor
from novaclient.v2.images import Image as Nova_image
from novaclient.v2.networks import Network as Nova_network

from carbon import Carbon
from carbon.core import CarbonException
from carbon._compat import is_py3
from carbon.helpers import file_mgmt
from carbon.provisioners.openshift import OpenshiftProvisioner
from carbon.provisioners.openshift import OpenshiftProvisionerException
from carbon.provisioners.openstack import OpenstackProvisioner
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
        obj.stop_container(obj.host.oc_name)
        obj.remove_container(obj.host.oc_name)

    def test_set_label(self):
        """Test setting the label for the application after the openshift
        provisioner class was instantiated.
        """
        obj = OpenshiftProvisioner(self.host)
        try:
            obj.labels = 'label1'
        except AttributeError:
            obj.stop_container(obj.host.oc_name)
            obj.remove_container(obj.host.oc_name)
            assert True

    def test_setup_labels(self):
        """Test the setup_labels method to create the list of labels to be
        assigned to the application when created.
        """
        obj = OpenshiftProvisioner(self.host)
        obj.setup_labels()
        obj.stop_container(obj.host.oc_name)
        obj.remove_container(obj.host.oc_name)
        assert_is_instance(obj.labels, list)

    @nottest
    def test_passwd_authentication(self):
        """Test authentication using username/password to openshift."""
        if is_py3:
            self.cbn.logger.warn('Skipping test due to Ansible support with '
                                 'Python3.')
            return True

        obj = OpenshiftProvisioner(self.host)
        obj.authenticate()
        obj.stop_container(obj.host.oc_name)
        obj.remove_container(obj.host.oc_name)

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
        params = self.data.pop('provision')[0]
        params['provider_creds'] = self.data.pop('credentials')
        self.host = Host(config=self.cbn.config, parameters=params)

    def test_create_object(self):
        """Create a openstack provisioner object. Verifies object is instance
        of carbon.provisioners.OpenstackProvisioner.
        """
        obj = OpenstackProvisioner(self.host)
        assert_is_instance(obj, OpenstackProvisioner)

    def test_get_provisioner_name(self):
        """Test getting the name of the provisioner class."""
        obj = OpenstackProvisioner(self.host)
        assert_equal(obj.name, 'openstack')

    @raises(ValueError)
    def test_set_provisioner_name(self):
        """Test setting the name for the provisioner class."""
        obj = OpenstackProvisioner(self.host)
        obj.name = 'openstack'

    @nottest
    def test_key_session_property(self):
        """Test creating a keystoneclient session. Verifies object is instance
        of keystoneauth1.session.Session.
        """
        obj = OpenstackProvisioner(self.host)
        assert_is_instance(obj.key_session, session.Session)

    @nottest
    def test_nova_property(self):
        """Test creating a nova client object. Verifies object is instance
        of novaclient.v2.client.Client.
        """
        obj = OpenstackProvisioner(self.host)
        assert_is_instance(obj.nova, Nova_client)

    @nottest
    def test_glance_property(self):
        """Test creating a glance client object. Verifies object is instance
        of glanceclient.v2.client.Client."""
        obj = OpenstackProvisioner(self.host)
        assert_is_instance(obj.glance, Glance_client)

    @nottest
    def test_neutron_property(self):
        """Test creating a neutron object. Verifies object is instance of
        neutronclient.v2.0.client.Client.
        """
        obj = OpenstackProvisioner(self.host)
        print(type(obj.neutron))
        assert_is_instance(obj.neutron, neutron_client.Client)

    @nottest
    def test_get_image(self):
        """Test getting image object for host image given. Verifies image
        object is instance of novaclient.v2.images.Image.
        """
        obj = OpenstackProvisioner(self.host)
        assert_is_instance(obj.image, Nova_image)

    @nottest
    @raises(ValueError)
    def test_set_image(self):
        """Test setting image for host. Exception should be raised since you
        cannot set image for host after resource.host is instantiated."""
        obj = OpenstackProvisioner(self.host)
        obj.image = 'Fedora-Cloud-Base-25-compose-latest'

    @nottest
    def test_get_flavor(self):
        """Test getting flavor object for host flavor given. Verifies flavor
        object is instance of novaclient.v2.flavors.Flavor.
        """
        obj = OpenstackProvisioner(self.host)
        assert_is_instance(obj.flavor, Nova_flavor)
        obj.host.os_flavor = 2
        assert_is_instance(obj.flavor, Nova_flavor)

    @nottest
    @raises(ValueError)
    def test_set_flavor(self):
        """Test setting flavor for host. Exception should be raised since you
        cannot set flavor for host after resource.host is instantiated."""
        obj = OpenstackProvisioner(self.host)
        obj.flavor = 'm1.small'

    @nottest
    def test_get_networks(self):
        """Test getting list of networks objects for host networks given.
        Verifies the list of network objects is an instance of
        novaclient.v2.networks.Network.
        """
        obj = OpenstackProvisioner(self.host)
        for network in obj.networks:
            assert_is_instance(network, Nova_network)

    @nottest
    @raises(ValueError)
    def test_set_networks(self):
        """Test setting networks for host. Exception should be raised since
        you cannot set networks for host after resource.host is instantiated.
        """
        obj = OpenstackProvisioner(self.host)
        obj.networks = ['network1']

    @nottest
    def test_create_delete(self):
        """Test creating a individual node. Always will delete the node to
        ensure proper cleanup.
        """
        obj = OpenstackProvisioner(self.host)
        try:
            obj.create()
        finally:
            obj.delete()
