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
    Unit tests to test carbon providers.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from copy import deepcopy
from unittest import TestCase

import os
from nose.tools import assert_true, assert_false, assert_is_instance, raises

try:
    from test.test_support import EnvironmentVarGuard
except ImportError:
    from test.support import EnvironmentVarGuard

from carbon import Carbon
from carbon.helpers import file_mgmt
from carbon.providers import OpenstackProvider, OpenshiftProvider
from carbon.providers import DigitalOceanProvider, RackspaceProvider
from carbon.providers import AwsProvider, BeakerProvider

# ++++++ IGNORE PYLINT MESSAGES ++++++ #
# - Ignores method names, unit tests setUp method needs this naming standard
# pylint: disable=C0103

scenario_description = file_mgmt('r', 'assets/scenario.yaml')


class TestRackspace(TestCase):
    """Unit tests to test carbon provider ~ rackspace."""
    _rspace = RackspaceProvider()

    def test_instantiate_class(self):
        """Test whether the instantiated provider class object is an actual
        instance of the provider class."""
        assert_is_instance(self._rspace, RackspaceProvider)


class TestOpenshift(TestCase):

    """Unit tests to test carbon provider ~ openshift."""
    _cp_scenario_description = dict(scenario_description)
    _host1 = _cp_scenario_description['provision'][3]
    _host2 = _cp_scenario_description['provision'][4]
    _ocp = OpenshiftProvider()

    def setUp(self):
        self.env = EnvironmentVarGuard()
        self.env.set('CARBON_SETTINGS', os.path.join(os.getcwd(), 'assets/carbon.cfg'))

    def test_instantiate_class(self):
        """Test whether the instantiated provider class object is an actual
        instance of the provider class."""
        assert_is_instance(self._ocp, OpenshiftProvider)

    def test_name(self):
        """Test the validate name method. This test performs the following:
            1. Name undefined.
            2. Name defined and is a valid name.
            3. Name defined and is a invalid data type.
        """
        obj = Carbon(__name__)
        scenario_data = open("assets/scenario_openshift.yaml")
        obj.load_from_yaml(scenario_data)

        host = obj.scenario.hosts[0]

        assert_true(host.provider.name, 'openshift')
        assert_false(host.provider.validate_name(None))
        assert_true(host.provider.validate_name('applicationbyimage'))
        assert_false(host.provider.validate_name(['applicationbygit']))

    def test_image(self):
        """Test the validate image method. This test performs the following:
            1. Image undefined.
            2. Image is a string data type.
        """
        key = '%simage' % self._ocp.__provider_prefix__
        cp_parameters = deepcopy(self._host1)
        assert_true(self._ocp.validate_image(None))
        assert_true(self._ocp.validate_image(cp_parameters.pop(key)))

    def test_git(self):
        """Test the validate git method. This test performs the following:
            1. Git undefined.
            2. Git defined and is a valid git.
            3. Git defined and is a invalid data type.
        """
        key = '%sgit' % self._ocp.__provider_prefix__
        cp_parameters = deepcopy(self._host2)
        assert_true(self._ocp.validate_git(None))
        assert_true(self._ocp.validate_git(cp_parameters.pop(key)))
        cp_parameters[key] = ['http://github.com']
        assert_false(self._ocp.validate_git(cp_parameters.pop(key)))

    def test_template(self):
        """Test the validate template method. This test performs the following:
            1. Template undefined.
            2. Template is a string data type.
        """
        assert_true(self._ocp.validate_template(None))
        assert_true(self._ocp.validate_template('my_template.yaml'))

    def test_custom_template(self):
        """Test the validate custom template method. This test performs the
        following:
            1. Template undefined.
            2. Template is a string data type
        """
        assert_true(self._ocp.validate_custom_template(None))
        assert_true(self._ocp.validate_custom_template('my_template.yaml'))

    def test_env_vars(self):
        """Test the validate env vars method. This test performs the following:
            1. Env vars undefined.
            2. Env vars is a dict data type.
        """
        key = '%senv_vars' % self._ocp.__provider_prefix__
        cp_parameters = deepcopy(self._host1)
        assert_true(self._ocp.validate_env_vars(None))
        assert_true(self._ocp.validate_env_vars(cp_parameters.pop(key)))

    def test_build_timeout(self):
        """Test the validate build timeout method. This test performs the
        following:
            1. Build timeout undefined.
            2. Build timeout is a int data type & > 0
            3. Build timeout is a non int data type
        """
        key = '%sbuild_timeout' % self._ocp.__provider_prefix__
        cp_parameters = deepcopy(self._host2)
        assert_true(self._ocp.validate_build_timeout(None))
        assert_true(self._ocp.validate_build_timeout(cp_parameters.pop(key)))
        assert_false(self._ocp.validate_build_timeout(2.5))

    def test_labels(self):
        """Test teh validate labels method. This test performs the following:
            1. Labels undefined.
            2. Labels is not a list.
            3. Labels list does not contain dict values.
            4. Labels list does contain dict values.
            5. Labels list dict contains more than one key:value.
            6. Labels list dict contains one key:value but key:value is not
                defined correctly.
        """
        key = '%slabels' % self._ocp.__provider_prefix__
        cp_parameters = deepcopy(self._host1)
        assert_true(self._ocp.validate_labels(None))
        assert_false(self._ocp.validate_labels('label1'))
        assert_false(self._ocp.validate_labels(['label1']))
        assert_true(self._ocp.validate_labels(cp_parameters.pop(key)))
        assert_false(self._ocp.validate_labels(
            [dict(label1='label1', label2='label2')]))
        assert_false(self._ocp.validate_labels(
            [dict(label1='')]))


