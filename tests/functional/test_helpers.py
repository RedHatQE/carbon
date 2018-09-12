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

from carbon.exceptions import CarbonError
from carbon.helpers import DataInjector


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
