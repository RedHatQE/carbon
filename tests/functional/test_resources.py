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
    Unit tests to test carbon resources.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from carbon import Carbon, Scenario, Host
from carbon.helpers import file_mgmt

scenario_description = file_mgmt('r', 'assets/scenario.yaml')


class TestScenario(object):
    """Unit tests to test carbon scenarios."""

    @staticmethod
    def test_new_scenario_from_yaml():
        scenario = Scenario(scenario_description)
        assert isinstance(scenario, Scenario)
        assert len(scenario.hosts) == 0

    @staticmethod
    def test_new_attribute():
        scenario = Scenario(scenario_description)
        scenario.newattribute = 'value'
        assert scenario.newattribute == str('value')


class TestHost(object):
    """Unit tests to test carbon host."""

    @staticmethod
    def test_new_host_from_yaml():
        # TODO: Revisit this test case
        # cp_scenario_description = dict(scenario_description)
        # host = Host(parameters=cp_scenario_description.pop('provision')[0])
        # assert isinstance(host, Host)
        pass

    @staticmethod
    def test_new_host_from_carbon_object():
        cbn = Carbon(__name__)
        cbn.load_from_yaml('assets/scenario.yaml')
        assert isinstance(cbn.scenario._hosts.pop(0), Host)
