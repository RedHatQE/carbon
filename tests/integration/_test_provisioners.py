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
    carbon.tests.integration.test_provisioners

    Integration tests to test carbon provisioners. Integration tests require
    credential details to communicate with various providers
    (openstack, beaker, etc.). You will need to configure a conf file which
    will hold all your provider credentials. Please see the example conf file
    at carbon/tests/assets/carbon.cfg. Once you have your conf file setup, you
    will want to export the following environment variable:

        export CARBON_SETTINGS=/etc/carbon/carbon.cfg

    You will want to replace the path to the location of your conf file. These
    tests will read credentials from that file.

    Beaker tests require you to set the environment variable below to define
    the path to your assets folder:

        export CARBON_ASSETS_PATH=/path/to/your/assets/folder

    You will want to replace the path to the location of your assets folder.
    Within this folder should contain three files:

        1. SSH private key
        2. Key tab file
        3. Example kick start file (example saved at carbon/tests/assets)

    Once this is all set you can run the tests!

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from unittest import TestCase

import os
from flask.config import Config
from glanceclient.v2.client import Client as Glance_client
from keystoneauth1 import session
from neutronclient.v2_0 import client as neutron_client
from nose import SkipTest
from nose.tools import assert_equal, assert_is_instance, nottest, raises
from novaclient.v2.client import Client as Nova_client
from novaclient.v2.flavors import Flavor as Nova_flavor
from novaclient.v2.images import Image as Nova_image
from novaclient.v2.networks import Network as Nova_network

from carbon import Carbon
from carbon._compat import is_py3
from carbon.helpers import file_mgmt
from carbon.provisioners.beaker import BeakerProvisioner
from carbon.provisioners.beaker import BeakerProvisionerError
from carbon.provisioners.openshift import OpenshiftProvisioner
from carbon.provisioners.openshift import OpenshiftProvisionerError
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


