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

import unittest

import os
from flask.config import Config
from nose.tools import assert_true, assert_false

from carbon.helpers import file_mgmt
from carbon.providers import OpenstackProvider


class TestOpenStack(unittest.TestCase):
    """OpenStack provider integration tests."""

    def setUp(self):
        """Test fixture setup."""
        if 'integration' in os.getcwd():
            _file = os.path.join(os.getcwd(), '../assets/scenario.yaml')
        else:
            _file = os.path.join(os.getcwd(), 'assets/scenario.yaml')
        descriptor = file_mgmt('r', _file)

        # get resource under test
        for host in descriptor['provision']:
            if host['provider'].lower() == 'openstack':
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
            if item['name'].lower() == 'openstack':
                credentials = item
                break
        del _credentials

        # instantiate openstack provider class
        self.provider = OpenstackProvider()

        # set provider credentials
        getattr(self.provider, 'set_credentials')(credentials)

    def tearDown(self):
        """Test fixture teardown."""
        pass

    def test_valid_flavor(self):
        key = '{0}flavor'.format(self.provider.__provider_prefix__)
        assert_true(self.provider.validate_flavor(self.host[key]))

    def test_invalid_flavor(self):
        assert_true(self.provider.validate_flavor(3))

    def test_valid_image(self):
        key = '{0}image'.format(self.provider.__provider_prefix__)
        assert_true(self.provider.validate_image(self.host[key]))

    def test_invalid_image(self):
        assert_false(self.provider.validate_image('my_image_123'))

    def test_valid_network(self):
        key = '{0}networks'.format(self.provider.__provider_prefix__)
        assert_true(self.provider.validate_networks(self.host[key]))

    def test_invalid_network(self):
        assert_false(self.provider.validate_networks('local'))

    def test_valid_keypair(self):
        key = '{0}keypair'.format(self.provider.__provider_prefix__)
        assert_true(self.provider.validate_keypair(self.host[key]))

    def test_invalid_keypair(self):
        assert_false(self.provider.validate_keypair('keypair-123'))

    def test_valid_floating_ip_pool(self):
        key = '{0}floating_ip_pool'.format(self.provider.__provider_prefix__)
        assert_true(self.provider.validate_floating_ip_pool(self.host[key]))

    def test_invalid_floating_ip_pool(self):
        assert_false(self.provider.validate_floating_ip_pool('192.168.1.0/22'))
