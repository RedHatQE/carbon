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
    Unit tests to test carbon helpers.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from unittest import TestCase

import os

try:
    from test.test_support import EnvironmentVarGuard
except ImportError:
    from test.support import EnvironmentVarGuard

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

from nose.tools import assert_is_instance, assert_equal, assert_is, raises
from nose.tools import assert_not_equal, assert_is_not, assert_is_none
from nose.tools import nottest

from carbon import Carbon
from carbon._compat import string_types
from carbon.helpers import file_mgmt, gen_random_str
from carbon.helpers import get_ansible_inventory_script
from carbon.helpers import get_provisioner_class, get_provisioners_classes
from carbon.helpers import get_provider_class, get_providers_classes
from carbon.providers import OpenstackProvider
from carbon.provisioners import LinchpinProvisioner


class TestLogging(TestCase):
    """Unit test to test carbon logging."""

    def setUp(self):
        self.env = EnvironmentVarGuard()
        self.env.set('CARBON_SETTINGS', os.path.join(os.getcwd(), 'assets/carbon.cfg'))

    @staticmethod
    @nottest
    def test_logger_cache():
        """Test carbons logger."""
        cbn = Carbon(__name__)
        logger1 = cbn.logger
        assert_is(cbn.logger, logger1)
        assert_equal(cbn.name, __name__)
        cbn.logger_name = __name__ + '/test_logger_cache'
        assert_is_not(cbn.logger, logger1)


class TestFileManagement(TestCase):
    """Unit tests to test carbons file management function."""

    @staticmethod
    @raises(Exception)
    def test_unknown_file_operation():
        """Test carbons file management function with an invalid operaton. An
        exception will be raised.
        """
        file_mgmt('x', 'test.yml')

    @staticmethod
    @raises(Exception)
    def test_file_not_found():
        """Test carbons file management function attempting to read a file
        that does not exist. An exception will be raised.
        """
        file_mgmt('r', 'test.yml')

    @staticmethod
    def test_yaml_file_extension():
        """Test carbons file management function attempting to read/write a
        yaml file type.
        """
        _file = "test_{}.yml".format(gen_random_str(8))
        _data = {'name': 'carbon', 'group': [{'name': 'group'}]}
        try:
            file_mgmt('w', _file, _data)
            assert_is_instance(file_mgmt('r', _file), dict)
        finally:
            try:
                os.remove(_file)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise

    @staticmethod
    def test_json_file_extension():
        """Test carbons file management function attempting to read/write a
        json file type.
        """
        _file = "test_{}.json".format(gen_random_str(8))
        _data = {'name': 'carbon', 'group': [{'name': 'group'}]}
        try:
            file_mgmt('w', _file, _data)
            assert_is_instance(file_mgmt('r', _file), dict)
        finally:
            try:
                os.remove(_file)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise

    @staticmethod
    def test_txt_file_extension():
        """Test carbons file management function attempting to read/write a
        txt file type.
        """
        _file = "test_{}.txt".format(gen_random_str(8))
        _data = "Carbon project"
        try:
            file_mgmt('w', _file, _data)
            assert_equal(file_mgmt('r', _file), "Carbon project")
        finally:
            try:
                os.remove(_file)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise

    @staticmethod
    def test_ini_file_extension():
        """Test carbons file management function attempting to read/write a
        ini file type.
        """
        _file = "test_{}.ini".format(gen_random_str(8))
        cfg1, cfg2 = ConfigParser(), ConfigParser()
        cfg1.add_section('Carbon')
        cfg1.set('Carbon', 'Team', 'PIT')
        try:
            file_mgmt('w', _file, cfg_parser=cfg1)
            file_mgmt('r', _file, cfg_parser=cfg2)
            assert_is_instance(cfg2, ConfigParser)
        finally:
            try:
                os.remove(_file)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise

class TestGetModuleClasses(TestCase):
    """Unit tests to test carbon functions that get classes or a class from
    carbon modules.
    """

    @staticmethod
    def test_get_provisioners_classes():
        """Test the function to get all provisioner classes. It checks if the
        length of the list returned is not zero.
        """
        provisioners = get_provisioners_classes()
        assert_not_equal(len(provisioners), 0)

    @staticmethod
    def test_get_provisioner_class():
        """Test the function to get a provisioner class. It will attempt to
        get the linchpin provisioner class and then verify that the class
        returned is the linchpin provisioner class.
        """
        provisioner = get_provisioner_class('linchpin')
        assert_is(provisioner, LinchpinProvisioner)

    @staticmethod
    def test_get_providers_classes():
        """Test the function to get all provider classes. It checks if the
        length of the list returned is not zero.
        """
        providers = get_providers_classes()
        assert_not_equal(len(providers), 0)

    @staticmethod
    def test_get_provider_class():
        """Test the function to get a provider class. It will attempt to get
        the openstack provider class and then verify that the class returned
        is the openstack provider class.
        """
        provider = get_provider_class('openstack')
        assert_is(provider, OpenstackProvider)


def test_get_ansible_inv_script():
    """Test the function to get the absolute path to the ansible dynamic
    inventory script for a given provider.
    """
    _script = get_ansible_inventory_script('docker')
    assert_is_instance(_script, string_types)
    _script = get_ansible_inventory_script('gru')
    assert_is_none(_script)
