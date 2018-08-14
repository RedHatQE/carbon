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

from nose.tools import assert_equal, assert_is_instance, raises, assert_true,\
    nottest

from carbon import Carbon
from carbon.constants import RESULTS_FILE
from carbon.resources.host import CarbonHostError


class TestCarbon(TestCase):
    """Unit test to test carbon module."""

    def setUp(self):
        self.env = EnvironmentVarGuard()
        self.env.set('CARBON_SETTINGS', os.path.join(os.getcwd(), 'workspace/carbon.cfg'))

    def test_create_carbon_object(self):
        """Test creating a new carbon object. It will verify the object
        created is an instance of the carbon class.
        """
        obj = Carbon(__name__)
        assert_is_instance(obj, Carbon)

    def test_load_yaml(self):
        """Test carbons function to load a scenario descriptor (yaml) file into
        the carbon object.
        """
        obj = Carbon(__name__)
        # apply templating before loading the data
        scenario_data = open("workspace/scenario.yaml")
        obj.load_from_yaml(scenario_data)

    def test_load_scenario_with_host_name_set_wrongly(self):
        """Test carbons function to load a scenario descriptor (yaml) file into
        the carbon object.
        """
        obj = Carbon(__name__)
        with self.assertRaises(CarbonHostError) as cm:
            scenario_data = open("workspace/invalid_scenario_provider_name_error.yaml")
            obj.load_from_yaml(scenario_data)
        raised_exception = cm.exception
        self.assertEqual(raised_exception.message,
                         ('The os_name parameter for machine_1 should not be set'
                          ' as it is under the framework\'s control'))

    def test_load_yaml_with_missing_section(self):
        """Test carbons function to load a scenario descriptor (yaml) file with
        a missing required section. An exception will be raised.
        """
        obj = Carbon(__name__)
        scenario_data = open("workspace/invalid_scenario.yaml")
        obj.load_from_yaml(scenario_data)

    @staticmethod
    def test_set_carbon_log_level():
        """Test creating a carbon object with declaring the log level."""
        cbn = Carbon(__name__, log_level='debug')
        assert_equal(cbn.config["LOG_LEVEL"], 'debug')

    @staticmethod
    def test_set_carbon_data_folder():
        """Test creating a carbon object with declaring the data folder."""
        data_folder = os.path.join(os.getcwd(), '.workspace')
        cbn = Carbon(__name__, data_folder=data_folder)
        assert_equal(cbn.data_folder, os.path.join(data_folder, cbn.uid))

    @staticmethod
    def test_set_carbon_workspace():
        """Test creating a carbon object with the workspace path set."""
        workspace_path = "workspace"
        cbn = Carbon(__name__, workspace=workspace_path)
        assert_equal(cbn.workspace, workspace_path)

    @staticmethod
    def test_results_file_property():
        """Test carbons property for returning its scenario results file."""
        cbn = Carbon(__name__)
        f = os.path.join('.workspace', cbn.uid, RESULTS_FILE)
        assert_equal(cbn.results_file, f)
