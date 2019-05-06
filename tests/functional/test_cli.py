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
    tests.test_cli

    Unit tests for testing carbon cli.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import mock
import pytest
import oyaml as yaml
from carbon import Carbon
from carbon.cli import print_header, carbon
from click.testing import CliRunner


@pytest.fixture(scope='class')
def runner():
    return CliRunner()


class TestCli(object):
    @staticmethod
    def test_print_header():
        assert print_header() is None

    @staticmethod
    def test_carbon_create(runner):
        results = runner.invoke(carbon, ['-v', 'create'])
        assert results.exit_code != 0

    @staticmethod
    def test_invalid_validate(runner):
        results = runner.invoke(carbon, ['validate', '-s', 'cdf.yml'])
        assert 'You have to provide a valid scenario file.' in results.output

    @staticmethod
    @mock.patch.object(Carbon, 'run')
    def test_valid_validate(mock_method, runner):
        mock_method.return_value = 0
        results = runner.invoke(
            carbon, ['validate', '-s', '../assets/descriptor.yml',
                     '-d', '/tmp']
        )
        assert results.exit_code == 0

    @staticmethod
    def test_invalid_run(runner):
        results = runner.invoke(carbon, ['run', '-s', 'cdf.yml'])
        assert 'You have to provide a valid scenario file.' in results.output

    @staticmethod
    @mock.patch.object(Carbon, 'run')
    def test_valid_run(mock_method, runner):
        mock_method.return_value = 0
        results = runner.invoke(
            carbon, ['run', '-s', '../assets/descriptor.yml', '-d', '/tmp']
        )
        assert results.exit_code == 0

    @staticmethod
    @mock.patch.object(Carbon, 'run')
    def test_valid_run_set_task(mock_method, runner):
        mock_method.return_value = 0
        results = runner.invoke(
            carbon, ['run', '-t', 'validate', '-s', '../assets/descriptor.yml',
                     '-d', '/tmp']
        )
        assert results.exit_code == 0

    @staticmethod
    @mock.patch.object(yaml, 'safe_load')
    def test_invalid_run_malformed_input(mock_method, runner):
        mock_method.side_effect = yaml.YAMLError('error')
        results = runner.invoke(
            carbon, ['run', '-s', '../assets/descriptor.yml', '-d', '/tmp']
        )
        assert 'Error loading updated scenario data!' in results.output
