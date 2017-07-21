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
from unittest import TestCase

import os

try:
    from test.test_support import EnvironmentVarGuard
except ImportError:
    from test.support import EnvironmentVarGuard

from nose.tools import assert_equal, assert_is_instance, raises, assert_true

from carbon import Carbon
from carbon.constants import STATUS_FILE, RESULTS_FILE
from carbon.resources.host import CarbonHostError


class TestCarbon(TestCase):
    """Unit test to test carbon module."""

    def setUp(self):
        self.env = EnvironmentVarGuard()
        self.env.set('CARBON_SETTINGS', os.path.join(os.getcwd(), 'assets/carbon.cfg'))

    def test_create_carbon_object(self):
        """Test creating a new carbon object. It will verify the object
        created is an instance of the carbon class.
        """
        obj = Carbon(__name__)
        assert_is_instance(obj, Carbon)

    def test_change_carbon_name(self):
        """Test changing the carbon name after the carbon object was created.
        It will verify the name attribute has the same value that was set.
        """
        obj = Carbon(__name__)
        assert_equal(obj.name, __name__)
        obj.name = 'my_scenario'
        assert_equal(obj.name, 'my_scenario')

    def test_load_yaml(self):
        """Test carbons function to load a scenario descriptor (yaml) file into
        the carbon object.
        """
        obj = Carbon(__name__)
        obj.load_from_yaml('assets/scenario.yaml')

    def test_load_scenario_with_host_name_set_wrongly(self):
        """Test carbons function to load a scenario descriptor (yaml) file into
        the carbon object.
        """
        obj = Carbon(__name__)
        with self.assertRaises(CarbonHostError) as cm:
            obj.load_from_yaml('assets/invalid_scenario_provider_name_error.yaml')
        raised_exception = cm.exception
        self.assertEqual(raised_exception.message,
                         ('The os_name parameter for machine1 should not be set'
                          ' as it is under the framework\'s control'))

    def test_load_yaml_with_missing_section(self):
        """Test carbons function to load a scenario descriptor (yaml) file with
        a missing required section. An exception will be raised.
        """
        obj = Carbon(__name__)
        obj.load_from_yaml('assets/invalid_scenario.yaml')

    @staticmethod
    def test_set_carbon_log_type():
        """Test creating a carbon object with declaring the log type."""
        cbn = Carbon(__name__, log_type='stream')
        assert_equal(cbn.logger_type, 'stream')

    @staticmethod
    def test_set_carbon_log_level():
        """Test creating a carbon object with declaring the log level."""
        cbn = Carbon(__name__, log_level='debug')
        assert_equal(cbn.log_level, 'debug')

    @staticmethod
    def test_set_carbon_cleanup_level():
        """Test creating a carbon object with declaring the cleanup level."""
        cbn = Carbon(__name__, cleanup='always')
        assert_equal(cbn.cleanup, 'always')

    @staticmethod
    def test_set_carbon_data_folder():
        """Test creating a carbon object with declaring the data folder."""
        data_folder = os.path.join(os.getcwd(), '.workspace')
        cbn = Carbon(__name__, data_folder=data_folder)
        assert_equal(cbn.data_folder, os.path.join(data_folder, cbn.uid))

    @staticmethod
    def test_set_carbon_assets():
        """Test creating a carbon object with the assets path set."""
        assets_path = "assets"
        cbn = Carbon(__name__, assets_path=assets_path)
        assert_equal(cbn.assets_path, assets_path)

    @staticmethod
    def test_status_file_property():
        """Test carbons property for returning its scenario status file."""
        cbn = Carbon(__name__)
        f = os.path.join(os.getcwd(), '.workspace', cbn.uid, STATUS_FILE)
        assert_equal(cbn.status_file, f)

    @staticmethod
    def test_results_file_property():
        """Test carbons property for returning its scenario results file."""
        cbn = Carbon(__name__)
        f = os.path.join(os.getcwd(), '.workspace', cbn.uid, RESULTS_FILE)
        assert_equal(cbn.results_file, f)


class TestResultsMixin(TestCase):
    """Unit tests to test carbon results mixin class."""

    def setUp(self):
        self.env = EnvironmentVarGuard()
        self.env.set('CARBON_SETTINGS', os.path.join(os.getcwd(), 'assets/carbon.cfg'))

    @staticmethod
    def test_get_results():
        """Test getting results for carbon scenario."""
        cbn = Carbon(__name__)
        assert_is_instance(cbn.results, dict)

    @staticmethod
    @raises(ValueError)
    def test_set_results():
        """Test setting results for carbon scenario."""
        cbn = Carbon(__name__)
        cbn.results = dict()

    @staticmethod
    def test_get_tasks():
        """Test getting tasks for carbon scenario."""
        cbn = Carbon(__name__)
        assert_is_instance(cbn.tasks, list)

    @staticmethod
    def test_set_tasks():
        """Test setting tasks for carbon scenario."""
        cbn = Carbon(__name__)
        cbn.tasks = ['provision']
        assert_true('provision', cbn.tasks)

    @staticmethod
    def test_read_write_status_file():
        """Test read/write status file for carbon scenario."""
        cbn = Carbon(__name__)
        status_file = 'status.yaml'
        cbn.write_status_file(status_file)
        assert_true(os.path.isfile(status_file))
        cbn.read_status_file(status_file)
        assert_is_instance(cbn.results, dict)
        os.remove(status_file)

    @staticmethod
    def test_update_results():
        """Test method to update results for carbon scenario."""
        cbn = Carbon(__name__)
        task1 = dict(resource=cbn.scenario)
        task2 = dict(host=cbn.scenario)
        context = dict(_taskrunner=dict())
        cbn.update_results('provision', task1, 0, context)
        cbn.update_results('provision', task2, 0, context)
