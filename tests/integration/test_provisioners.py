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
import ast
from unittest import TestCase

import os
from glanceclient.v2.client import Client as Glance_client
from keystoneauth1 import session
from neutronclient.v2_0 import client as neutron_client
from nose import SkipTest
from nose.tools import assert_is_instance, nottest, raises
from novaclient.v2.client import Client as Nova_client
from novaclient.v2.flavors import Flavor as Nova_flavor
from novaclient.v2.images import Image as Nova_image
from novaclient.v2.networks import Network as Nova_network

from carbon import Carbon
from carbon._compat import is_py3
from carbon.helpers import file_mgmt
from carbon.provisioners.beaker import BeakerProvisioner
from carbon.provisioners.beaker import BeakerProvisionerError
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
    os.path.join(os.getcwd(), 'assets/scenario_nocreds.yaml'),
    os.path.join(os.getcwd(), '../assets/scenario_nocreds.yaml')
]

def read_data(file_location):
    myvars = {}
    with open(file_location) as myfile:
        for line in myfile:
            if "=" in line:
                name = line.split("=")[0]
                var = line.split("=")[1]
                myvars[name.strip()] = var
    return myvars

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
        #self.env.set('CARBON_SETTINGS', CARBON_CFG)

        # Create carbon object
        self.cbn = Carbon(__name__, assets_path="assets")

        # Load scenario data
        self.data = file_mgmt('r', SCENARIO_CFG)
        params = self.data.pop('provision')[0]
        if os.getenv("CARBON_SETTINGS") is not None:
            params['provider_creds'] = ast.literal_eval(read_data(os.environ["CARBON_SETTINGS"])["CREDENTIALS"].strip())
        else:
            params['provider_creds'] = self.data.pop('credentials')
        self.host = Host(config=self.cbn.config, parameters=params)

    def test_key_session_property(self):
        """Test creating a keystoneclient session. Verifies object is instance
        of keystoneauth1.session.Session.
        """
        obj = OpenstackProvisioner(self.host)
        assert_is_instance(obj.key_session, session.Session)

    def test_nova_property(self):
        """Test creating a nova client object. Verifies object is instance
        of novaclient.v2.client.Client.
        """
        obj = OpenstackProvisioner(self.host)
        assert_is_instance(obj.nova, Nova_client)

    def test_glance_property(self):
        """Test creating a glance client object. Verifies object is instance
        of glanceclient.v2.client.Client."""
        obj = OpenstackProvisioner(self.host)
        assert_is_instance(obj.glance, Glance_client)

    def test_neutron_property(self):
        """Test creating a neutron object. Verifies object is instance of
        neutronclient.v2.0.client.Client.
        """
        obj = OpenstackProvisioner(self.host)
        print(type(obj.neutron))
        assert_is_instance(obj.neutron, neutron_client.Client)

    def test_get_image(self):
        """Test getting image object for host image given. Verifies image
        object is instance of novaclient.v2.images.Image.
        """
        obj = OpenstackProvisioner(self.host)
        assert_is_instance(obj.image, Nova_image)

    @raises(ValueError)
    def test_set_image(self):
        """Test setting image for host. Exception should be raised since you
        cannot set image for host after resource.host is instantiated."""
        obj = OpenstackProvisioner(self.host)
        obj.image = 'Fedora-Cloud-Base-25-compose-latest'

    def test_get_flavor(self):
        """Test getting flavor object for host flavor given. Verifies flavor
        object is instance of novaclient.v2.flavors.Flavor.
        """
        obj = OpenstackProvisioner(self.host)
        assert_is_instance(obj.flavor, Nova_flavor)
        obj.host.os_flavor = 2
        assert_is_instance(obj.flavor, Nova_flavor)

    @raises(ValueError)
    def test_set_flavor(self):
        """Test setting flavor for host. Exception should be raised since you
        cannot set flavor for host after resource.host is instantiated."""
        obj = OpenstackProvisioner(self.host)
        obj.flavor = 'm1.small'

    def test_get_networks(self):
        """Test getting list of networks objects for host networks given.
        Verifies the list of network objects is an instance of
        novaclient.v2.networks.Network.
        """
        obj = OpenstackProvisioner(self.host)
        for network in obj.networks:
            assert_is_instance(network, Nova_network)

    @raises(ValueError)
    def test_set_networks(self):
        """Test setting networks for host. Exception should be raised since
        you cannot set networks for host after resource.host is instantiated.
        """
        obj = OpenstackProvisioner(self.host)
        obj.networks = ['network1']

    def test_create_delete(self):
        """Test creating a individual node. Always will delete the node to
        ensure proper cleanup.
        """
        obj = OpenstackProvisioner(self.host)
        try:
            obj.create()
        finally:
            obj.delete()

