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
    carbon.resources.executes

    Module used for building carbon execute compounds. A execute's main goal
    is to run tests against the set of hosts for the scenario.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..core import CarbonResource, CarbonResourceError
from ..tasks import ExecuteTask, ValidateTask


class CarbonExecuteError(CarbonResourceError):
    """Execute's base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: details about the error
        :type message: str
        """
        super(CarbonExecuteError, self).__init__(message)


class Execute(CarbonResource):
    """
    The execute resource class.
    """

    _valid_tasks_types = ['validate', 'execute']
    _fields = [
        'name',
        'framework',
        'vars',
    ]

    def __init__(self,
                 config=None,
                 name=None,
                 parameters={},
                 execute_task_cls=ExecuteTask,
                 validate_task_cls=ValidateTask,
                 **kwargs):
        """Constructor.

        :param config: carbon configuration
        :type config: dict
        :param name: execute resource name
        :type name: str
        :param parameters: content which makes up the execute resource
        :type parameters: dict
        :param execute_task_cls: carbons execute task class
        :type execute_task_cls: object
        :param validate_task_cls: carbons validate task class
        :type validate_task_cls: object
        :param kwargs: additional key:value(s)
        :type kwargs: dict
        """
        super(Execute, self).__init__(config=config, name=name, **kwargs)

        # set the carbon task classes for the resource
        self._validate_task_cls = validate_task_cls
        self._execute_task_cls = execute_task_cls

        # reload construct task methods
        self.reload_tasks()

        # load the parameters into the object itself
        if parameters:
            self.load(parameters)

    def profile(self):
        """Build a profile for the execute resource.

        :return: the execute profile
        :rtype: dict
        """
        raise NotImplementedError

    def _construct_validate_task(self):
        """Constructs the validate task associated to the execute resource.

        :return: validate task definition
        :rtype: dict
        """
        task = {
            'task': self._validate_task_cls,
            'name': str(self.name),
            'resource': self,
            'methods': self._req_tasks_methods
        }
        return task

    def _construct_execute_task(self):
        """Constructs the execute task associated to the execute resource.

        :return: execute task definition
        :rtype: dict
        """
        task = {
            'task': self._execute_task_cls,
            'name': str(self.name),
            'package': self,
            'msg': '   executing %s' % self.name,
            'methods': self._req_tasks_methods
        }
        return task