class TestDigitalocean(TestCase):
    """Unit tests to test carbon provider ~ digital ocean."""
    _docean = DigitalOceanProvider()

    def test_instantiate_class(self):
        """Test whether the instantiated provider class object is an actual
        instance of the provider class."""
        assert_is_instance(self._docean, DigitalOceanProvider)


class TestBeaker(TestCase):
    """Unit tests to test carbon provider ~ beaker."""
    _beaker = BeakerProvider()

    def test_instantiate_class(self):
        """Test whether the instantiated provider class object is an actual
        instance of the provider class."""
        assert_is_instance(self._beaker, BeakerProvider)

    def test_instantiate_class(self):
        """Test whether the instantiated provider class object is an actual
        instance of the provider class."""
        assert_is_instance(self._beaker, BeakerProvider)

    def test_name(self):
        """Test the validate name method. This test performs the following:
            1. Name undefined.
            2. Name is a string data type.
        """
        assert_false(self._beaker.validate_name(None))
        assert_false(self._beaker.validate_name(1))
        assert_true(self._beaker.validate_name('test_name'))

    def test_timeout(self):
        """Test the validate timeout method. This test performs the following:
            1. timeout undefined.
            2. timeout is a string data type.
        """
        assert_false(self._beaker.validate_timeout('11'))
        assert_false(self._beaker.validate_timeout(3599))
        assert_false(self._beaker.validate_timeout(172801))
        assert_false(self._beaker.validate_timeout(-6000))
        assert_true(self._beaker.validate_timeout(None))
        assert_true(self._beaker.validate_timeout(3600))
        assert_true(self._beaker.validate_timeout(172800))
        assert_true(self._beaker.validate_timeout(100001))

    def test_arch(self):
        """Test the validate arch method."""
        assert_true(self._beaker.validate_arch('x86_64'))

    def test_tag(self):
        """Test the validate tag method."""
        assert_false(self._beaker.validate_tag(11))
        assert_true(self._beaker.validate_tag(None))
        assert_true(self._beaker.validate_tag('RTT_ACCEPTED'))

    def test_family(self):
        """Test the validate family method."""
        assert_true(self._beaker.validate_family('FEDORA26'))
        assert_true(self._beaker.validate_family(None))

    def test_variant(self):
        """Test the validate variant method."""
        assert_true(self._beaker.validate_variant('workstation'))

    def test_distro(self):
        """Test the validate variant distro."""
        assert_false(self._beaker.validate_distro(11))
        assert_true(self._beaker.validate_distro(None))
        assert_true(self._beaker.validate_distro('Rhel-7'))

    def test_kernel_options(self):
        """Test the validate kernel options method."""
        assert_false(self._beaker.validate_kernel_options("isolcpus=0,5"))
        assert_true(self._beaker.validate_kernel_options(None))
        assert_true(self._beaker.validate_kernel_options(["selinux=--permisssive", "keyboard=us", "lang=us", "timezone=est"]))
        assert_true(self._beaker.validate_kernel_options([1, 2, 3]))

    def test_kernel_post_options(self):
        """Test the validate kernel post options method."""
        assert_false(self._beaker.validate_kernel_post_options("isolcpus=0,5"))
        assert_true(self._beaker.validate_kernel_post_options(None))
        assert_true(self._beaker.validate_kernel_post_options(["isolcpus=0,5", "timezone=est", "selinux=--disabled"]))
        assert_true(self._beaker.validate_kernel_post_options([1, 2, 3]))

    def test_host_requires_options(self):
        """Test the validate host requires options method."""
        assert_false(self._beaker.validate_host_requires_options(11))
        assert_true(self._beaker.validate_host_requires_options(None))
        assert_true(self._beaker.validate_host_requires_options(["arch=x86_64", "memory>=15000"]))
        assert_true(self._beaker.validate_host_requires_options([1, 2, 3]))

    def test_distro_requires_options(self):
        """Test the validate distro requires options method."""
        assert_false(self._beaker.validate_distro_requires_options(11))
        assert_true(self._beaker.validate_distro_requires_options(None))
        assert_true(self._beaker.validate_distro_requires_options(["arch=x86_64", "memory>=15000"]))
        assert_true(self._beaker.validate_distro_requires_options([1, 2, 3]))

    def test_virtual_machine(self):
        """Test the validate virtual machine method."""
        assert_false(self._beaker.validate_virtual_machine(3))
        assert_false(self._beaker.validate_virtual_machine(1))
        assert_false(self._beaker.validate_virtual_machine('True'))
        assert_true(self._beaker.validate_virtual_machine(None))
        assert_true(self._beaker.validate_virtual_machine(True))
        assert_true(self._beaker.validate_virtual_machine(False))
        assert_true(self._beaker.validate_virtual_machine(0))

    def test_virt_capable(self):
        """Test the validate virt capable method."""
        assert_false(self._beaker.validate_virt_capable(5))
        assert_false(self._beaker.validate_virt_capable(1))
        assert_false(self._beaker.validate_virt_capable('True'))
        assert_true(self._beaker.validate_virt_capable(None))
        assert_true(self._beaker.validate_virt_capable(True))
        assert_true(self._beaker.validate_virt_capable(False))
        assert_true(self._beaker.validate_virt_capable(0))

    def test_retention_tag(self):
        """Test the validate retention tag method."""
        assert_false(self._beaker.validate_retention_tag(11))
        assert_true(self._beaker.validate_retention_tag(None))
        assert_true(self._beaker.validate_retention_tag('Rhel-7'))
        assert_true(self._beaker.validate_retention_tag('Scratch'))

    def test_priority(self):
        """Test the validate priority method."""
        assert_false(self._beaker.validate_priority(11))
        assert_true(self._beaker.validate_priority(None))
        assert_true(self._beaker.validate_priority('Rhel-7'))
        assert_true(self._beaker.validate_priority('Low'))

    def test_whiteboard(self):
        """Test the validate whiteboard method."""
        assert_false(self._beaker.validate_whiteboard(11))
        assert_true(self._beaker.validate_whiteboard(None))
        assert_true(self._beaker.validate_whiteboard('Rhel-7'))
        assert_true(self._beaker.validate_whiteboard('Title of the job or job id'))

    def test_jobgroup(self):
        """Test the validate jobgoup method."""
        assert_false(self._beaker.validate_jobgroup(11))
        assert_true(self._beaker.validate_jobgroup(None))
        assert_true(self._beaker.validate_jobgroup('Rhel-7'))
        assert_true(self._beaker.validate_jobgroup('ci-ops-pit'))

    def test_key_values(self):
        """Test the validate key_values method."""
        assert_false(self._beaker.validate_key_values(11))
        assert_true(self._beaker.validate_key_values(None))
        assert_true(self._beaker.validate_key_values(["DISKSPACE>=500000", "HVM=1"]))
        assert_true(self._beaker.validate_key_values([1, 2, 3]))

    def test_username(self):
        """Test the validate username method."""
        assert_false(self._beaker.validate_username(11))
        assert_true(self._beaker.validate_username(None))
        assert_true(self._beaker.validate_username('ci-ops-pit'))

    def test_password(self):
        """Test the validate password method."""
        assert_false(self._beaker.validate_password(11))
        assert_true(self._beaker.validate_password(None))
        assert_true(self._beaker.validate_password('ci-ops-pit'))

    def test_keytab(self):
        """Test the validate keytab method."""
        assert_false(self._beaker.validate_keytab(11))
        assert_true(self._beaker.validate_keytab(None))
        assert_true(self._beaker.validate_keytab('ci-ops-pit'))

    def test_ssh_key(self):
        """Test the validate ssh_key method."""
        assert_false(self._beaker.validate_ssh_key(11))
        assert_true(self._beaker.validate_ssh_key(None))
        assert_true(self._beaker.validate_ssh_key('ci-ops-pit'))

    def test_kickstart(self):
        """Test the validate kickstart method."""
        assert_false(self._beaker.validate_kickstart(11))
        assert_true(self._beaker.validate_kickstart(None))
        assert_true(self._beaker.validate_kickstart('ci-ops-pit'))

    def test_hostname(self):
        """Test the validate hostname method."""
        assert_false(self._beaker.validate_hostname(11))
        assert_true(self._beaker.validate_hostname(None))
        assert_true(self._beaker.validate_hostname('ci-ops-pit'))

    def test_ip_address(self):
        """Test the validate ip_address method."""
        assert_false(self._beaker.validate_ip_address(11))
        assert_true(self._beaker.validate_ip_address(None))
        assert_true(self._beaker.validate_ip_address('ci-ops-pit'))

    def test_job_id(self):
        """Test the validate job_id method."""
        assert_false(self._beaker.validate_job_id(11))
        assert_true(self._beaker.validate_job_id(None))
        assert_true(self._beaker.validate_job_id('ci-ops-pit'))

    def test_taskparam(self):
        """Test the validate taskparam method."""
        assert_false(self._beaker.validate_taskparam(11))
        assert_true(self._beaker.validate_taskparam(None))
        assert_true(self._beaker.validate_taskparam(["DISKSPACE>=500000", "HVM=1"]))
        assert_true(self._beaker.validate_taskparam([1, 2, 3]))

    def test_ksmeta(self):
        """Test the validate ksmeta method."""
        assert_false(self._beaker.validate_ksmeta(11))
        assert_true(self._beaker.validate_ksmeta(None))
        assert_true(self._beaker.validate_ksmeta(["DISKSPACE>=500000", "HVM=1"]))
        assert_true(self._beaker.validate_ksmeta([1, 2, 3]))

    def test_ignore_panic(self):
        """Test the validate ignore panic method."""
        assert_false(self._beaker.validate_ignore_panic(3))
        assert_false(self._beaker.validate_ignore_panic(1))
        assert_false(self._beaker.validate_ignore_panic('True'))
        assert_true(self._beaker.validate_ignore_panic(None))
        assert_true(self._beaker.validate_ignore_panic(True))
        assert_true(self._beaker.validate_ignore_panic(False))
        assert_true(self._beaker.validate_ignore_panic(0))


