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

import unittest

import os
from flask.config import Config
from nose import SkipTest
from nose.tools import raises

from carbon import Carbon
from carbon.helpers import file_mgmt
from carbon.provisioners import BeakerProvisioner, OpenshiftProvisioner
from carbon.provisioners.beaker import BeakerProvisionerError
from carbon.provisioners.openshift import OpenshiftProvisionerError
from carbon.resources import Host


class TestOpenshiftProvisioner(unittest.TestCase):

    def setUp(self):
        """Test fixture setup."""
        if 'integration' in os.getcwd():
            _file = os.path.join(os.getcwd(), '../assets/scenario.yaml')
        else:
            _file = os.path.join(os.getcwd(), 'assets/scenario.yaml')
        descriptor = file_mgmt('r', _file)

        # get resource under test
        for host in descriptor['provision']:
            if host['provider'].lower() == 'openshift':
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
            if item['name'].lower() == 'openshift':
                credentials = item
                break
        del _credentials

        # create carbon object for config attribute
        cbn = Carbon(__name__, assets_path="assets")

        # create the host object
        self.host['provider_creds'] = [credentials]
        self.host = Host(config=cbn.config, parameters=self.host)

        # instantiate openshift provider class
        self.provider = OpenshiftProvisioner(self.host)

    def tearDown(self):
        """Test fixture teardown"""
        pass

    @SkipTest
    def test_valid_password_authentication(self):
        # disabled since valid authentication is required and its not
        # available to have a generic account for openshift
        self.provider.host.provider._credentials['username'] = 'username'
        self.provider.host.provider._credentials['password'] = 'password'

    @raises(OpenshiftProvisionerError)
    def test_invalid_password_authentication(self):
        self.provider.authenticate()

    @SkipTest
    def test_valid_token_authentication(self):
        # disabled since valid authentication is required and its not
        # available to have a generic account for openshift
        # tokens are also time based
        self.provider.host.provider._credentials['token'] = \
            'w3fsadfadsfszdcsf2Vasdfc1j7O4XFTkqVu3TdvreM'
        self.provider.authenticate()

    @raises(OpenshiftProvisionerError)
    def test_invalid_token_authentication(self):
        self.provider.host.provider._credentials['token'] = 'abcitseasyas123'
        self.provider.authenticate()

    @SkipTest
    def test_select_valid_project(self):
        # disabled since valid authentication is required and its not
        # available to have a generic account for openshift
        self.provider.authenticate()
        self.provider.select_project()

    @raises(OpenshiftProvisionerError)
    def test_select_invalid_project(self):
        self.provider.authenticate()
        self.provider.select_project()


class TestBeakerProvisioner(unittest.TestCase):

    @staticmethod
    def remove_beaker_config():
        """Remove beaker config."""
        conf = os.path.join(os.path.expanduser('~'), '.beaker_client/config')
        if os.path.isfile(conf):
            os.remove(conf)

    def setUp(self):
        """Test fixture setup."""
        if 'integration' in os.getcwd():
            _file = os.path.join(os.getcwd(), '../assets/scenario.yaml')
            _assets = os.path.join(os.getcwd(), '../assets')
        else:
            _file = os.path.join(os.getcwd(), 'assets/scenario.yaml')
            _assets = os.path.join(os.getcwd(), 'assets')
        descriptor = file_mgmt('r', _file)

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

        # get assets path
        if os.getenv('CARBON_ASSETS_PATH'):
            assets = os.getenv('CARBON_ASSETS_PATH')
        else:
            assets = _assets

        # create carbon object for config attribute
        self.cbn = Carbon(__name__, assets_path=assets)

        # create the host object
        self.host['provider_creds'] = [credentials]
        self.host = Host(config=self.cbn.config, parameters=self.host)

        # add host to carbon object
        self.cbn.scenario.add_hosts(self.host)

        # remove beaker config before test execution
        self.remove_beaker_config()

    def tearDown(self):
        """Test fixture teardown."""
        self.remove_beaker_config()

    @SkipTest
    def test_valid_password_authentication(self):
        # disabled since valid authentication is required and its not
        # available to have a generic account for beaker
        self.provider = BeakerProvisioner(self.host)
        self.provider.authenticate()

    @raises(BeakerProvisionerError)
    def test_invalid_password_authentication(self):
        self.host.provider.credentials['username'] = 'kingbob'
        self.host.provider.credentials['password'] = 'stuart'
        self.provider = BeakerProvisioner(self.host)
        self.provider.authenticate()

    def test_valid_kerberos_authentication(self):
        if 'username' in self.host.provider.credentials:
            del self.host.provider.credentials['username']
        if 'password' in self.host.provider.credentials:
            del self.host.provider.credentials['password']
        self.cbn._copy_assets()
        self.provider = BeakerProvisioner(self.host)
        self.provider.authenticate()

    @raises(BeakerProvisionerError)
    def test_invalid_kerberos_authentication(self):
        if 'username' in self.host.provider.credentials:
            del self.host.provider.credentials['username']
        if 'password' in self.host.provider.credentials:
            del self.host.provider.credentials['password']
        self.host.provider.credentials['keytab'] = 'abcitseasyas123'
        self.host.provider.credentials['keytab_principal'] = 'abcitseasyas123'
        self.provider = BeakerProvisioner(self.host)
        self.provider.authenticate()

    def test_create_valid_xml(self):
        if 'username' in self.host.provider.credentials:
            del self.host.provider.credentials['username']
        if 'password' in self.host.provider.credentials:
            del self.host.provider.credentials['password']
        self.cbn._copy_assets()
        self.provider = BeakerProvisioner(self.host)
        self.provider.authenticate()
        self.provider.gen_bkr_xml()

    def test_submit_job(self):
        if 'username' in self.host.provider.credentials:
            del self.host.provider.credentials['username']
        if 'password' in self.host.provider.credentials:
            del self.host.provider.credentials['password']
        self.cbn._copy_assets()
        self.provider = BeakerProvisioner(self.host)
        self.provider.authenticate()
        self.provider.gen_bkr_xml()
        self.provider.submit_bkr_xml()
        self.provider.cancel_job()

    def test_create_machine(self):
        if 'username' in self.host.provider.credentials:
            del self.host.provider.credentials['username']
        if 'password' in self.host.provider.credentials:
            del self.host.provider.credentials['password']
        self.cbn._copy_assets()
        self.provider = BeakerProvisioner(self.host)
        self.provider.create()
        self.provider.delete()