class TestOpenstackProvisioner(TestCase):
    """Integration tests to test openstack provisioner.

    The purpose of this class is to test different methods of the provisioner
    class that require communicating with openstack to provision and delete
    resources.
    """

    def setUp(self):
        """Setup tasks to be run before each test case."""
        global CARBON_CFG, CARBON_CFGS
        global SCENARIO_CFG, SCENARIO_CFGS

        # get carbon config file path
        for f in CARBON_CFGS:
            if os.path.exists(f):
                CARBON_CFG = f

        # get carbon scenario file path
        for f in SCENARIO_CFGS:
            if os.path.exists(f):
                SCENARIO_CFG = f

        # set carbon settings env variable
        self.env = EnvironmentVarGuard()

        # create a carbon object
        self.cbn = Carbon(__name__, assets_path="assets")

        # load scenario
        self.data = file_mgmt('r', SCENARIO_CFG)
        host_params = self.data['provision'][0]

        if os.getenv('CARBON_SETTINGS'):
            # load conf file
            config = Config(os.getcwd())
            config.from_pyfile(os.environ['CARBON_SETTINGS'], silent=True)

            # set provider credentials for host
            for item in config['CREDENTIALS']:
                if 'openstack' in item['name']:
                    host_params['provider_creds'] = [item]
                    break
        else:
            # set provider credentials for host
            host_params['provider_creds'] = self.data.pop('credentials')

        # create host object
        self.host = Host(config=self.cbn.config, parameters=host_params)

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

    # attribute place holders
    host = object
    host2 = object
    host3 = object
    host4 = object
    host5 = object
    host6 = object


    def setUp(self):
        """Setup tasks to be run before each test case."""
        global CARBON_CFG, CARBON_CFGS
        global SCENARIO_CFG, SCENARIO_CFGS

        # beaker provisioner object
        self.obj = object

        # get carbon conf file path
        for f in CARBON_CFGS:
            if os.path.exists(f):
                CARBON_CFG = f

        # get carbon scenario file path
        for f in SCENARIO_CFGS:
            if os.path.exists(f):
                SCENARIO_CFG = f

        # set carbon settings env variable
        self.env = EnvironmentVarGuard()

        # create carbon object
        if os.getenv("CARBON_ASSETS_PATH"):
            self.cbn = Carbon(__name__, assets_path = \
                os.environ["CARBON_ASSETS_PATH"])
        else:
            # static to carbon jenkins slave
            self.cbn = Carbon(__name__, assets_path="/home/fedora/assets")

        BeakerProvisioner._bkr_image = \
            "docker-registry.engineering.redhat.com/carbon/bkr-client"

        # load scenario
        self.data = file_mgmt('r', SCENARIO_CFG)

        # create host objects
        base = 0
        for index in range(5, 11):
            # get host data
            host_params = self.data['provision'][index]

            if os.getenv('CARBON_SETTINGS'):
                # load conf file
                config = Config(os.getcwd())
                config.from_pyfile(os.environ['CARBON_SETTINGS'], silent=True)

                # set provider credentials for host
                for item in config['CREDENTIALS']:
                    if 'beaker' in item['name']:
                        host_params['provider_creds'] = [item]
                        break
            else:
                host_params['provider_creds'] = self.data.pop('credentials')

            # create host object
            if index == 5:
                host_attr = 'host'
                # set base to be used to determine attribute name based on
                # position in provision list of hosts.
                base = index - 1
            else:
                host_attr = 'host%s' % (index - base)

            # set attribute
            setattr(
                self,
                host_attr,
                Host(config=self.cbn.config, parameters=host_params)
            )

            # add host to carbon scenario
            self.cbn.scenario.add_hosts(getattr(self, host_attr))


    def tearDown(self):
        """ Cleanup Docker Container. Stop and remove"""
        # Stop/remove container
        if self.obj and self.obj.docker and self.obj.docker.\
                get_container_status():
            self.obj.docker.stop_container()
            self.obj.docker.remove_container()

    def test_authenticate(self):
        """Create a beaker provisioner object. Verifies object is instance
        of carbon.provisioners.BeakerProvisioner. Authenticate
        """
        if is_py3:
            raise SkipTest('Ansible support for Python 3 not available.')

        # Create a new carbon compound
        self.cbn._copy_assets()
        self.obj = BeakerProvisioner(self.host)
        assert_is_instance(self.obj, BeakerProvisioner)
        self.obj.start_container()
        self.obj.authenticate()

    @nottest
    def test_authenticate_user_password(self):
        """Create a beaker provisioner object. Verifies object is instance
        of carbon.provisioners.BeakerProvisioner. Authenticate with user and
        password
        """
        if is_py3:
            raise SkipTest('Ansible support for Python 3 not available.')

        # Create a new carbon compound
        self.cbn._copy_assets()
        self.obj = BeakerProvisioner(self.host2)
        assert_is_instance(self.obj, BeakerProvisioner)
        self.obj.start_container()
        self.obj.authenticate()

    def test_create_and_delete(self):
        """Create a beaker provisioner object. Verifies object is instance
        of carbon.provisioners.BeakerProvisioner. Create and delete resource
        """
        if is_py3:
            raise SkipTest('Ansible support for Python 3 not available.')

        self.cbn._copy_assets()
        self.obj = BeakerProvisioner(self.host)
        assert_is_instance(self.obj, BeakerProvisioner)
        self.obj.create()
        self.obj = BeakerProvisioner(self.host)
        self.obj.delete()

    def test_generateBKRXMLfrom_host(self):
        """Test create resource for the provisioner class."""
        if is_py3:
            raise SkipTest('Ansible support for Python 3 not available.')

        self.cbn._copy_assets()
        self.obj = BeakerProvisioner(self.host)
        self.obj.start_container()
        self.obj.authenticate()
        self.obj.gen_bkr_xml()

    def test_generateBKRXML_no_save_print(self):
        """Test create resource for the provisioner class. No Save"""
        if is_py3:
            raise SkipTest('Ansible support for Python 3 not available.')

        self.cbn._copy_assets()
        self.obj = BeakerProvisioner(self.host)
        self.obj.start_container()
        self.obj.authenticate()

        # Obtain xml path
        bkr_xml_file = os.path.join(self.obj.host.data_folder(),
                                    self.obj._bkr_xml)

        host_desc = self.obj.host.profile()

        # Set attributes for Beaker
        for key in host_desc:
            if key is not 'bkr_name' and key.startswith('bkr_'):
                xml_key = key.split("bkr_", 1)[1]
                if host_desc[key]:
                    try:
                        setattr(self.obj.bxml, xml_key, host_desc[key])
                    except Exception as ex:
                        raise Exception(
                            'Error setting beaker attribute data: %s' % ex
                        )

        # Generate Beaker XML
        self.obj.bxml.generate_beaker_xml(bkr_xml_file, savefile=False)
        assert_equal(self.obj.bxml.cmd,
                     "bkr workflow-simple --arch x86_64 --variant Workstation "
                     "--whiteboard 'Testing machine provisioning from Carbon' "
                     "--method nfs --kernel_options 'selinux=--permisssive "
                     "keyboard=us lang=us timezone=est' --kernel_options_post "
                     "'isolcpus = 0,5' --debug --dryrun --task /distribution/"
                     "reservesys --tag RTT_ACCEPTED --distro RHEL-6.9 --job-"
                     "group ci-ops-pit --priority Normal "
                     "--keyvalue 'DISKSPACE>=500000' --keyvalue 'HVM=1'")

        # Format command for container
        _cmd = self.obj.bxml.cmd.replace('=', "\=")

        # Run command on container
        results = self.obj.ansible.run_module(
            dict(name='bkr workflow-simple',
                 hosts=self.obj.docker.cname, gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args=_cmd))])
        )

        # Process results and get xml from stdout
        self.obj.ansible.results_analyzer(results['status'])

        if results['status'] != 0:
            raise Exception('Issue generating beaker xml.')
        else:
            if len(results["callback"].contacted) == 1:
                parsed_results = results["callback"].contacted[0]["results"]
            else:
                raise Exception('Unexpected error creating beaker xml.')
            output = parsed_results["stdout"]

        # Test generation of XML DOM
        self.obj.bxml.generate_xml_dom(bkr_xml_file, output, savefile=False)

        # Test getting Text methods of xml
        self.obj.bxml.get_xml_text()
        self.obj.bxml.get_xmldom_pretty()

    def test_create_and_delete_all_keys_(self):
        """Create a beaker provisioner object. Verifies object is instance
        of carbon.provisioners.BeakerProvisioner. Create and delete resource
        Use all keys and authenticate with user password
        """
        if is_py3:
            raise SkipTest('Ansible support for Python 3 not available.')

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
            raise SkipTest('Ansible support for Python 3 not available.')

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
        self.obj.start_container()
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
        self.obj.start_container()
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
        self.obj.start_container()
        self.obj.authenticate()
