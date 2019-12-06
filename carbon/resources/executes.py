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

from .._compat import string_types
from ..core import CarbonResource
from ..constants import EXECUTOR
from ..helpers import get_executor_plugin_class, \
    get_executors_plugin_list
from ..tasks import ExecuteTask, ValidateTask
from ..exceptions import CarbonExecuteError
from collections import OrderedDict


class Execute(CarbonResource):
    """
    The execute resource class.
    """

    _valid_tasks_types = ['validate', 'execute']

    # The fields (ansible_options, git, shell, and script) could have been
    # optional parameters for the runner executor; however, since this is
    # planned to be the main executor, it made sense to define them here
    # and not appending runner to those keys.  This can be changed if
    # there are more executors added.
    _fields = [
        'name',
        'description',
        'hosts',
        'artifacts',
        'ansible_options',
        'git',
        'ignore_rc',
        'valid_rc',
        'artifacts_location'
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

        # set the execute resource name
        if name is None:
            self._name = parameters.pop('name', None)
            if self._name is None:
                raise CarbonExecuteError('Unable to build execute object. Name'
                                         ' field missing!')
        else:
            self._name = name

        # set the execute description
        self._description = parameters.pop('description', None)

        # every execute has a mandatory executor, lets set it
        executor = parameters.pop('executor', EXECUTOR)

        if executor not in get_executors_plugin_list():
            raise CarbonExecuteError('Executor: %s is not supported!' %
                                     executor)

        # get the executor class
        self._executor = get_executor_plugin_class(executor)

        self.hosts = parameters.pop('hosts')
        if self.hosts is None:
            raise CarbonExecuteError('Unable to associate hosts to executor:'
                                     '%s. No hosts defined!' % self._name)

        # convert the hosts into list format if hosts defined as str format
        if isinstance(self.hosts, string_types):
            self.hosts = self.hosts.replace(' ', '').split(',')

        self.artifacts = parameters.pop('artifacts', None)
        if self.artifacts:
            if isinstance(self.artifacts, string_types):
                self.artifacts = self.artifacts.replace(' ', '').split(',')

        self.artifact_locations = parameters.pop('artifact_locations', None)

        # create the executor attributes in the execute object
        for p in getattr(self.executor, 'get_all_parameters')():
            setattr(self, p, parameters.get(p, {}))

        # set the carbon task classes for the resource
        self._validate_task_cls = validate_task_cls
        self._execute_task_cls = execute_task_cls

        # update fields attr with executor types
        for item in getattr(self.executor, '_execute_types'):
            self._fields.append(item)

        # reload construct task methods
        self.reload_tasks()

        # load the parameters into the object itself
        if parameters:
            self.load(parameters)

    @property
    def executor(self):
        """Executor property.

        :return: executor class object
        :rtype: object
        """
        return self._executor

    @executor.setter
    def executor(self, value):
        """Set executor property."""
        raise AttributeError('Executor class property cannot be set.')

    def profile(self):
        """Build a profile for the execute resource.

        :return: the execute profile
        :rtype: OrderedDict
        """
        profile = OrderedDict()
        profile.update({'name': self.name})
        profile.update({'description': self.description})
        profile.update({'executor': getattr(self.executor, '__executor_name__')})

        for item in getattr(self, '_fields'):
            if getattr(self, item, None):
                profile.update({item: getattr(self, item)})

        # set the execute's hosts
        if all(isinstance(item, string_types) for item in self.hosts):
            profile.update(hosts=[host for host in self.hosts])
        else:
            profile.update(dict(hosts=[host.name for host in self.hosts]))

        # update the profile with executor properties
        profile.update(getattr(self.executor, 'build_profile')(self))

        if self.artifact_locations:
            profile.update({'artifact_locations': self.artifact_locations})

        return profile

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
