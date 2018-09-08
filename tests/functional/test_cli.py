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

import pytest
from click.testing import CliRunner

from carbon.cli import print_header, carbon


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
    def test_carbon_validate_invalid_scenario(runner):
        results = runner.invoke(carbon, ['validate', '-s', 'cdf.yml'])
        assert 'You have to provide a valid scenario file.' in results.output
