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

import os

from carbon import Carbon
from carbon.constants import RESULTS_FILE
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
        carbon = Carbon(data_folder='/tmp', workspace='/tmp')
        assert '/tmp' in carbon.config['DATA_FOLDER']
        assert carbon.workspace == '/tmp'

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
    def test_carbon_load_from_yaml_01():
        data = template_render('../assets/descriptor.yml', os.environ)
        carbon = Carbon(data_folder='/tmp')
        carbon.load_from_yaml(data)

    @staticmethod
    def test_carbon_load_from_yaml_02():
        data = template_render('../assets/descriptor.yml', os.environ)
        carbon = Carbon(data_folder='/tmp')
        carbon.config['CREDENTIALS'] = [{'name': 'provider'}]
        carbon.load_from_yaml(data)

    @staticmethod
    def test_carbon_load_from_yaml_03():
        data = template_render('../assets/descriptor.yml', os.environ)
        carbon = Carbon(data_folder='/tmp')
        carbon.load_from_yaml(data)

    @staticmethod
    def test_name_property():
        carbon = Carbon(data_folder='/tmp')
        assert carbon.name == 'carbon'

