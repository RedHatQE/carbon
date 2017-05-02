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
import os

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

from nose.tools import assert_is_instance, assert_equal, assert_is, raises
from nose.tools import assert_not_equal

from carbon import Carbon
from carbon.helpers import file_mgmt
from carbon.helpers import get_provisioner_class, get_provisioners_classes
from carbon.helpers import get_provider_class, get_providers_classes
from carbon.providers import OpenstackProvider
from carbon.provisioners import LinchpinProvisioner


class TestLogging(object):
    """Unit test to test carbon logging."""

    @staticmethod
    def test_logger_cache():
        cbn = Carbon(__name__)
        logger1 = cbn.logger
        assert cbn.logger is logger1
        assert cbn.name == __name__
        cbn.logger_name = __name__ + '/test_logger_cache'
        assert cbn.logger is not logger1


class TestFileManagement(object):
    """Unit tests to test carbons file management function."""

    @staticmethod
    @raises(Exception)
    def test_unknown_file_operation():
        file_mgmt('x', 'test.yml')

    @staticmethod
    @raises(Exception)
    def test_file_not_found():
        file_mgmt('r', 'test.yml')

    @staticmethod
    def test_yaml_file_extension():
        _file = "test.yml"
        _data = {'name': 'carbon', 'group': [{'name': 'group'}]}
        try:
            file_mgmt('w', _file, _data)
            assert_is_instance(file_mgmt('r', _file), dict)
        finally:
            os.remove(_file)

    @staticmethod
    def test_json_file_extension():
        _file = "test.json"
        _data = {'name': 'carbon', 'group': [{'name': 'group'}]}
        try:
            file_mgmt('w', _file, _data)
            assert_is_instance(file_mgmt('r', _file), dict)
        finally:
            os.remove(_file)

    @staticmethod
    def test_txt_file_extension():
        _file = "test.txt"
        _data = "Carbon project"
        try:
            file_mgmt('w', _file, _data)
            assert_equal(file_mgmt('r', _file), "Carbon project")
        finally:
            os.remove(_file)

    @staticmethod
    def test_ini_file_extension():
        _file = "test.ini"
        cfg1, cfg2 = ConfigParser(), ConfigParser()
        cfg1.add_section('Carbon')
        cfg1.set('Carbon', 'Team', 'PIT')
        try:
            file_mgmt('w', _file, cfg_parser=cfg1)
            file_mgmt('r', _file, cfg_parser=cfg2)
            assert_is_instance(cfg2, ConfigParser)
        finally:
            os.remove(_file)


class TestGetModuleClasses(object):
    """Unit tests to test carbon functions that get classes or a class from
    carbon modules.
    """

    @staticmethod
    def test_get_provisioners_classes():
        provisioners = get_provisioners_classes()
        assert_not_equal(len(provisioners), 0)

    @staticmethod
    def test_get_provisioner_class():
        provisioner = get_provisioner_class('linchpin')
        assert_is(provisioner, LinchpinProvisioner)

    @staticmethod
    def test_get_providers_classes():
        providers = get_providers_classes()
        assert_not_equal(len(providers), 0)

    @staticmethod
    def test_get_provider_class():
        provider = get_provider_class('openstack')
        assert_is(provider, OpenstackProvider)
