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
    tests.test_helpers

    Unit tests for testing carbon helpers.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import pytest
import os
from carbon.constants import TASKLIST
from carbon.resources.assets import Asset
from carbon.resources.reports import Report
from carbon.resources.executes import Execute
from carbon._compat import ConfigParser
from carbon.utils.config import Config
from carbon.exceptions import CarbonError, HelpersError
from carbon.helpers import DataInjector, validate_render_scenario, set_task_class_concurrency, \
    mask_credentials_password, sort_tasklist, find_artifacts_on_disk, walk_results_directory


@pytest.fixture(scope='class')
def data_injector():
    class Host(object):
        def __init__(self):
            self.name = 'node01'
            self.random = '123'
            self.random_01 = ['123']
            self.metadata = {
                'k1': 'v1',
                'k2': ['item1', 'item2'],
                'k3': {'k1': 'v1'},
                'k4': {'k1': [{'sk1': 'sv1'}]},
                'k5': [{'k1': 'v1'}]
            }

    return DataInjector([Host()])


@pytest.fixture(scope='class')
def task_concurrency_config():
    config_file = '../assets/carbon.cfg'
    cfgp = ConfigParser()
    cfgp.read(config_file)
    cfgp.set('task_concurrency','provision','True')
    cfgp.set('task_concurrency','report','True')
    with open(config_file, 'w') as cf:
        cfgp.write(cf)
    os.environ['CARBON_SETTINGS'] = config_file
    config = Config()
    config.load()
    return config


@pytest.fixture(scope='class')
def task_host(task_concurrency_config):
    params=dict(groups='test_group',
                ip_address='1.2.3.4')
    host = Asset(name='Host01',
         config=task_concurrency_config,
         parameters=params)
    return host


@pytest.fixture(scope='class')
def task_report(task_concurrency_config):
    e_params = dict(description='description', hosts='test', executor='runner')
    ex = Execute(name='dummy_execute', parameters=e_params)
    r_params=dict(importer='dummy', executes=[ex])
    report = Report(name='/tmp/dummy.xml',
                 config=task_concurrency_config,
                 parameters=r_params)
    return report


@pytest.fixture(scope='function')
def os_creds():
    return dict(auth_url='http://test', username='tester', password='changeme')


@pytest.fixture(scope='function')
def rp_creds():
    return dict(rp_url='http://test', api_token='1234-456-78912-4567')


@pytest.fixture(scope='function')
def aws_creds():
    return dict(aws_access_key_id='ABCDEFG', aws_secret_access_key='abc123456defg')

@pytest.fixture(scope='class')
def data_folder():
    data_folder = '/tmp/1'
    os.system('mkdir /tmp/1 /tmp/1/artifacts /tmp/1/artifacts/localhosts /tmp/1/artifacts/localhosts/payload_eg '
              '/tmp/1/artifacts/localhosts/payload_eg/results /tmp/.results /tmp/.results/artifacts /tmp/.results/logs')
    os.system('touch /tmp/1/artifacts/localhosts/payload_eg/results/junit_example.xml '
              '/tmp/.results/junit2.xml /tmp/1/junit3.xml')
    return data_folder


