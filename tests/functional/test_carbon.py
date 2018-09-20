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
    tests.test_carbon

    Unit tests for testing carbon module.

    :copyright: (c) 2017 Red Hat, Inc.
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
from carbon.resources import Host


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
        carbon = Carbon(data_folder='/tmp', workspace='/tmp')
        assert '/tmp' in carbon.config['DATA_FOLDER']
        assert carbon.workspace == '/tmp'

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
        carbon.load_from_yaml('')

    @staticmethod
    def test_carbon_load_from_yaml_02():
        data = template_render('../assets/descriptor.yml', os.environ)
        carbon = Carbon(data_folder='/tmp')
        carbon.load_from_yaml(data)

    @staticmethod
    def test_carbon_load_from_yaml_03():
        data = template_render('../assets/descriptor.yml', os.environ)
        carbon = Carbon(data_folder='/tmp')
        carbon.config['CREDENTIALS'] = [{'name': 'provider'}]
        carbon.load_from_yaml(data)

    @staticmethod
    def test_carbon_load_from_yaml_04():
        data = template_render('../assets/descriptor.yml', os.environ)
        carbon = Carbon(data_folder='/tmp')
        carbon.load_from_yaml(data)

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
    def test_load_resource(default_host_params):
        carbon = Carbon(data_folder='/tmp')
        params = copy.deepcopy(default_host_params)
        carbon.scenario.add_credentials(params['provider_creds'][0])
        carbon._load_resources(Host, [params])
