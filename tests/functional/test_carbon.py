# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Red Hat, Inc.
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
    tests.test_carbon

    Unit tests for testing carbon module.

    :copyright: (c) 2020 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import copy
import os
import sys

import mock
import pytest
import yaml

from carbon import Carbon
from carbon.constants import RESULTS_FILE
from carbon.exceptions import CarbonError
from carbon.helpers import template_render


class TestCarbon(object):
    @staticmethod
    def test_create_carbon_instance_01():
        carbon = Carbon(data_folder='/tmp')
        assert isinstance(carbon, Carbon)

    @staticmethod
    def test_create_carbon_instance_02():
        carbon = Carbon(log_level='info', data_folder='/tmp')
        assert carbon.config['LOG_LEVEL'] == 'info'

    @staticmethod
    def test_create_carbon_instance_03():
        """verifies carbon instance is created when data folder and workspace is provided and kwargs in none"""
        carbon = Carbon(data_folder='/tmp', workspace='/tmp')
        assert '/tmp' in carbon.config['DATA_FOLDER']
        assert carbon.workspace == '/tmp'
        assert carbon.carbon_options == {}

    @staticmethod
    def test_create_carbon_instance_with_labels():
        """this test is to verify carbon instance gets created when labels/skip_labels are passed"""
        carbon = Carbon(data_folder='/tmp', workspace='/tmp', labels=('lab1', 'lab2'), skip_labels=('lab3',))
        assert carbon.carbon_options['labels'] == ('lab1', 'lab2')
        assert carbon.carbon_options['skip_labels'] == ('lab3', )

    @staticmethod
    @mock.patch.object(os, 'makedirs')
    @pytest.mark.filterwarnings('ignore::DeprecationWarning')
    def test_create_carbon_instance_04(mock_method):
        with pytest.raises(CarbonError):
            mock_method.side_effect = IOError()
            Carbon(data_folder='/tmp', workspace='/tmp')

    @staticmethod
    @mock.patch.object(os, 'makedirs')
    def test_create_carbon_instance_05(mock_method):
        with pytest.raises(CarbonError):
            mock_method.side_effect = IOError()
            mock_method.side_effect.errno = 13
            Carbon(data_folder='/tmp', workspace='/tmp')

    @staticmethod
    def test_data_folder_property():
        carbon = Carbon(data_folder='/tmp')
        assert carbon.data_folder == carbon.config['DATA_FOLDER']

    @staticmethod
    def test_results_file_property():
        carbon = Carbon(data_folder='/tmp')
        assert carbon.results_file == os.path.join(
            carbon.data_folder, RESULTS_FILE)

    @staticmethod
    @mock.patch.object(yaml, 'safe_load')
    def test_carbon_load_from_yaml_01(mock_method):
        mock_method.return_value = {}
        carbon = Carbon(data_folder='/tmp')
        carbon.load_from_yaml([''])

    @staticmethod
    def test_carbon_load_from_yaml_02():
        data = list()
        data.append(template_render('../assets/descriptor.yml', os.environ))
        carbon = Carbon(data_folder='/tmp')
        carbon.load_from_yaml(data)

    @staticmethod
    def test_carbon_load_from_yaml_03():
        data = list()
        data.append(template_render('../assets/descriptor.yml', os.environ))
        carbon = Carbon(data_folder='/tmp')
        carbon.config['CREDENTIALS'] = [{'name': 'provider'}]
        carbon.load_from_yaml(data)

    @staticmethod
    def test_carbon_load_from_yaml_04():
        data = list()
        data.append(template_render('../assets/descriptor.yml', os.environ))
        carbon = Carbon(data_folder='/tmp')
        carbon.load_from_yaml(data)

    @staticmethod
    def test_carbon_load_from_yaml_05():
        data = list()
        data.append(template_render('../assets/correct_include_descriptor.yml', os.environ))
        data.append(template_render('../assets/common.yml', os.environ))
        carbon = Carbon(data_folder='/tmp')
        carbon.load_from_yaml(data)
        assert carbon.scenario.child_scenarios

    @staticmethod
    def test_name_property_01():
        carbon = Carbon(data_folder='/tmp')
        assert carbon.name == 'carbon'

    @staticmethod
    def test_name_property_02():
        carbon = Carbon(import_name='__main__', data_folder='/tmp')
        assert carbon.name != 'carbon'

    @staticmethod
    def test_name_property_03():
        sys.modules['__main__'].__file__ = None
        carbon = Carbon(import_name='__main__', data_folder='/tmp')
        assert carbon.name == '__main__'

    @staticmethod
    def test_static_inventory_folder():
        carbon = Carbon(import_name='__main__', data_folder='/tmp')
        assert carbon.static_inv_dir
        assert carbon.config['INVENTORY_FOLDER'] == '/tmp'

    @staticmethod
    def test_validate_labels_01(scenario_labels):
        """ this test verifies validate_labels throws error when wrong labels is provided"""
        carbon = Carbon(data_folder='/tmp', workspace='/tmp', labels=('lab1',))
        carbon.scenario = scenario_labels
        with pytest.raises(CarbonError) as ex:
            carbon._validate_labels()
        assert "No resources were found corresponding to the label/skip_label lab1. " \
               "Please check the labels provided during the run match the ones in "\
               "scenario descriptor file" in ex.value.args

    def test_validate_labels_02(scenario_labels):
        """ this test verifies validate_labels throws error when wrong skip_labels is provided"""
        carbon = Carbon(data_folder='/tmp', workspace='/tmp', skip_labels=('lab1','label2'))
        with pytest.raises(CarbonError) as ex:
            carbon._validate_labels()
        assert "No resources were found corresponding to the label/skip_label lab1. " \
               "Please check the labels provided during the run match the ones in "\
               "scenario descriptor file" in ex.value.args
