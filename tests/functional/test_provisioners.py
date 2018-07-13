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
from carbon.helpers import file_mgmt
from carbon.provisioners.beaker import BeakerProvisioner
from carbon.provisioners.openshift import OpenshiftProvisioner
from carbon.provisioners.openstack import OpenstackProvisioner
from carbon.resources import Host

try:
    from test.test_support import EnvironmentVarGuard
except ImportError:
    from test.support import EnvironmentVarGuard

from flask.config import Config

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
        obj.create_labels()
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

    @staticmethod
    def remove_beaker_config():
        """Remove beaker config."""
        conf = os.path.join(os.path.expanduser('~'), '.beaker_client/config')
        if os.path.isfile(conf):
            os.remove(conf)

    def setUp(self):
        """Test fixture setup."""
        if 'functional' in os.getcwd():
            _file = os.path.join(os.getcwd(), '../assets/scenario.yaml')
        else:
            _file = os.path.join(os.getcwd(), 'assets/scenario.yaml')
        descriptor = file_mgmt('r', _file)

        # get resource under test
        for host in descriptor['provision']:
            if host['provider'].lower() == 'openstack':
                self.host = host
                break

        # get resource under test
        for host in descriptor['provision']:
            if host['provider'].lower() == 'beaker':
                self.host = host
                break

        # initialize credentials variable
        credentials = dict()

        # get provider credentials
        if os.getenv('CARBON_SETTINGS'):
            # read from conf file
            config = Config(os.getcwd())
            config.from_pyfile(os.getenv('CARBON_SETTINGS'), silent=True)
            _credentials = config['CREDENTIALS']
        else:
            # read from descriptor
            _credentials = descriptor['credentials']

        # select credentials
        for item in _credentials:
            if item['name'].lower() == 'beaker':
                credentials = item
                break
        del _credentials

        # determine abs path to carbon config
        for f in CARBON_CFGS:
            if os.path.exists(f):
                CARBON_CFG = f

        # set carbon settings env variable
        self.env = EnvironmentVarGuard()
        self.env.set('CARBON_SETTINGS', CARBON_CFG)

        # create carbon object for config attribute
        self.cbn = Carbon(__name__, assets_path='assets')

        # create the host object
        self.host['provider_creds'] = [credentials]
        self.host = Host(config=self.cbn.config, parameters=self.host)

        # add host to carbon object
        self.cbn.scenario.add_hosts(self.host)

        # instantiate beaker provider class
        self.provider = BeakerProvisioner(self.host)

        # remove beaker config before test execution
        self.remove_beaker_config()

    def tearDown(self):
        """Test fixture teardown."""
        self.remove_beaker_config()

    def test_create_object(self):
        assert_is_instance(self.provider, BeakerProvisioner)

    @raises(AttributeError)
    def test_set_provisioner_name(self):
        self.provider.name = 'beaker'

    def test_get_provisioner_name(self):
        assert_equal(self.provider.name, 'beaker')

    def test_set_kernel_options(self):
        options = ['selinux=--permisssive', 'keyboard=us',
                   'lang=us', 'timezone=est']
        self.provider.bkr_xml.kernel_options = options
        assert_equal(self.provider.bkr_xml.kernel_options, options)

    def test_set_kernel_post_options(self):
        options = ['isolcpus=0,5']
        self.provider.bkr_xml.kernel_post_options = options
        assert_equal(self.provider.bkr_xml.kernel_post_options, options)

    def test_set_kickstart(self):
        kickstart = 'rhel7-7.3-ci-cloud.ks'
        self.provider.bkr_xml.kickstart = kickstart
        assert_equal(self.provider.bkr_xml.kickstart, kickstart)

    def test_set_ksmeta(self):
        meta = ['a=b', 'c>d']
        self.provider.bkr_xml.ksmeta = meta
        assert_equal(self.provider.bkr_xml.ksmeta, meta)

    def test_set_architecture(self):
        architecture = 'x86_64'
        self.provider.bkr_xml.arch = architecture
        assert_equal(self.provider.bkr_xml.arch, architecture)

    def test_set_family(self):
        family = 'RedHatEnterpriseLinux7'
        self.provider.bkr_xml.family = family
        assert_equal(self.provider.bkr_xml.family, family)

    def test_set_ignore_panic(self):
        self.provider.bkr_xml.ignore_panic = True
        assert_true(self.provider.bkr_xml.ignore_panic)

    def test_set_tag(self):
        tag = 'RTT_ACCEPTED'
        self.provider.bkr_xml.tag = tag
        assert_equal(self.provider.bkr_xml.tag, tag)

    def test_set_retention_tag(self):
        tag = '60days'
        self.provider.bkr_xml.retention_tag = tag
        assert_equal(self.provider.bkr_xml.retention_tag, tag)

    def test_set_job_group(self):
        group = 'ci-ops-pit'
        self.provider.bkr_xml.jobgroup = group
        assert_equal(self.provider.bkr_xml.jobgroup, group)

    def test_set_component(self):
        component = 'rhv'
        self.provider.bkr_xml.component = component
        assert_equal(self.provider.bkr_xml.component, component)

    def test_set_distro(self):
        distro = 'RHEL-7.5'
        self.provider.bkr_xml.distro = distro
        assert_equal(self.provider.bkr_xml.distro, distro)

    def test_set_method(self):
        method = 'nfs'
        self.provider.bkr_xml.method = method
        assert_equal(self.provider.bkr_xml.method, method)

    def test_set_priority(self):
        priority = 'Urgent'
        self.provider.bkr_xml.priority = priority
        assert_equal(self.provider.bkr_xml.priority, priority)

    def test_set_whiteboard(self):
        whiteboard = 'Content goes here'
        self.provider.bkr_xml.whiteboard = whiteboard
        assert_equal(self.provider.bkr_xml.whiteboard, whiteboard)

    def test_set_run_id(self):
        run_id = '123456789'
        self.provider.bkr_xml.runid = run_id
        assert_equal(self.provider.bkr_xml.runid, run_id)

    def test_set_key_values(self):
        values = ['DISKSPACE>=500000', 'HVM=1']
        self.provider.bkr_xml.key_values = values
        assert_equal(self.provider.bkr_xml.key_values, values)

    def test_set_task_param(self):
        param = ['RESERVETIME=172800']
        self.provider.bkr_xml.taskparam = param
        assert_equal(self.provider.bkr_xml.taskparam, param)

    def test_set_host_requires(self):
        options = ['arch=x86_64', 'memory>=15000']
        self.provider.bkr_xml.host_requires_options = options
        assert_equal(self.provider.bkr_xml.host_requires_options, options)

    def test_set_distro_requires(self):
        options = ['method=nfs', 'tag=RTT_ACCEPTED']
        self.provider.bkr_xml.distro_requires_options = options
        assert_equal(self.provider.bkr_xml.distro_requires_options, options)

    @raises(AttributeError)
    def test_set_hrname(self):
        self.provider.bkr_xml.hrname = 'minions'

    @raises(AttributeError)
    def test_set_param_list(self):
        self.provider.bkr_xml.paramlist = 'stuart'

    @raises(AttributeError)
    def test_set_hrop(self):
        self.provider.bkr_xml.hrop = 'gru'

    @raises(AttributeError)
    def test_set_hrvalue(self):
        self.provider.bkr_xml.hrvalue = 'kevin'

    @raises(AttributeError)
    def test_set_drname(self):
        self.provider.bkr_xml.drname = 'bob'

    @raises(AttributeError)
    def test_set_drop(self):
        self.provider.bkr_xml.drop = 'illumination'

    @raises(AttributeError)
    def test_set_drvalue(self):
        self.provider.bkr_xml.drvalue = 'banana'

    def test_set_cmd(self):
        command = 'bkr whoami'
        self.provider.bkr_xml.cmd = command
        assert_equal(self.provider.bkr_xml.cmd, command)

    def test_set_virtual_machine(self):
        flag = True
        self.provider.bkr_xml.virtual_machine = flag
        assert_equal(self.provider.bkr_xml.virtual_machine, flag)

    def test_set_virt_capable(self):
        flag = False
        self.provider.bkr_xml.virt_capable = flag
        assert_equal(self.provider.bkr_xml.virt_capable, flag)

    def test_set_variant(self):
        variant = 'Server'
        self.provider.bkr_xml.variant = variant
        assert_equal(self.provider.bkr_xml.variant, variant)

    def test_set_reserve_time(self):
        total = 10000
        self.provider.bkr_xml.reservetime = total
        assert_equal(self.provider.bkr_xml.reservetime, total)

    def test_get_param_list(self):
        assert_equal(self.provider.bkr_xml.paramlist, list())

    def test_get_task_list(self):
        assert_equal(self.provider.bkr_xml.taskparam, list())

    @raises(AttributeError)
    def test_set_tasklist(self):
        self.provider.bkr_xml.tasklist = ['marvel']

    def test_create_xml(self):
        xml_file = os.path.join(self.provider.host.data_folder,
                                self.provider.job_xml)
        self.provider.bkr_xml.generate_beaker_xml(xml_file, savefile=True)
        assert_equal(
            self.provider.bkr_xml.cmd,
            "bkr workflow-simple --arch  --whiteboard 'Carbon: , ' "
            "--method nfs --debug --dryrun --task /distribution/reservesys "
            "--priority Normal"
        )

    @raises(AttributeError)
    def test_create_xml_with_invalid_task_param(self):
        xml_file = os.path.join(self.provider.host.data_folder,
                                self.provider.job_xml)
        self.provider.bkr_xml.taskparam = ['time=0600']
        self.provider.bkr_xml.generate_beaker_xml(xml_file, savefile=True)

    def test_create_xml_family_and_virt(self):
        xml_file = os.path.join(self.provider.host.data_folder,
                                self.provider.job_xml)
        self.provider.bkr_xml.family = 'RedHatEnterpriseLinux7'
        self.provider.bkr_xml.distro = ''
        self.provider.bkr_xml.virtual_machine = True
        self.provider.bkr_xml.generate_beaker_xml(xml_file, savefile=True)
        assert_equal(
            self.provider.bkr_xml.cmd,
            "bkr workflow-simple --arch  --family RedHatEnterpriseLinux7 "
            "--whiteboard 'Carbon: RedHatEnterpriseLinux7, ' --method nfs "
            "--debug --dryrun --task /distribution/reservesys "
            "--priority Normal"
        )