class TestAws(TestCase):
    """Unit tests to test carbon provider ~ aws."""
    _aws = AwsProvider()

    def test_instantiate_class(self):
        """Test whether the instantiated provider class object is an actual
        instance of the provider class."""
        assert_is_instance(self._aws, AwsProvider)


class TestOpenstack(TestCase):
    """Unit tests to test carbon provider ~ openstack.

    Majority of the tests for Openstack provider are validating the parameters
    a user would declare for a resource to be created in Openstack.

    Mock up data is supplied and used to perform all positive and negative
    testing.
    """
    _cp_scenario_description = dict(scenario_description)
    _host = _cp_scenario_description.pop('provision')[0]
    _credentials = _cp_scenario_description.pop('credentials')[0]
    _osp = OpenstackProvider()

    def setUp(self):
        """Tasks to be performed before each test case."""
        self._osp.set_credentials(self._credentials)

    def test_instantiate_class(self):
        """Test whether the instantiated provider class object is an actual
        instance of the provider class."""
        assert_is_instance(self._osp, OpenstackProvider)

    def test_name(self):
        """Test the validate name method. This test performs the following:
            1. Name undefined.
            2. Name defined and is a valid name.
            3. Name defined and is a invalid data type.
        """
        key = 'name'
        cp_parameters = deepcopy(self._host)
        assert_false(self._osp.validate_name(None))
        assert_true(self._osp.validate_name(cp_parameters.pop(key)))
        cp_parameters[key] = ['machine1']
        assert_false(self._osp.validate_name(cp_parameters.pop(key)))

    def test_flavor(self):
        """Test the validate flavor method. This test performs the following:
            1. Flavor undefined.
            2. Flavor defined and is a invalid data type(s).
        """
        key = '%sflavor' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        assert_false(self._osp.validate_flavor(None))
        cp_parameters[key] = [3]
        assert_false(self._osp.validate_flavor(cp_parameters.pop(key)))

    def test_image(self):
        """Test the validate image method. This test performs the following:
            1. Image undefined.
            2. Image defined and is a invalid data type(s).
        """
        key = '%simage' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        assert_false(self._osp.validate_image(None))
        cp_parameters[key] = 1234
        assert_false(self._osp.validate_image(cp_parameters.pop(key)))

    def test_networks(self):
        """Test the validate networks method. This test performs the following:
            1. Networks undefined.
            2. Networks defined and networks are a invalid data type(s).
        """
        key = '%snetworks' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        assert_false(self._osp.validate_networks(None))
        cp_parameters['os_networks'] = "local-network"
        assert_false(self._osp.validate_networks(cp_parameters.pop(key)))

    def test_keypair(self):
        """Test the validate keypair method. This test performs the following:
            1. Keypair undefined.
            2. Keypair defined and is a invalid data type(s).
        """
        key = '%skeypair' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        assert_false(self._osp.validate_keypair(None))
        # assert_true(self._osp.validate_keypair(cp_parameters[key]))
        # cp_parameters[key] = 'carbon-123'
        # assert_false(self._osp.validate_keypair(cp_parameters[key]))
        cp_parameters[key] = ['carbon-123']
        assert_false(self._osp.validate_keypair(cp_parameters[key]))

    def test_floating_ip_pool(self):
        """Test the validate floating ip pool method. This test performs the
        following:
            1. Floating ip pool undefined.
            2. Floating ip pool defined and is a invalid data type(s).
        """
        key = '%sfloating_ip_pool' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        cp_parameters[key] = ['192.168.1.0/22']
        assert_false(self._osp.validate_floating_ip_pool(cp_parameters[key]))
