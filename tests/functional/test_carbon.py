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
    Unit tests to test carbon.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from nose.tools import assert_equal, assert_is_instance, raises

from carbon import Carbon
from carbon.core import CarbonException
from carbon.helpers import file_mgmt


class TestCarbon(object):
    """Unit test to test carbon module."""

    @staticmethod
    def test_create_carbon_object():
        """Test creating a new carbon object. It will verify the object
        created is an instance of the carbon class.
        """
        obj = Carbon(__name__)
        assert_is_instance(obj, Carbon)

    @staticmethod
    def test_change_carbon_name():
        """Test changing the carbon name after the carbon object was created.
        It will verify the name attribute has the same value that was set.
        """
        obj = Carbon(__name__)
        assert_equal(obj.name, __name__)
        obj.name = 'my_scenario'
        assert_equal(obj.name, 'my_scenario')

    @staticmethod
    def test_load_yaml():
        """Test carbons function to load a scenario descriptor (yaml) file into
        the carbon object.
        """
        obj = Carbon(__name__)
        obj.load_from_yaml('assets/scenario.yaml')

    @staticmethod
    def test_load_yaml_with_missing_section():
        """Test carbons function to load a scenario descriptor (yaml) file with
        a missing required section. An exception will be raised.
        """
        obj = Carbon(__name__)
        obj.load_from_yaml('assets/invalid_scenario.yaml')
