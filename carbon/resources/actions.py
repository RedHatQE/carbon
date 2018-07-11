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
    carbon.resources.actions

    Module used for building carbon action compounds. An action's main goal
    is to perform some sort of work.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import os

from .._compat import string_types
from ..constants import ORCHESTRATOR
from ..core import CarbonResource, CarbonResourceError
from ..helpers import fetch_hosts, get_orchestrator_class, \
    get_orchestrators_list
from ..tasks import OrchestrateTask, ValidateTask


class CarbonActionError(CarbonResourceError):
    """Action's base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        :type message: str
        """
        self.message = message
        super(CarbonActionError, self).__init__(message)


class Action(CarbonResource):
    """
    The action resource class. The carbon compound can contain x amount of
    actions. Their primary responsibility is to do some sort of work. Actions
    can handle any sort of task to be processed. Most of the time you will
    see actions consisting of the following:
        - System configuration
        - Product installation/configuration
        - Test setup (test framework installation/configuration)

    Each action has an associated orchestrator. The orchestrator is what
    processes (completes) the given action.
    """

    _valid_tasks_types = ['validate', 'orchestrate']
    _fields = ['name', 'hosts']

    def __init__(self,
                 config=None,
                 name=None,
                 parameters=dict,
                 validate_task_cls=ValidateTask,
                 orchestrate_task_cls=OrchestrateTask,
                 **kwargs):
        """Constructor.

        The primary focus of the constructor is to build the action object
        containing all necessary parts to process the action.

        :param config: carbon configuration
        :type config: dict
        :param name: action resource name
        :type name: str
        :param parameters: content which makes up the action resource
        :type parameters: dict
        :param validate_task_cls: carbons validate task class
        :type validate_task_cls: object
        :param orchestrate_task_cls: carbons orchestrate task class
        :type orchestrate_task_cls: object
        :param kwargs: additional key:value(s)
        :type kwargs: dict
        """
        super(Action, self).__init__(config=config, name=name, **kwargs)

        # set the action resource name
        if name is None:
            self._name = parameters.pop('name', None)
            if self._name is None:
                raise CarbonActionError('Unable to build action object. Name'
                                        ' field missing!')
        else:
            self._name = name

        # each action will have x number of hosts associated to it. lets
        # associate the list of hosts to the action object itself. currently
        # the hosts are strings, when carbon builds the pipeline, they will
        # be updated with their corresponding host object.
        self.hosts = parameters.pop('hosts')
        if self.hosts is None:
            raise CarbonActionError('Unable to associate hosts to action: %s.'
                                    'No hosts defined!' % self._name)

        # convert the hosts into list format if hosts defined as str format
        if isinstance(self.hosts, string_types):
            self.hosts = self.hosts.replace(' ', '').split(',')

        # every action has a mandatory orchestrator, lets set it
        orchestrator = parameters.pop('orchestrator', ORCHESTRATOR)
        if orchestrator not in get_orchestrators_list():
            raise CarbonActionError('Orchestrator: %s is not supported!' %
                                    orchestrator)

        # now that we know the orchestrator, lets get the class
        self._orchestrator = get_orchestrator_class(orchestrator)

        # create the orchestrator attributes in the action object
        for p in getattr(self.orchestrator, 'get_all_parameters')():
            setattr(self, p, parameters.get(p, None))

        # set the carbon task classes for the resource
        self._validate_task_cls = validate_task_cls
        self._orchestrate_task_cls = orchestrate_task_cls

        # reload construct task methods
        self.reload_tasks()

        # load the parameters set into the object itself
        if parameters:
            self.load(parameters)

    @property
    def orchestrator(self):
        """Orchestrator property.

        :return: orchestrator class object
        :rtype: object
        """
        return self._orchestrator

    @orchestrator.setter
    def orchestrator(self, value):
        """Set orchestrator property."""
        raise AttributeError('Orchestrator class property cannot be set.')

    def profile(self):
        """Builds a profile for the action resource.

        :return: the action profile
        :rtype: dict
        """
        # initialize the profile with orchestrator properties
        profile = getattr(self.orchestrator, 'build_profile')(self)

        # set additional action properties
        profile.update({
            'name': self.name,
            'orchestrator': getattr(self.orchestrator, '__orchestrator_name__')
        })

        # set the action's hosts
        if all(isinstance(item, string_types) for item in self.hosts):
            profile.update(hosts=[host for host in self.hosts])
        else:
            profile.update(dict(hosts=[host.name for host in self.hosts]))

        return profile

    def get_assets_list(self, hosts):
        """Return all assets for the action resource.

        Action assets may consist of the following:
            - orchestrator files (directory)
            - orchestrator parameters assets defined in each host

        :param hosts: list of host objects associated to the action
            reference: carbon.resources.scenario.get_assets_list()
        :return: action assets
        :rtype: list
        """
        orchestrator = getattr(self.orchestrator, '__orchestrator_name__')

        # initialize empty assets list
        assets = list()

        # append the orchestrator files directory
        path = os.path.join(
            self.config['ASSETS_PATH'],
            getattr(self.orchestrator, '__orchestrator_name__')
        )

        if os.path.exists(path):
            assets.append(orchestrator)

        # append host orchestrator parameters for the action
        hosts = fetch_hosts(hosts, dict(package=self), all_hosts=True)
        for host in hosts['package'].hosts:
            field = '%s_params' % orchestrator
            if not hasattr(host, field):
                continue
            for asset in getattr(self.orchestrator, '_assets_parameters'):
                params = getattr(host, field)
                if asset in params and params[asset]:
                    assets.append(getattr(host, field)[asset])

        # append role_file (if set)
        galaxy_options = getattr(self, '%s_galaxy_options' % orchestrator)
        if galaxy_options is not None:
            for element in galaxy_options:
                if 'role_file' in element:
                    assets.append(galaxy_options[element])

        return assets

    def _construct_validate_task(self):
        """Constructs the validate task associated to the action resource.

        :returns: validate task definition
        :rtype: dict
        """
        task = {
            'task': self._validate_task_cls,
            'name': str(self.name),
            'resource': self,
            'methods': self._req_tasks_methods
        }
        return task

    def _construct_orchestrate_task(self):
        """Constructs the orchestrate task associated to the action.

        :return: orchestrate task definition
        :rtype: dict
        """
        task = {
            'task': self._orchestrate_task_cls,
            'name': str(self.name),
            'package': self,
            'msg': '   running orchestration %s for %s' % (
                self.name, self.hosts),
            'methods': self._req_tasks_methods
        }
        return task
