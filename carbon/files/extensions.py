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
    Pykwalify extensions module.

    Module containing custom validation functions used for schema checking.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from carbon.constants import ORCHESTRATOR
from carbon.helpers import get_executor_class, get_executors_list


def type_str_list(value, rule_obj, path):
    """Verify a key's value is either a string or list."""
    if not isinstance(value, (str, list)):
        raise AssertionError(
            '%s must be either a string or list.' % path.split('/')[-1]
        )
    return True


def valid_orchestrator(value, rule_obj, path):
    """Verify the given orchestrator is a valid selection by carbon."""
    if value.lower() != ORCHESTRATOR:
        raise AssertionError(
            'Orchestrator %s is invalid.\n'
            'Available orchestrators %s' % (value, ORCHESTRATOR)
        )
    return True


def valid_executor(value, rule_obj, path):
    """Verify the given executor is a valid selection by carbon."""
    executors = get_executors_list()
    if value.lower() not in executors:
        raise AssertionError(
            'Executor %s is invalid.\n'
            'Available executors %s' % (value, executors)
        )
    return True


def valid_execute_types(value, rule_obj, path):
    """Verify the execute type defined is valid for the supplied executor."""
    match = list()
    executor = value['executor']

    # first verify the executor is valid
    valid_executor(executor, rule_obj, path)

    types = getattr(get_executor_class(value['executor']), '_execute_types')

    for item in types:
        if item in value.keys():
            match.append(item)

    if match.__len__() > 1:
        raise AssertionError(
            'Only one execute type can be set for executor ~ %s.\n'
            'Available types: %s\n'
            'Set types: %s' % (executor, types, match)
        )
    return True
