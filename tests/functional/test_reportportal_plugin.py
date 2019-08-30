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
    tests.test_reportportal_plugin

    Unit tests for testing reportportal plugin.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""


import pytest
import mock
import json
import os
from carbon.importers.ext import ReportPortalPlugin
from carbon.utils.config import Config
from carbon.resources import Report, Execute
from carbon.exceptions import CarbonReportError
from carbon.helpers import exec_local_cmd
from carbon.core import ImporterPlugin


@pytest.fixture(scope='class')
def config():
    config_file = '../assets/carbon.cfg'
    os.environ['CARBON_SETTINGS'] = config_file
    config = Config()
    config.load()
    return config


@pytest.fixture(scope='class')
def artifact_locations():
    artifacts = dict()
    artifacts['artifacts/host01'] = ['test.xml']
    artifacts['artifacts/host02'] = ['sample2.xml']

    return artifacts


@pytest.fixture(scope='class')
def execute(artifact_locations, config):
    return Execute(
        name='rp_execute',
        parameters=dict( artifact_locations=artifact_locations,
                         executor='runner',
                         hosts='host1')
    )


@pytest.fixture(scope='class')
def default_params(execute):
    params = dict(executes=[execute],
                  provider = dict(name='reportportal',
                                  credential='reportportal-creds',
                                  rp_project='carbon_1',
                                  service=True,
                                  launch_name='carbon_launch',
                                  launch_description='carbon_launch_desc',
                                  tags=['tag1','tag2'],
                                  merge_launches=True,
                                  auto_dashboard=True,
                                  simple_xml=False
                                  )
                  )
    return params


@pytest.fixture(scope='class')
def report(default_params, config):
    return Report(
        name='test.xml',
        config=config,
        importer='reportportal',
        parameters=default_params,


    )


@pytest.fixture(scope='class')
def default_profile_params(report):
    temp_dict = report.profile()
    temp_dict.update(data_folder='/tmp')
    temp_dict.update(workspace='/tmp')
    temp_dict.update(provider_credentials= dict(rp_url='https://test.com/rp',
                                                api_token='1234-5678-9018',
                                                service_url='https://test_service_rp.com/rp'))
    temp_dict.update(artifacts=[])
    temp_dict.update(config_params={})
    return temp_dict


@pytest.fixture(scope='class')
def reportportal_plugin(default_profile_params):
    return ReportPortalPlugin(default_profile_params)


class TestReportPortalPlugin(object):

    @staticmethod
    def test_reportportal_plugin_constructor(reportportal_plugin):
        assert isinstance(reportportal_plugin, ReportPortalPlugin)

    @staticmethod
    def test_create_rp_payload_dir_1(reportportal_plugin):
        reportportal_plugin.artifacts=['/payload_medium/results', '/payload_medium/results/test.xml']
        assert reportportal_plugin._create_rp_payload_dir() == '/payload_medium'

    @staticmethod
    def test_create_rp_payload_dir_2(reportportal_plugin):
        reportportal_plugin.artifacts=['/payload_medium/results/test.xml']
        assert reportportal_plugin._create_rp_payload_dir() == '/payload_medium'

    @staticmethod
    def test_create_rp_payload_dir_3(reportportal_plugin):
        reportportal_plugin.artifacts=['/payload_medium/test1.xml', '/payload_medium/test.xml']
        assert reportportal_plugin._create_rp_payload_dir() == '/tmp/rp_payload'

    @staticmethod
    def test_convert_params_rp_json(reportportal_plugin):
        rp_json_file = reportportal_plugin._convert_params_to_rp_json()
        with open(rp_json_file) as data_file:
            data_loaded = json.load(data_file)
        assert data_loaded['reportportal']['project'] == 'carbon_1'
        assert data_loaded['reportportal']['launch']['name'] == 'carbon_launch'
        assert data_loaded['rp_preproc']['service_url'] == 'https://test_service_rp.com/rp'

    @staticmethod
    def test_validate_rp_json_path_exist_1(reportportal_plugin):
        os.system('touch /tmp/test_config.json')
        assert reportportal_plugin._validate_rp_json_path_exist('test_config.json') == '/tmp/test_config.json'

    @staticmethod
    def test_validate_rp_json_path_exist_2(reportportal_plugin):
        with pytest.raises(CarbonReportError,  match='Report Portal Config json file not found'):
            reportportal_plugin._validate_rp_json_path_exist('test_config1.json')


    @staticmethod
    def test_validate_rp_json_1(reportportal_plugin):
        with pytest.raises(CarbonReportError, match='Error with json'):
            reportportal_plugin._validate_rp_json('../assets/rp_wrong_syntax.json')

    @staticmethod
    def test_validate_rp_json_2(reportportal_plugin):
        for i in range(1, 5):
            file_name = '../assets/rp_wrong_config_' + str(i) + '.json'
            with pytest.raises(CarbonReportError, match='value in the rp config file cannot be empty'):
                reportportal_plugin._validate_rp_json(file_name)