class TestDataInjector(object):

    def test_constructor(self, data_injector):
        assert isinstance(data_injector, DataInjector)

    def test_valid_host(self, data_injector):
        h = data_injector.host_exist('node01')
        assert getattr(h, 'name') == 'node01'

    def test_invalid_host(self, data_injector):
        with pytest.raises(CarbonError) as ex:
            data_injector.host_exist('null')

        assert 'Node null not found!' in ex.value.args

    def test_inject_uc01(self, data_injector):
        cmd = data_injector.inject('cmd { node01.random }')
        assert 'cmd 123' == cmd

    def test_inject_uc02(self, data_injector):
        cmd = data_injector.inject('cmd { node01.metadata.k1 }')
        assert 'cmd v1' == cmd

    def test_inject_uc03(self, data_injector):
        cmd = data_injector.inject('cmd { node01.metadata.k2[1] }')
        assert 'cmd item2' == cmd

    def test_inject_uc04(self, data_injector):
        cmd = data_injector.inject('cmd { node01.metadata.k3.k1 }')
        assert 'cmd v1' == cmd

    def test_inject_uc05(self, data_injector):
        cmd = data_injector.inject('cmd { node01.metadata.k4.k1[0].sk1 }')
        assert 'cmd sv1' == cmd

    def test_inject_uc06(self, data_injector):
        cmd = data_injector.inject('cmd { node01.metadata.k5[0].k1 }')
        assert 'cmd v1' == cmd

    def test_inject_uc07(self, data_injector):
        with pytest.raises(CarbonError):
            data_injector.inject('cmd { node01.metadata.null }')

    def test_inject_uc08(self, data_injector):
        data_injector.inject('cmd { node01.random_01[0] }')

    def test_inject_uc09(self, data_injector):
        with pytest.raises(AttributeError) as ex:
            data_injector.inject('cmd { node01.null }')
        assert 'null not found in host node01!' in ex.value.args

    def test_inject_uc10(self, data_injector):
        cmd = data_injector.inject('cmd')
        assert cmd == 'cmd'

    def test_inject_jsonpath_support_uc1(self, data_injector):
        cmd = data_injector.inject('cmd { .spec }')
        assert cmd == 'cmd { .spec }'

    def test_inject_jsonpath_support_uc2(self, data_injector):
        cmd = data_injector.inject('cmd { $ }')
        assert cmd == 'cmd { $ }'

    def test_inject_jsonpath_support_uc3(self, data_injector):
        cmd = data_injector.inject('cmd { @ }')
        assert cmd == 'cmd { @ }'

    def test_inject_jsonpath_support_uc4(self, data_injector):
        cmd = data_injector.inject('cmd { range. }')
        assert cmd == 'cmd { range. }'

    def test_inject_jsonpath_support_uc5(self, data_injector):
        cmd = data_injector.inject('cmd { test: dictionary }')
        assert cmd == 'cmd { test: dictionary }'

    def test_inject_jsonpath_support_uc6(self, data_injector):
        cmd = data_injector.inject("cmd { 'test': 'dictionary' }")
        assert cmd == "cmd { 'test': 'dictionary' }"

    def test_inject_dictionary_01(self, data_injector):
        cmd = data_injector.inject_dictionary(dict(ans_var='{ node01.random }'))
        assert cmd.get('ans_var') == '123'

    def test_inject_dictionary_02(self, data_injector):
        cmd = data_injector.inject_dictionary(dict(ans_var=['{ node01.random }']))
        assert cmd.get('ans_var')[-1] == '123'

    def test_inject_dictionary_03(self, data_injector):
        cmd = data_injector.inject_dictionary(
            dict(ans_var={'{ node01.metadata.k1 }': '{ node01.random_01[0] }'})
        )
        assert cmd.get('ans_var').get('v1') == '123'

    def test_inject_dictionary_04(self, data_injector):
        cmd = data_injector.inject_dictionary(dict(ans_args='-c -e { node01.random } { node01.random_01[0]}'))
        assert '123' in cmd.get('ans_args')


def test_validate_render_scenario_no_include():
    result = validate_render_scenario(os.path.abspath('../assets/no_include.yml'))
    assert len(result) == 1


def test_validate_render_scenario_correct_include():
    result = validate_render_scenario('../assets/correct_include_descriptor.yml')
    assert len(result) == 2


def test_validate_render_scenario_wrong_include():
    with pytest.raises(HelpersError) as e:
        validate_render_scenario('../assets/wrong_include_descriptor.yml')


def test_validate_render_scenario_empty_include():
    with pytest.raises(HelpersError) as e:
        validate_render_scenario('../assets/descriptor.yml')


def test_set_task_concurrency_provision_is_false(host):
    for task in host.get_tasks():
        if task['task'].__task_name__ == 'provision':
            assert set_task_class_concurrency(task, host)['task'].__concurrent__ is False


def test_set_task_concurrency_report_is_false(report_resource):
    for task in report_resource.get_tasks():
        if task['task'].__task_name__ == 'report':
            assert set_task_class_concurrency(task, report_resource)['task'].__concurrent__ is False