class TestBeakerProvisioner(TestCase):
    """Unit tests to test carbon provisioner ~ beaker."""

    def setUp(self):
        """Actions to be performed before each test case."""
        global CARBON_CFG, CARBON_CFGS
        global SCENARIO_CFG, SCENARIO_CFGS

        # BeakerProvisioner obj
        self.obj = None

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
        #self.env.set('CARBON_SETTINGS', CARBON_CFG)

        # Create carbon object
        if os.getenv("CARBON_ASSETS_PATH") is not None:
            self.cbn = Carbon(__name__, assets_path = os.environ["CARBON_ASSETS_PATH"])
        else:
            self.cbn = Carbon(__name__, assets_path="/home/fedora/assets")

        BeakerProvisioner._bkr_image = "docker-registry.engineering.redhat.com/carbon/bkr-client"

        # Load scenario data
        self.data = file_mgmt('r', SCENARIO_CFG)
        params = self.data.pop('provision')[5]
        if os.getenv("CARBON_SETTINGS") is not None:
            params['provider_creds'] = ast.literal_eval(read_data(os.environ["CARBON_SETTINGS"])["CREDENTIALS"].strip())
        else:
            params['provider_creds'] = self.data.pop('credentials')
        self.host = Host(config=self.cbn.config, parameters=params)
        self.cbn.scenario.add_hosts(self.host)

        self.data = file_mgmt('r', SCENARIO_CFG)
        params = self.data.pop('provision')[6]
        if os.getenv("CARBON_SETTINGS") is not None:
            params['provider_creds'] = ast.literal_eval(read_data(os.environ["CARBON_SETTINGS"])["CREDENTIALS"].strip())
        else:
            params['provider_creds'] = self.data.pop('credentials')
        self.host2 = Host(config=self.cbn.config, parameters=params)
        self.cbn.scenario.add_hosts(self.host2)

        self.data = file_mgmt('r', SCENARIO_CFG)
        params = self.data.pop('provision')[7]
        if os.getenv("CARBON_SETTINGS") is not None:
            params['provider_creds'] = ast.literal_eval(read_data(os.environ["CARBON_SETTINGS"])["CREDENTIALS"].strip())
        else:
            params['provider_creds'] = self.data.pop('credentials')
        self.host3 = Host(config=self.cbn.config, parameters=params)
        self.cbn.scenario.add_hosts(self.host3)

        self.data = file_mgmt('r', SCENARIO_CFG)
        params = self.data.pop('provision')[8]
        if os.getenv("CARBON_SETTINGS") is not None:
            params['provider_creds'] = ast.literal_eval(read_data(os.environ["CARBON_SETTINGS"])["CREDENTIALS"].strip())
        else:
            params['provider_creds'] = self.data.pop('credentials')
        self.host4 = Host(config=self.cbn.config, parameters=params)
        self.cbn.scenario.add_hosts(self.host4)

        self.data = file_mgmt('r', SCENARIO_CFG)
        params = self.data.pop('provision')[9]
        if os.getenv("CARBON_SETTINGS") is not None:
            params['provider_creds'] = ast.literal_eval(read_data(os.environ["CARBON_SETTINGS"])["CREDENTIALS"].strip())
        else:
            params['provider_creds'] = self.data.pop('credentials')
        self.host5 = Host(config=self.cbn.config, parameters=params)
        self.cbn.scenario.add_hosts(self.host5)

        self.data = file_mgmt('r', SCENARIO_CFG)
        params = self.data.pop('provision')[10]
        if os.getenv("CARBON_SETTINGS") is not None:
            params['provider_creds'] = ast.literal_eval(read_data(os.environ["CARBON_SETTINGS"])["CREDENTIALS"].strip())
        else:
            params['provider_creds'] = self.data.pop('credentials')
        self.host6 = Host(config=self.cbn.config, parameters=params)
        self.cbn.scenario.add_hosts(self.host6)

    def tearDown(self):
        """ Cleanup Docker Container. Stop and remove"""
        # Stop/remove container
        if self.obj and self.obj.docker and self.obj.docker.get_container_status():
            self.obj.docker.stop_container()
            self.obj.docker.remove_container()

    def test_authenticate(self):
        """Create a beaker provisioner object. Verifies object is instance
        of carbon.provisioners.BeakerProvisioner. Authenticate
        """
        if is_py3:
            self.cbn.logger.warn('Skipping test due to Ansible support with '
                                 'Python3.')
            raise SkipTest('Skipping test due to Ansible support with Python3.')

        # Create a new carbon compound
        self.cbn._copy_assets()
        self.obj = BeakerProvisioner(self.host)
        assert_is_instance(self.obj, BeakerProvisioner)
        self.obj.authenticate()

    @nottest
    def test_authenticate_user_password(self):
        """Create a beaker provisioner object. Verifies object is instance
        of carbon.provisioners.BeakerProvisioner. Authenticate with user and
        password
        """
        if is_py3:
            self.cbn.logger.warn('Skipping test due to Ansible support with '
                                 'Python3.')
            raise SkipTest('Skipping test due to Ansible support with Python3.')

        # Create a new carbon compound
        self.cbn._copy_assets()
        self.obj = BeakerProvisioner(self.host2)
        assert_is_instance(self.obj, BeakerProvisioner)
        self.obj.authenticate()

    def test_create_and_delete(self):
        """Create a beaker provisioner object. Verifies object is instance
        of carbon.provisioners.BeakerProvisioner. Create and delete resource
        """
        if is_py3:
            self.cbn.logger.warn('Skipping test due to Ansible support with '
                                 'Python3.')
            raise SkipTest('Skipping test due to Ansible support with Python3.')

        self.cbn._copy_assets()
        self.obj = BeakerProvisioner(self.host)
        assert_is_instance(self.obj, BeakerProvisioner)
        self.obj.create()
        self.obj = BeakerProvisioner(self.host)
        self.obj.delete()

    def test_generateBKRXMLfrom_host(self):
        """Test create resource for the provisioner class."""
        if is_py3:
            self.cbn.logger.warn('Skipping test due to Ansible support with '
                                 'Python3.')
            raise SkipTest('Skipping test due to Ansible support with Python3.')

        self.cbn._copy_assets()
        self.obj = BeakerProvisioner(self.host)

        self.obj.authenticate()
        self.obj.gen_bkr_xml()

    def test_create_and_delete_all_keys_(self):
        """Create a beaker provisioner object. Verifies object is instance
        of carbon.provisioners.BeakerProvisioner. Create and delete resource
        Use all keys and authenticate with user password
        """
        if is_py3:
            self.cbn.logger.warn('Skipping test due to Ansible support with '
                                 'Python3.')
            raise SkipTest('Skipping test due to Ansible support with Python3.')

        self.cbn._copy_assets()
        self.host5.bkr_timeout = 160
        self.obj = BeakerProvisioner(self.host5)
        assert_is_instance(self.obj, BeakerProvisioner)
        try:
            self.obj.create()
        except BeakerProvisionerError:
            pass
        self.obj = BeakerProvisioner(self.host5)
        self.obj.delete()


    def test_create_and_delete_all_keys_except_kickstart(self):
        """Create a beaker provisioner object. Verifies object is instance
        of carbon.provisioners.BeakerProvisioner. Create and delete resource
        Use all keys and authenticate with user password
        """
        if is_py3:
            self.cbn.logger.warn('Skipping test due to Ansible support with '
                                 'Python3.')
            raise SkipTest('Skipping test due to Ansible support with Python3.')

        self.cbn._copy_assets()
        self.obj = BeakerProvisioner(self.host6)
        assert_is_instance(self.obj, BeakerProvisioner)
        self.obj.create()
        self.obj = BeakerProvisioner(self.host6)
        self.obj.delete()

    @raises(BeakerProvisionerError)
    def test_authenticate_unable_to_copy_files_to_cotainer(self):
        """Create a beaker provisioner object. Verifies object is instance
        of carbon.provisioners.BeakerProvisioner. Authenticate fail to copy
        files to container
        """
        # Create a new carbon compound
        self.cbn._copy_assets()
        self.obj = BeakerProvisioner(self.host)
        assert_is_instance(self.obj, BeakerProvisioner)
        self.obj.host.provider.credentials["keytab"] = "badfile"
        self.obj.authenticate()

    @raises(BeakerProvisionerError)
    def test_authenticate_no_credentials(self):
        """Create a beaker provisioner object. Verifies object is instance
        of carbon.provisioners.BeakerProvisioner. Authenticate with no
        credentials set
        """
        # Create a new carbon compound
        self.cbn._copy_assets()
        self.obj = BeakerProvisioner(self.host3)
        assert_is_instance(self.obj, BeakerProvisioner)
        self.obj.host.provider.credentials["keytab"] = None
        self.obj.host.provider.credentials["keytab_principal"] = None
        self.obj.host.provider.credentials["username"] = None
        self.obj.host.provider.credentials["passwork"] = None
        self.obj.authenticate()

    @raises(BeakerProvisionerError)
    def test_authenticate_bad_credentials(self):
        """Create a beaker provisioner object. Verifies object is instance
        of carbon.provisioners.BeakerProvisioner. Authenticate with no
        credentials set
        """
        # Create a new carbon compound
        self.cbn._copy_assets()
        self.obj = BeakerProvisioner(self.host4)
        assert_is_instance(self.obj, BeakerProvisioner)
        self.obj.host.provider.credentials["keytab"] = None
        self.obj.host.provider.credentials["keytab_principal"] = None
        self.obj.host.provider.credentials["username"] = "badname"
        self.obj.host.provider.credentials["password"] = "badpass"
        self.obj.authenticate()