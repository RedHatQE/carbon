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
from carbon.helpers import get_executor_plugin_class, get_executors_plugin_list, get_orchestrator_plugin_class


def type_str_list(value, rule_obj, path):
    """Verify a key's value is either a string or list."""
    if not isinstance(value, (str, list)):
        raise AssertionError(
            '%s must be either a string or list.' % path.split('/')[-1]
        )
    return True


def type_int_list(value, rule_obj, path):
    """Verfiy a key's value is either a int or list."""
    if not isinstance(value, (int, list)):
        raise AssertionError(
            '%s must be either a integer or list of integers.' % path.split('/')[-1]
        )
    if isinstance(value, list):
        for x in value:
            if not isinstance(x, int):
                raise AssertionError(
                    '%s must be either a integer or list of integers.' % path.split('/')[-1]
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
    executors = get_executors_plugin_list()
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

    types = getattr(get_executor_plugin_class(value['executor']), '_execute_types')

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


def valid_ansible_script_type(value, rule_obj, path):
    """ Verify if ansible_script type is either a boolean or a dictionary
        and extra_args are from the given list and name key is required
    """

    extra_args = ['name', 'creates', 'decrypt', 'executable', 'removes', 'warn', 'stdin', 'stdin_add_newline']
    if isinstance(value, bool):
        return True
    elif isinstance(value, dict):
        if True in [keys in extra_args and isinstance(values, str) for keys, values in value.items()] \
                and value['name']:
            return True
        else:
            return False
    else:
        return False


def valid_action_types(value, rule_obj, path):
    """ Verify if only one action type is set for a orchestrate task"""
    match = list()

    # first verify the orchestrator is valid
    valid_orchestrator(value['orchestrator'], rule_obj, path)

    types = getattr(get_orchestrator_plugin_class(value['orchestrator']), '_action_types')

    for item in types:
        if item in value.keys():
            match.append(item)

    if match.__len__() > 1:
        raise AssertionError(
            'Only one action type can be set for orchestrator ~ %s.\n'
            'Available types: %s\n'
            'Set types: %s' % (value['orchestrator'], types, match)
        )
    return True
