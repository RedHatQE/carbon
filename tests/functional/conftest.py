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
    tests.conftest

    Module containing hooks used by all tests.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from fixtures import action_resource, action_resource_cleanup, scenario, \
    report_resource, execute_resource, host, default_host_params, \
    scenario_resource, config, master_child_scenario, scenario1, asset1, asset3, action1,\
    scenario_resource1, execute1, execute2, asset2

__all__ = [
    action_resource,
    action_resource_cleanup,
    config,
    default_host_params,
    execute_resource,
    execute1,
    execute2,
    host,
    asset1,
    asset2,
    asset3,
    action1,
    report_resource,
    scenario,
    scenario1,
    scenario_resource,
    scenario_resource1,
    master_child_scenario
]
