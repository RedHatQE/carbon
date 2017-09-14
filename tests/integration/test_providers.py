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
    carbon.tests.integration.test_providers

    Integration tests to test carbon providers. Integration tests require
    credential details to communicate with various providers
    (openstack, beaker, etc.). You will need to configure a conf file which
    will hold all your provider credentials. Please see the example conf file
    at carbon/tests/assets/carbon.cfg. Once you have your conf file setup, you
    will want to export the following environment variable:

        export CARBON_SETTINGS=/etc/carbon/carbon.cfg

    You will want to replace the path to the location of your conf file. These
    tests will read credentials from that file. Once this is all set you can
    run the tests!

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from copy import deepcopy
from unittest import TestCase

import os
from flask.config import Config
from nose.tools import assert_true, assert_false

try:
    from test.test_support import EnvironmentVarGuard
except ImportError:
    from test.support import EnvironmentVarGuard

from carbon.helpers import file_mgmt
from carbon.providers import OpenstackProvider


scenario_description = file_mgmt('r', 'assets/scenario.yaml')
scenario_description_cred = file_mgmt('r', 'assets/scenario_nocreds.yaml')


class TestOpenstack(TestCase):
    """Integration tests to test openstack provider.

    The purpose of this class is to test different methods of the provider
    class that require communicating to openstack.
    """

    # load descriptor file and carbon settings if applicable
    if os.getenv('CARBON_SETTINGS'):
        # load conf file
        config = Config(os.getcwd())
        config.from_pyfile(os.environ['CARBON_SETTINGS'], silent=True)
        _credentials = config['CREDENTIALS']
        _cp_scenario_description = dict(scenario_description_cred)
    else:
        _cp_scenario_description = dict(scenario_description)
        _credentials = _cp_scenario_description.pop('credentials')[0]

    _host = _cp_scenario_description.pop('provision')[0]
    _osp = OpenstackProvider()

    def setUp(self):
        """Setup tasks to be run before each test case."""
        for item in self._credentials:
            if 'openstack' in item['name']:
                self._osp.set_credentials(item)
                break

    def test_flavor(self):
        """Test the openstack provider validate_flavor method.

        This test will communicate with openstack to test whether a flavor
        provided is valid or invalid.
        """
        key = '%sflavor' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        assert_true(self._osp.validate_flavor(cp_parameters.pop(key)))
        cp_parameters[key] = 3
        assert_true(self._osp.validate_flavor(cp_parameters.pop(key)))
        cp_parameters[key] = -1
        assert_false(self._osp.validate_flavor(cp_parameters.pop(key)))

    def test_image(self):
        """Test the openstack provider validate_image method.

        This test will communicate with openstack to test whether a image
        provided is valid or invalid.
        """
        key = '%simage' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        assert_true(self._osp.validate_image(cp_parameters.pop(key)))
        cp_parameters[key] = 'my_image_123'
        assert_false(self._osp.validate_image(cp_parameters.pop(key)))

    def test_networks(self):
        """Test the openstack provider validate_networks method.

        This test will communicate with openstack to test whether a network
        provided is valid or invalid.
        """
        key = '%snetworks' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        assert_true(self._osp.validate_networks(cp_parameters.pop(key)))
        cp_parameters[key] = ['local-network']
        assert_false(self._osp.validate_networks(cp_parameters.pop(key)))

    def test_keypair(self):
        """Test the openstack provider validate_keypair method.

        This test will communicate with openstack to test whether a key pair
        provided is valid or invalid.
        """
        key = '%skeypair' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        assert_true(self._osp.validate_keypair(cp_parameters[key]))
        cp_parameters[key] = 'carbon-123'
        assert_false(self._osp.validate_keypair(cp_parameters[key]))

    def test_floating_ip_pool(self):
        """Test the openstack provider validate_floating_ip_pool method.

        This test will communicate with openstack to test whether a floating
        ip pool provided is valid or invalid.
        """
        key = '%sfloating_ip_pool' % self._osp.__provider_prefix__
        cp_parameters = deepcopy(self._host)
        assert_true(self._osp.validate_floating_ip_pool(cp_parameters[key]))
        cp_parameters[key] = '192.168.1.0/22'
        assert_false(self._osp.validate_floating_ip_pool(cp_parameters[key]))
