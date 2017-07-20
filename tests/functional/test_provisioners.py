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
from unittest import TestCase

import os
from nose.tools import assert_is_instance, assert_equal, nottest, raises

from carbon import Carbon
from carbon._compat import is_py3
from carbon.controllers import AnsibleController
from carbon.controllers import DockerController
from carbon.helpers import file_mgmt
from carbon.provisioners.beaker import BeakerProvisioner
from carbon.provisioners.beaker import BeakerProvisionerException
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
        obj.docker.stop_container()
        obj.docker.remove_container()

    def test_set_label(self):
        """Test setting the label for the application after the openshift
        provisioner class was instantiated.
        """
        obj = OpenshiftProvisioner(self.host)
        try:
            obj.labels = 'label1'
        except AttributeError:
            obj.docker.stop_container()
            obj.docker.remove_container()
            assert True

    def test_setup_labels(self):
        """Test the setup_labels method to create the list of labels to be
        assigned to the application when created.
        """
        obj = OpenshiftProvisioner(self.host)
        obj.setup_labels()
        obj.docker.stop_container()
        obj.docker.remove_container()
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
        obj.docker.stop_container()
        obj.docker.remove_container()

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
        params = self.data.pop('provision')[1]
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

    @raises(AttributeError)
    def test_set_provisioner_name(self):
        """Test setting the name for the provisioner class."""
        obj = OpenstackProvisioner(self.host)
        obj.name = 'openstack'


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
        self.env.set('CARBON_SETTINGS', CARBON_CFG)

        # Create carbon object
        self.cbn = Carbon(__name__, assets_path="assets")

        BeakerProvisioner._bkr_image = "docker-registry.engineering.redhat.com/carbon/bkr-client"

        # Load scenario data
        self.data = file_mgmt('r', SCENARIO_CFG)
        params = self.data.pop('provision')[5]
        _credentials = self.data.pop('credentials')
        params['provider_creds'] = _credentials
        self.host = Host(config=self.cbn.config, parameters=params)
        self.cbn.scenario.add_hosts(self.host)


    def tearDown(self):
        """ Cleanup Docker Container. Stop and remove"""
        # Stop/remove container
        if self.obj and self.obj.docker and self.obj.docker.get_container_status():
            self.obj.docker.stop_container()
            self.obj.docker.remove_container()


    def test_create_object(self):
        """Create a beaker provisioner object. Verifies object is instance
        of carbon.provisioners.BeakerProvisioner.
        """
        self.obj = BeakerProvisioner(self.host)
        assert_is_instance(self.obj, BeakerProvisioner)

    def test_set(self):
        """ Create a beaker provisioner object. Verify object is instance
        or carbon.provisioners.BeakerProvisioner. Verify set method.
        """
        self.obj = BeakerProvisioner(self.host)
        assert_equal(self.obj.bxml.set('variant', 'Server'), 0)
        assert_equal(self.obj.bxml.set("priority", "Urgent"), 0)
        assert_equal(self.obj.bxml.set("family", "RedHatEnterpriseLinux7"), 0)
        assert_equal(self.obj.bxml.set("retentiontag", "60days"), 0)
        assert_equal(self.obj.bxml.set("whiteboard", "Test White board Value"), 0)
        assert_equal(self.obj.bxml.set("packages", ["git, yum"]), 0)
        assert_equal(self.obj.bxml.set("tasks", ["/distribution/install", "distribution/dummy"]), 0)
        assert_equal(self.obj.bxml.set("tag", "RTT_ACCEPTED"), 0)
        assert_equal(self.obj.bxml.set("distro", "RHEL-73"), 0)
        assert_equal(self.obj.bxml.set("arch", "x86_64"), 0)
        assert_equal(self.obj.bxml.set("reservetime", "172800"), 0)
        assert_equal(self.obj.bxml.set("method", "nfs"), 0)
        assert_equal(self.obj.bxml.set("component", "network"), 0)
        assert_equal(self.obj.bxml.set("product", "Rhevm"), 0)
        assert_equal(self.obj.bxml.set("kernel_options",
                                  ["selinux=--permisssive", "keyboard=us",
                                   "lang=us", "timezone=est"]), 0)
        assert_equal(self.obj.bxml.set("kernel_post_options", ["isolcpus=0,5"]), 0)
        assert_equal(self.obj.bxml.set("cclist", ["user1", "user2", "user3"]), 0)
        assert_equal(self.obj.bxml.set("gargage", "badparam"), 1)

    @raises(BeakerProvisionerException)
    def test_create_object_bad_docker_image(self):
        """Create a beaker provisioner object. Verifies object is instance
        of carbon.provisioners.BeakerProvisioner.
        """
        BeakerProvisioner._bkr_image = "abx"
        self.obj = BeakerProvisioner(self.host)
        assert_is_instance(self.obj, BeakerProvisioner)

    def test_get_provisioner_name(self):
        """Test getting the name of the provisioner class."""
        self.obj = BeakerProvisioner(self.host)
        assert_equal(self.obj.name, 'beaker')

    @raises(AttributeError)
    def test_set_provisioner_name(self):
        """Test setting the name for the provisioner class."""
        self.obj = BeakerProvisioner(self.host)
        self.obj.name = 'beaker'

    def test_get_provisioner_docker(self):
        """Test getting docker controller of the provisioner class."""
        self.obj = BeakerProvisioner(self.host)
        assert_is_instance(self.obj.docker, DockerController)

    @raises(ValueError)
    def test_set_provisioner_docker(self):
        """Test setting the docker controller for the provisioner class."""
        self.obj = BeakerProvisioner(self.host)
        self.obj.docker = DockerController(cname="new_Docker_controller")

    def test_get_provisioner_ansible(self):
        """Test getting ansible controller of the provisioner class."""
        self.obj = BeakerProvisioner(self.host)
        assert_is_instance(self.obj.ansible, AnsibleController)

    @raises(ValueError)
    def test_set_provisioner_ansible(self):
        """Test setting the ansible controller for the provisioner class."""
        self.obj = BeakerProvisioner(self.host)
        self.obj.ansible = AnsibleController(self.obj.docker.name.lower())

    def test_generateBKRXML(self):
        """Test create resource for the provisioner class."""
        self.obj = BeakerProvisioner(self.host)
        bkr_xml_file = os.path.join(self.obj._data_folder,
                                    self.obj._bkr_xml)

        self.obj.bxml.generateBKRXML(bkr_xml_file, savefile=True)
        assert_equal(self.obj.bxml.cmd,
                     "bkr workflow-simple --arch  --whiteboard 'Carbon: , ' --method nfs --debug --dryrun --task /distribution/reservesys --priority Normal")
