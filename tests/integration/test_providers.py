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
import os
import ast
from copy import deepcopy
from nose.tools import assert_true, assert_false, assert_is_instance, raises
from nose.plugins.attrib import attr
from unittest import TestCase

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
scenario_description_cred = file_mgmt('r', 'assets/scenario_nocreds.yaml')


def read_data(file_location):
    myvars = {}
    with open(file_location) as myfile:
        for line in myfile:
            if "=" in line:
                name = line.split("=")[0]
                var = line.split("=")[1]
                myvars[name.strip()] = var
    return myvars


class TestOpenstack(TestCase):
    """Unit tests to test carbon provider ~ openstack.

    Majority of the tests for Openstack provider are validating the parameters
    a user would declare for a resource to be created in Openstack.

    Mock up data is supplied and used to perform all positive and negative
    testing.
    """

    if os.getenv("CARBON_SETTINGS") is not None:
        _credentials = ast.literal_eval(read_data(os.environ["CARBON_SETTINGS"])["CREDENTIALS"].strip())[1]
        _cp_scenario_description = dict(scenario_description_cred)
    else:
        _cp_scenario_description = dict(scenario_description)
        _credentials = _cp_scenario_description.pop('credentials')[0]
    _host = _cp_scenario_description.pop('provision')[0]
    _osp = OpenstackProvider()

    def setUp(self):
        """Tasks to be performed before each test case."""
        self._osp.set_credentials(self._credentials)

    @attr('creds_required')
    def test_flavor(self):
        """Test the validate flavor method. This test performs the following:
            1. Flavor defined and is a valid flavor.
            2. Flavor defined and is a invalid flavor.
        """
        key = '%sflavor' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        assert_true(self._osp.validate_flavor(cp_parameters.pop(key)))
        cp_parameters[key] = 3
        assert_true(self._osp.validate_flavor(cp_parameters.pop(key)))
        cp_parameters[key] = -1
        assert_false(self._osp.validate_flavor(cp_parameters.pop(key)))

    def test_image(self):
        """Test the validate image method. This test performs the following:
            1. Image defined and is a valid image.
            2. Image defined and is a invalid image.
        """
        key = '%simage' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        assert_true(self._osp.validate_image(cp_parameters.pop(key)))
        cp_parameters[key] = 'my_image_123'
        assert_false(self._osp.validate_image(cp_parameters.pop(key)))

    def test_networks(self):
        """Test the validate networks method. This test performs the following:
            1. Networks defined and are valid networks.
            2. Networks defined and are invalid networks.
        """
        key = '%snetworks' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        assert_true(self._osp.validate_networks(cp_parameters.pop(key)))
        cp_parameters[key] = ['local-network']
        assert_false(self._osp.validate_networks(cp_parameters.pop(key)))

    def test_keypair(self):
        """Test the validate keypair method. This test performs the following:
            1. Keypair defined and is a valid keypair.
            2. Keypair defined and is a invalid keypair.
        """
        key = '%skeypair' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        assert_true(self._osp.validate_keypair(cp_parameters[key]))
        cp_parameters[key] = 'carbon-123'
        assert_false(self._osp.validate_keypair(cp_parameters[key]))

    def test_floating_ip_pool(self):
        """Test the validate floating ip pool method. This test performs the
        following:
            1. Floating ip pool defined and is a valid floating ip pool.
            2. Floating ip pool defined and is a invalid floating ip pool.
        """
        key = '%sfloating_ip_pool' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        assert_true(self._osp.validate_floating_ip_pool(cp_parameters[key]))
        cp_parameters[key] = '192.168.1.0/22'
        assert_false(self._osp.validate_floating_ip_pool(cp_parameters[key]))
