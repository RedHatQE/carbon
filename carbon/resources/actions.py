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

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import os

from .._compat import string_types
from ..constants import DEFAULT_ORCHESTRATOR
from ..core import CarbonResource, CarbonResourceError
from ..helpers import fetch_hosts, get_orchestrator_class, \
    get_orchestrators_list
from ..tasks import OrchestrateTask, ValidateTask


class CarbonActionError(CarbonResourceError):
    """Action's base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        self.message = message
        super(CarbonActionError, self).__init__(message)


class Action(CarbonResource):

    _valid_tasks_types = ['validate', 'orchestrate']
    _fields = [
        'name',
        'hosts',
        'vars',
    ]

    def __init__(self,
                 config=None,
                 name=None,
                 parameters={},
                 validate_task_cls=ValidateTask,
                 orchestrate_task_cls=OrchestrateTask,
                 **kwargs):

        super(Action, self).__init__(config=config, name=name, **kwargs)

        # Every action is REQUIRED to have a name. The name for each action
        # is the actual action to be executed. i.e. an ansible action's name
        # is the name of the module or playbook to be executed. This cannot
        # be null, user needs to set this.
        if name is None:
            self._name = parameters.pop('name', None)
            if self._name is None:
                raise CarbonActionError('All actions require a name!')
        else:
            self._name = name

        # Every action object will have 'x' number of hosts associated with
        # it. Every action is also going to have an orchestrator associated
        # to it. Each orchestrator will require different configuration for
        # connecting to the remote host(s). Once defined the orchestrator can
        # execute the given action against the remote host(s). Most
        # orchestrator's are going to require an IP address and authentication
        # details (SSH) to connect to host(s).

        # Lets associate the list of hosts for the action to the action
        # object itself. Don't worry these hosts are currently strings. When
        # carbon goes to build the pipeline it does a lookup and gets the
        # actual host object from the scenario including all the required
        # information. i.e. IP address, SSH keys, etc..
        self.hosts = parameters.pop('hosts')
        if self.hosts is None:
            raise CarbonActionError('An action must have hosts associated '
                                    'to it.')

        # Hosts can be in the form of either string or list defined by the
        # user. lets convert the hosts into a list if in string format
        if isinstance(self.hosts, string_types):
            self.hosts = self.hosts.replace(' ', '').split(',')

        # We must have an orchestrator set for each action, default=ansible
        orchestrator_param = parameters.pop(
            'orchestrator',
            DEFAULT_ORCHESTRATOR
        )
        if orchestrator_param not in get_orchestrators_list():
            raise CarbonActionError('Invalid orchestrator: %s for action %s.'
                                    % (orchestrator_param, str(self.name)))

        # We need to get the orchestrator class
        self._orchestrator_cls = get_orchestrator_class(orchestrator_param)

        # Lets update the parameters to include a vars key if none exists.
        # It is possible that some actions may not require variables.
        if 'vars' not in parameters:
            parameters['vars'] = dict()

        self._validate_task_cls = validate_task_cls
        self._orchestrate_task_cls = orchestrate_task_cls

        self.reload_tasks()

        if parameters:
            self.load(parameters)

    @property
    def orchestrator_cls(self):
        return self._orchestrator_cls

    @orchestrator_cls.setter
    def orchestrator_cls(self, value):
        raise AttributeError('Orchestrator class property cannot be set.')

    def profile(self):
        """Builds a profile for the action.

        :return: the action profile
        """
        profile = dict(
            name=self.name,
            orchestrator=self.orchestrator_cls.__orchestrator_name__,
            vars=getattr(self, 'vars')
        )

        # build the hosts key
        if all(isinstance(item, string_types) for item in self.hosts):
            profile.update(hosts=[host for host in self.hosts])
        else:
            profile.update(dict(hosts=[host.name for host in self.hosts]))

        return profile

    def get_assets_list(self, hosts):
        """Get the assets for the action.

        Every action has an associated orchestrator. Each orchestrator will
        have a directory with the name of the orchestrator where all its
        files will be stored. These files will be copied to carbon's data
        folder at run time which then the orchestrator will read from that
        location.

        This method will build the assets for the action
        This method will build the assets for the action including the
        following:
            - orchestrator files directory
            - any orchestrator parameter assets defined in each host
                - i.e.
                    - hosts:
                        ansible_params:
                            ansible_ssh_private_key: private_key

        :param hosts: list of host objects associated to the action
            reference: carbon.resources.scenario.get_assets_list()
        :return: list of the actions assets
        """
        # initialize empty assets list
        assets = list()

        # append the orchestrator files directory
        path = os.path.join(
            self.config['ASSETS_PATH'],
            self.orchestrator_cls.__orchestrator_name__
        )

        if os.path.exists(path):
            assets.append(self.orchestrator_cls.__orchestrator_name__)

        # append host orchestrator parameters for the action
        hosts = fetch_hosts(hosts, dict(package=self), all_hosts=True)
        for host in hosts['package'].hosts:
            field = '%s_params' % self.orchestrator_cls.__orchestrator_name__
            if not hasattr(host, field):
                continue
            for asset in getattr(self.orchestrator_cls, '_assets_parameters'):
                params = getattr(host, field)
                if asset in params and params[asset]:
                    assets.append(getattr(host, field)[asset])
        return assets

    def _construct_validate_task(self):
        task = {
            'task': self._validate_task_cls,
            'name': str(self.name),
            'resource': self,
            'methods': self._req_tasks_methods
        }
        return task

    def _construct_orchestrate_task(self):
        """
        Used to create the create attribute by the Host constructor.
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