def test_set_task_concurrency_provision_is_true(task_host):
    for task in task_host.get_tasks():
        if task['task'].__task_name__ == 'provision':
            assert set_task_class_concurrency(task, task_host)['task'].__concurrent__ is True


def test_set_task_concurrency_report_is_true(task_report):
    for task in task_report.get_tasks():
        if task['task'].__task_name__ == 'report':
            assert set_task_class_concurrency(task, task_report)['task'].__concurrent__ is True


def test_mask_credentials_password_param(os_creds):
    key_len = len(os_creds.get('password'))
    creds = mask_credentials_password(os_creds)
    assert '*' in creds.get('password') and len(creds.get('password')) == key_len


def test_mask_credentials_password_token_param(rp_creds):
    key_len = len(rp_creds.get('api_token'))
    creds = mask_credentials_password(rp_creds)
    assert '*' in creds.get('api_token') and len(creds.get('api_token')) == key_len


def test_mask_credentials_password_key_param(aws_creds):
    key_len = len(aws_creds.get('aws_secret_access_key'))
    creds = mask_credentials_password(aws_creds)
    assert '*' in creds.get('aws_secret_access_key') and len(creds.get('aws_secret_access_key')) == key_len

def test_sort_tasklist():
    user_task = ['orchestrate', 'report', 'validate', 'cleanup', 'execute', 'provision']
    assert sort_tasklist(user_task) == TASKLIST


def test_find_artifacts_on_disk_no_art_location_1(data_folder):
    assert len(find_artifacts_on_disk(data_folder, '*xml')) == 3

def test_find_artifacts_on_disk_no_art_location_2(data_folder):
    assert len(find_artifacts_on_disk(data_folder, 'junit2.xml')) == 1

def test_find_artifacts_on_disk_no_art_location_3(data_folder):
    assert len(find_artifacts_on_disk(data_folder, 'payload_eg/*')) == 1


def test_find_artifacts_on_disk_art_location_1(data_folder):
    art_location = {'artifacts/localhosts': ['payload_eg/', 'payload_eg/results',
                                             'payload_eg/results/junit_example.xml']}
    assert len(find_artifacts_on_disk(data_folder, 'junit_*.xml', art_location)) == 1


def test_find_artifacts_on_disk_art_location_2(data_folder):
    art_location = {'artifacts/localhosts': ['payload_eg/', 'payload_eg/results',
                                             'payload_eg/results/junit_example.xml']}
    assert len(find_artifacts_on_disk(data_folder, '*.xml', art_location)) == 3


def test_find_artifacts_on_disk_art_location_3(data_folder):
    art_location = {'artifacts/localhosts': ['payload_eg/', 'payload_eg/results',
                                             'payload_eg/results/junit_example.xml']}
    assert len(find_artifacts_on_disk(data_folder, 'junit3.xml', art_location)) == 1


def test_find_artifacts_on_disk_art_location_4(data_folder):
    art_location = {'artifacts/localhosts': ['payload_eg/', 'payload_eg/results',
                                             'payload_eg/results/junit_example.xml']}
    assert len(find_artifacts_on_disk(data_folder, 'hello.xml', art_location)) == 0


def test_find_artifacts_on_disk_art_location_5(data_folder):
    art_location = {'artifacts/localhosts': ['payload_eg/', 'payload_eg/results',
                                             'payload_eg/results/junit_example.xml']}
    assert len(find_artifacts_on_disk(data_folder, 'payload_eg/*', art_location)) == 3


def test_find_artifacts_on_disk_art_location_6(data_folder):
    art_location = {'artifacts/localhosts': ['payload_eg/', 'payload_eg/results',
                                             'payload_eg/results/junit_example.xml']}
    assert len(find_artifacts_on_disk(data_folder, 'payload_eg/', art_location)) == 1


def test_find_artifacts_on_disk_art_location_7(data_folder):
    art_location = {'artifacts/localhosts': ['payload_eg/', 'payload_eg/results',
                                             'payload_eg/results/junit_example.xml'],
                    '.results': ['junit2.xml']}
    assert len(find_artifacts_on_disk(data_folder, 'junit2.xml', art_location)) == 1


