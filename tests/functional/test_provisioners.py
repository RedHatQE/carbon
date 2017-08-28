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
from nose.tools import assert_is_instance, assert_equal, assert_true, \
    raises

from carbon import Carbon
from carbon.controllers import AnsibleController
from carbon.controllers import DockerController
from carbon.controllers import DockerControllerError
from carbon.helpers import file_mgmt
from carbon.provisioners.beaker import BeakerProvisioner
from carbon.provisioners.openshift import OpenshiftProvisioner
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

    @raises(AttributeError)
    def test_set_label(self):
        """Test setting the label for the application after the openshift
        provisioner class was instantiated.
        """
        obj = OpenshiftProvisioner(self.host)
        obj.labels = 'label1'

    def test_setup_labels(self):
        """Test the setup_labels method to create the list of labels to be
        assigned to the application when created.
        """
        obj = OpenshiftProvisioner(self.host)
        obj.setup_labels()
        assert_is_instance(obj.labels, list)


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

        BeakerProvisioner._bkr_image = \
            "docker-registry.engineering.redhat.com/carbon/bkr-client"

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
        if self.obj and self.obj.docker and self.obj.docker.\
                get_container_status():
            self.obj.docker.stop_container()
            self.obj.docker.remove_container()


    def test_create_object(self):
        """Create a beaker provisioner object. Verifies object is instance
        of carbon.provisioners.BeakerProvisioner.
        """
        self.obj = BeakerProvisioner(self.host)
        assert_is_instance(self.obj, BeakerProvisioner)

    def test_set_kernel_options(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set kernel_options.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.kernel_options = ["selinux=--permisssive", "keyboard=us",
                                      "lang=us", "timezone=est"]

        assert_equal(self.obj.bxml.kernel_options, ["selinux=--permisssive",
                                                    "keyboard=us",
                                                    "lang=us", "timezone=est"])

    def test_set_kernel_post_options(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner.
        Verify set kernel_post_options.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.kernel_post_options = ["isolcpus=0,5"]

        assert_equal(self.obj.bxml.kernel_post_options, ["isolcpus=0,5"])

    def test_set_kickstart(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set kickstart.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.kickstart = "rhel7-7.3-ci-cloud.ks"

        assert_equal(self.obj.bxml.kickstart, "rhel7-7.3-ci-cloud.ks")

    def test_set_ksmeta(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set ksmeta.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.ksmeta = ["a=b", "c>d"]

        assert_equal(self.obj.bxml.ksmeta, ["a=b", "c>d"])

    def test_set_arch(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set arch.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.arch = "x86_64"

        assert_equal(self.obj.bxml.arch, "x86_64")

    def test_set_family(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set family.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.family = "RedHatEnterpriseLinux7"

        assert_equal(self.obj.bxml.family, "RedHatEnterpriseLinux7")

    def test_set_ignore_panic(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set ignore_panic.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.ignore_panic = True

        assert_true(self.obj.bxml.ignore_panic)

    def test_set_tag(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set tag.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.tag = "RTT_ACCEPTED"

        assert_equal(self.obj.bxml.tag, "RTT_ACCEPTED")

    def test_set_retention_tag(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set retention_tag.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.retention_tag = "60days"

        assert_equal(self.obj.bxml.retention_tag, "60days")

    def test_set_jobgroup(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set job group.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.job_group = "ci-ops-pit"

        assert_equal(self.obj.bxml.job_group, "ci-ops-pit")

    def test_set_component(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set component.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.component = "rhevm"

        assert_equal(self.obj.bxml.component, "rhevm")

    def test_set_distro(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set distro.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.distro = "RHEL-7.4"

        assert_equal(self.obj.bxml.distro, "RHEL-7.4")

    def test_set_method(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set method.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.method = "nfs"

        assert_equal(self.obj.bxml.method, "nfs")

    def test_set_priority(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set priority.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.priority = "Urgent"

        assert_equal(self.obj.bxml.priority, "Urgent")

    def test_set_whiteboard(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set whiteboard.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.whiteboard = "This is the whiteboard"

        assert_equal(self.obj.bxml.whiteboard, "This is the whiteboard")


    def test_set_runid(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify get runid.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.runid = "123123456"

        assert_equal(self.obj.bxml.runid, "123123456")

    def test_set_key_values(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set key values.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.key_values = ["DISKSPACE>=500000", "HVM=1"]

        assert_equal(self.obj.bxml.key_values, ["DISKSPACE>=500000", "HVM=1"])

    def test_set_taskparam(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set task param.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.taskparam = ["RESERVETIME=172800"]

        assert_equal(self.obj.bxml.taskparam, ["RESERVETIME=172800"])

    def test_set_host_requires(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set host requires.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.host_requires_options = ["arch=x86_64", "memory>=15000"]

        assert_equal(self.obj.bxml.host_requires_options,
                     ["arch=x86_64", "memory>=15000"])

    def test_set_distro_requires(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set distro requires.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.distro_requires_options = \
            ["method=nfs", "tag=RTT_ACCEPTED"]

        assert_equal(self.obj.bxml.distro_requires_options,
                     ["method=nfs", "tag=RTT_ACCEPTED"])

    @raises(AttributeError)
    def test_set_hrname(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set hrname.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.hrname = "ThrowException"

    @raises(AttributeError)
    def test_set_paramlist(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set paramlist.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.paramlist = "ThrowException"

    @raises(AttributeError)
    def test_set_hrop(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set hrop.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.hrop = "ThrowException"

    @raises(AttributeError)
    def test_set_hrvalue(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set hrvalue.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.hrvalue = "ThowException"

    @raises(AttributeError)
    def test_set_drname(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set drname.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.drname = "ThowException"

    @raises(AttributeError)
    def test_set_drop(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set drop.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.drop = "ThowException"

    @raises(AttributeError)
    def test_set_drvalue(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set drvalue.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.drvalue = "ThowException"

    def test_set_cmd(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set cmd.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.cmd = "bkr whoami"

        assert_equal(self.obj.bxml.cmd, "bkr whoami")

    def test_set_virtual_machine(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set virtual_machine.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.virtual_machine = True

        assert_equal(self.obj.bxml.virtual_machine, True)

    def test_set_virt_capable(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set virt capable.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.virt_capable = False

        assert_equal(self.obj.bxml.virt_capable, False)

    def test_set_variant(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set variant.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.variant = "Server"

        assert_equal(self.obj.bxml.variant, "Server")

    def test_set_taskparam(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set taskparam.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.settaskparam("reservetime", {'reservetime': '50000'})

        assert_equal(self.obj.bxml.tasklist, ['reservetime'])
        assert_equal(self.obj.bxml.paramlist, [{'reservetime': '50000'}])

    def test_set_reservetime(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set reservetime.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.reservetime = 10000

        assert_equal(self.obj.bxml.reservetime, 10000)

    def test_get_paramlist(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify get paramlist.
        """
        self.obj = BeakerProvisioner(self.host)
        assert_equal(self.obj.bxml.paramlist, [])

    def test_get_tasklist(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify get tasklist.
        """
        self.obj = BeakerProvisioner(self.host)
        assert_equal(self.obj.bxml.tasklist, [])

    @raises(AttributeError)
    def test_set_tasklist(self):
        """ Create a beaker provisioner object. Verify object is instance
        of carbon.provisioners.BeakerProvisioner. Verify set tasklist.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj.bxml.tasklist = ["ThowException"]

    @raises(DockerControllerError)
    def test_create_object_bad_docker_image(self):
        """Create a beaker provisioner object. Verifies object is instance
        of carbon.provisioners.BeakerProvisioner.
        """
        self.obj = BeakerProvisioner(self.host)
        self.obj._bkr_image = "abx"
        self.obj.start_container()

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

    @raises(AttributeError)
    def test_set_provisioner_docker(self):
        """Test setting the docker controller for the provisioner class."""
        self.obj = BeakerProvisioner(self.host)
        self.obj.docker = DockerController(cname="new_Docker_controller")

    def test_get_provisioner_ansible(self):
        """Test getting ansible controller of the provisioner class."""
        self.obj = BeakerProvisioner(self.host)
        assert_is_instance(self.obj.ansible, AnsibleController)

    @raises(AttributeError)
    def test_set_provisioner_ansible(self):
        """Test setting the ansible controller for the provisioner class."""
        self.obj = BeakerProvisioner(self.host)
        self.obj.ansible = AnsibleController(self.obj.docker.name.lower())

    def test_generateBKRXML(self):
        """Test create resource for the provisioner class."""
        self.obj = BeakerProvisioner(self.host)
        bkr_xml_file = os.path.join(self.obj.host.data_folder(),
                                    self.obj._bkr_xml)

        self.obj.bxml.generate_beaker_xml(bkr_xml_file, savefile=True)
        assert_equal(
            self.obj.bxml.cmd,
            "bkr workflow-simple --arch  --whiteboard 'Carbon: , ' "\
            "--method nfs --debug --dryrun --task /distribution/reservesys "\
            "--priority Normal"
        )

    @raises(AttributeError)
    def test_generateBKRXML_invalid_taskparam(self):
        """Test create resource for the provisioner class with an invalid
        Taskparam.
        """
        self.obj = BeakerProvisioner(self.host)

        bkr_xml_file = os.path.join(self.obj.host.data_folder(),
                                    self.obj._bkr_xml)
        self.obj.bxml.taskparam = [ "time=0600"]
        self.obj.bxml.generate_beaker_xml(bkr_xml_file, savefile=True)

    def test_generateBKRXML_family_and_virt(self):
        """Test create resource for the provisioner class with family and virt
        set.
        """
        self.obj = BeakerProvisioner(self.host)
        bkr_xml_file = os.path.join(self.obj.host.data_folder(),
                                    self.obj._bkr_xml)
        self.obj.bxml.family = "RedHatEnterpriseLinux7"
        self.obj.bxml.distro = ""
        self.obj.bxml.virtual_machine = True
        self.obj.bxml.generate_beaker_xml(bkr_xml_file, savefile=True)
        assert_equal(
            self.obj.bxml.cmd,
            "bkr workflow-simple --arch  --family RedHatEnterpriseLinux7 "
            "--whiteboard 'Carbon: RedHatEnterpriseLinux7, ' --method nfs "
            "--debug --dryrun --task /distribution/reservesys "
            "--priority Normal"
        )
