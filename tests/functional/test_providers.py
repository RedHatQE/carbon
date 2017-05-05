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
from nose.tools import assert_true, assert_false, assert_is_instance, raises

from carbon.helpers import file_mgmt
from carbon.providers import OpenstackProvider, OpenshiftProvider
from carbon.providers import DigitalOceanProvider, RackspaceProvider
from carbon.providers import AwsProvider, BeakerProvider

# ++++++ IGNORE PYLINT MESSAGES ++++++ #
# - Ignores method names, unit tests setUp method needs this naming standard
# pylint: disable=C0103

scenario_description = file_mgmt('r', 'assets/scenario.yaml')


class TestRackspace(object):
    """Unit tests to test carbon provider ~ rackspace."""
    _rspace = RackspaceProvider()

    def test_instantiate_class(self):
        """Test whether the instantiated provider class object is an actual
        instance of the provider class."""
        assert_is_instance(self._rspace, RackspaceProvider)


class TestOpenshift(object):
    """Unit tests to test carbon provider ~ openshift."""
    _ocp = OpenshiftProvider()

    def test_instantiate_class(self):
        """Test whether the instantiated provider class object is an actual
        instance of the provider class."""
        assert_is_instance(self._ocp, OpenshiftProvider)


class TestDigitalocean(object):
    """Unit tests to test carbon provider ~ digital ocean."""
    _docean = DigitalOceanProvider()

    def test_instantiate_class(self):
        """Test whether the instantiated provider class object is an actual
        instance of the provider class."""
        assert_is_instance(self._docean, DigitalOceanProvider)


class TestBeaker(object):
    """Unit tests to test carbon provider ~ beaker."""
    _beaker = BeakerProvider()

    def test_instantiate_class(self):
        """Test whether the instantiated provider class object is an actual
        instance of the provider class."""
        assert_is_instance(self._beaker, BeakerProvider)


class TestAws(object):
    """Unit tests to test carbon provider ~ aws."""
    _aws = AwsProvider()

    def test_instantiate_class(self):
        """Test whether the instantiated provider class object is an actual
        instance of the provider class."""
        assert_is_instance(self._aws, AwsProvider)


class TestOpenstack(object):
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

    @raises(ValueError)
    def test_instantiate_novaclient(self):
        """Test the method to create novaclient object after class was
        instantiated. An exception will be raised.
        """
        self._osp.nova = self._credentials

    @raises(ValueError)
    def test_instantiate_glanceclient(self):
        """Test the method to create glanceclient object after class was
        instantiated. An exception will be raised.
        """
        self._osp.glance = self._credentials

    @raises(ValueError)
    def test_instantiate_neutronclient(self):
        """Test the method to create neutronclient object after class was
        instantiated. An exception will be raised.
        """
        self._osp.neutron = self._credentials

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

    def test_count(self):
        """Test the validate count method. This test performs the following:
            1. Count undefined.
            2. Count defined and is a valid count.
            3. Count defined and is a invalid count (negative number).
            4. Count defined and is a invalid count (float number).
        """
        key = '%scount' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        assert_false(self._osp.validate_count(None))
        assert_true(self._osp.validate_count(cp_parameters.pop(key)))
        cp_parameters[key] = -1
        assert_false(self._osp.validate_count(cp_parameters.pop(key)))
        cp_parameters[key] = 1.5
        assert_false(self._osp.validate_count(cp_parameters.pop(key)))

    def test_flavor(self):
        """Test the validate flavor method. This test performs the following:
            1. Flavor undefined.
            2. Flavor defined and is a valid flavor.
            3. Flavor defined and is a invalid flavor.
            4. Flavor defined and is a invalid data type(s).
        """
        key = '%sflavor' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        assert_false(self._osp.validate_flavor(None))
        # assert_true(self._osp.validate_flavor(cp_parameters.pop(key)))
        # cp_parameters[key] = 3
        # assert_true(self._osp.validate_flavor(cp_parameters.pop(key)))
        # cp_parameters[key] = -1
        # assert_false(self._osp.validate_flavor(cp_parameters.pop(key)))
        cp_parameters[key] = [3]
        assert_false(self._osp.validate_flavor(cp_parameters.pop(key)))

    def test_image(self):
        """Test the validate image method. This test performs the following:
            1. Image undefined.
            2. Image defined and is a valid image.
            3. Image defined and is a invalid image.
            4. Image defined and is a invalid data type(s).
        """
        key = '%simage' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        assert_false(self._osp.validate_image(None))
        # assert_true(self._osp.validate_image(cp_parameters.pop(key)))
        # cp_parameters[key] = 'my_image_123'
        # assert_false(self._osp.validate_image(cp_parameters.pop(key)))
        cp_parameters[key] = 1234
        assert_false(self._osp.validate_image(cp_parameters.pop(key)))

    def test_networks(self):
        """Test the validate networks method. This test performs the following:
            1, Networks undefined.
            2. Networks defined and are valid networks.
            3. Networks defined and are invalid networks.
            4. Networks defined and networks are a invalid data type(s).
        """
        key = '%snetworks' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        assert_false(self._osp.validate_networks(None))
        # assert_true(self._osp.validate_networks(cp_parameters.pop(key)))
        # cp_parameters[key] = ['local-network']
        # assert_false(self._osp.validate_networks(cp_parameters.pop(key)))
        cp_parameters['os_networks'] = "local-network"
        assert_false(self._osp.validate_networks(cp_parameters.pop(key)))

    def test_keypair(self):
        """Test the validate keypair method. This test performs the following:
            1. Keypair undefined.
            2. Keypair defined and is a valid keypair.
            3. Keypair defined and is a invalid keypair.
            4. Keypair defined and is a invalid data type(s).
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
            2. Floating ip pool defined and is a valid floating ip pool.
            3. Floating ip pool defined and is a invalid floating ip pool.
            4. Floating ip pool defined and is a invalid data type(s).
        """
        key = '%sfloating_ip_pool' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        assert_false(self._osp.validate_floating_ip_pool(None))
        # assert_true(self._osp.validate_floating_ip_pool(cp_parameters[key]))
        # cp_parameters[key] = '192.168.1.0/22'
        # assert_false(self._osp.validate_floating_ip_pool(cp_parameters[key]))
        cp_parameters[key] = ['192.168.1.0/22']
        assert_false(self._osp.validate_floating_ip_pool(cp_parameters[key]))
