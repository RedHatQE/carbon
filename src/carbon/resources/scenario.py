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
    carbon.resources.scenario

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import errno

import os
import yaml
from pykwalify.core import Core
from pykwalify.errors import CoreError, SchemaError

from .actions import Action
from .executes import Execute
from .host import Host
from .reports import Report
from ..constants import SCENARIO_SCHEMA
from ..core import CarbonResource, CarbonResourceError
from ..helpers import gen_random_str
from ..tasks import ValidateTask


class ScenarioError(CarbonResourceError):
    """Scenario's base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        super(ScenarioError, self).__init__(message)


class Scenario(CarbonResource):

    _valid_tasks_types = ['validate']

    _fields = [
        'name',         # the name of the scenario
        'description',  # a brief description of what the scenario is
    ]

    def __init__(self,
                 config=None,
                 name=None,
                 parameters={},
                 validate_task_cls=ValidateTask,
                 **kwargs):

        super(Scenario, self).__init__(config=config, name=name, **kwargs)

        if not name:
            self._name = gen_random_str(15)

        self._credentials = list()

        self._hosts = list()
        self._actions = list()
        self._executes = list()
        self._reports = list()
        self._yaml_data = None
        self._validate_task_cls = validate_task_cls

        self.reload_tasks()

        if parameters:
            self.load(parameters)

        # create a scenario data folder where all hosts, actions, executes, reports
        # will live during the scenario life cycle
        # TODO: cleanup task should clean this directory after report collects it
        self._data_folder = self.config['DATA_FOLDER']
        try:
            if not os.path.exists(self._data_folder):
                os.makedirs(self._data_folder)
        except OSError as ex:
            if ex.errno == errno.EACCES:
                raise ScenarioError('You do not have permission to create'
                                    ' the workspace.')
            else:
                raise ScenarioError('Error creating scenario workspace: '
                                    '%s' % ex.message)

    def add_resource(self, item):
        """Add a scenario resource to its corresponding list.

        :param item: Resource.
        :type item: object
        """
        if isinstance(item, Host):
            self._hosts.append(item)
        elif isinstance(item, Action):
            self._actions.append(item)
        elif isinstance(item, Execute):
            self._executes.append(item)
        elif isinstance(item, Report):
            self._reports.append(item)
        else:
            raise ValueError('Resource must be of a valid Resource type.'
                             'Check the type of the given item: %s' % item)

    def initialize_resource(self, item):
        """Initialize resource list.

        The primary purpose for this method is to wipe out an entire resource
        list if the resource passed in is a match. This is needed after
        blaster run is finished to update the scenarios resources objects.
        The reason to update them is because blaster uses multiprocessing which
        spawns new processes which may alter a scenario resource object given
        to it. Carbon then has no corelation with that updated resource object.
        Which is why we need to refresh the scenario resources after run time.

        :param item: Resource.
        :type item: object
        """
        if isinstance(item, Host):
            self._hosts = list()
        elif isinstance(item, Action):
            self._actions = list()
        elif isinstance(item, Execute):
            self._executes = list()
        elif isinstance(item, Report):
            self._reports = list()
        else:
            raise ValueError('Resource must be of a valid Resource type.'
                             'Check the type of the given item: %s' % item)

    def reload_resources(self, tasks):
        """Reload scenario resources."""
        count = 0

        for task in tasks:
            for key, value in task.items():
                if isinstance(value, Host) and count <= 0:
                    self.initialize_resource(value)
                    self.add_resource(value)
                    count += 1
                elif isinstance(value, Host) and count >= 1:
                    self.add_resource(value)

    @property
    def data_folder(self):
        return self._data_folder

    @data_folder.setter
    def data_folder(self, value):
        raise ValueError('Data folder is set automatically.')

    @property
    def hosts(self):
        return self._hosts

    @hosts.setter
    def hosts(self, value):
        raise ValueError('You can not set hosts directly.'
                         'Use function ~Scenario.add_hosts')

    @property
    def yaml_data(self):
        return self._yaml_data

    @yaml_data.setter
    def yaml_data(self, value):
        self._yaml_data = value

    def add_hosts(self, h):
        if not isinstance(h, Host):
            raise ValueError('Host must be of type %s ' % type(Host))
        self._hosts.append(h)

    @property
    def actions(self):
        return self._actions

    @actions.setter
    def actions(self, value):
        raise ValueError('You can not set actions directly.'
                         'Use function ~Scenario.add_actions')

    def add_actions(self, h):
        if not isinstance(h, Action):
            raise ValueError('Action must be of type %s ' % type(Action))
        self._actions.append(h)

    @property
    def executes(self):
        return self._executes

    @executes.setter
    def executes(self, value):
        raise ValueError('You can not set executes directly.'
                         'Use function ~Scenario.add_executes')

    def add_executes(self, h):
        if not isinstance(h, Execute):
            raise ValueError('Execute must be of type %s ' % type(Execute))
        self._executes.append(h)

    @property
    def reports(self):
        return self._reports

    @reports.setter
    def reports(self, value):
        raise ValueError('You can not set reports directly.'
                         'Use function ~Scenario.add_reports')

    def add_reports(self, h):
        if not isinstance(h, Report):
            raise ValueError('Execute must be of type %s ' % type(Execute))
        self._reports.append(h)

    @property
    def credentials(self):
        return self._credentials

    @credentials.setter
    def credentials(self, value):
        raise ValueError('You cannot set credentials directly. '
                         'Use function ~Scenario.add_credentials')

    def add_credentials(self, data):
        if self._credentials:
            for index, value in enumerate(self._credentials):
                # overwrite if exists
                if value["name"] == data["name"]:
                    # self._credentials.remove(value)
                    self._credentials.pop(index)
            self._credentials.append(data)
        else:
            self._credentials.append(data)

    def yaml_validate(self):
        """Validate the carbon scenario yaml file."""
        self.logger.debug('Validating the scenario yaml data')

        try:
            c = Core(source_data=yaml.load(self._yaml_data),
                     schema_files=[SCENARIO_SCHEMA])
            c.validate(raise_exception=True)

            self.logger.debug(
                'Successfully validated scenario yaml based on schema.'
            )
        except (CoreError, SchemaError) as ex:
            self.logger.error(
                'Unsuccessfully validated scenario yaml based on schema.'
            )
            raise ScenarioError(ex.msg)

    def profile(self):
        """
        Builds a dictionary that represents the scenario with
        all its properties.
        :return: a dictionary representing the scenario
        """
        profile = dict(
            name=self.name,
            description=self.description,
            credentials=self.credentials,
            provision=[host.profile() for host in self.hosts],
            orchestrate=[],
            execute=[],
            report=[]
        )
        return profile

    def validate(self):
        # Perform scenario file validation based on carbon schema
        self.yaml_validate()

    def get_assets_list(self):
        """
        Get a list of all assets needed by all hosts in the scenario
        :return: list of assets
        """
        assets = []
        for host in self.hosts:
            assets += host.get_assets_list()
        return assets

    def _construct_validate_task(self):
        task = {
            'task': self._validate_task_cls,
            'name': str(self.name),
            'resource': self,
            'methods': self._req_tasks_methods
        }

        return task
