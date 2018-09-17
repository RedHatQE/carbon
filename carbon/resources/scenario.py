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

    Module used for building carbon scenario compound. Every carbon object
    has one scenario which has additional compounds associated to it.

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
from ..constants import SCENARIO_SCHEMA, DEP_CHECK_LIST, SCHEMA_EXT
from ..core import CarbonResource
from ..exceptions import ScenarioError
from ..helpers import gen_random_str, dep_check
from ..tasks import ValidateTask


class Scenario(CarbonResource):
    """
    The scenario resource class. It is the core resource which makes up the
    carbon compound. A scenario consists of multiple compounds of 'resources'.
    Those compounds make up the scenario which derive tasks for the scenario
    to be processed.
    """

    _valid_tasks_types = ['validate']

    _fields = [
        'name',         # the name of the scenario
        'description',  # a brief description of what the scenario is,
        'dep_check',    # external dependency check resources
    ]

    def __init__(self,
                 config=None,
                 name=None,
                 parameters={},
                 validate_task_cls=ValidateTask,
                 **kwargs):
        """Constructor.

        :param config: carbon configuration
        :type config: dict
        :param name: scenario name
        :type name: str
        :param parameters: content which makes up the scenario
        :type parameters: dict
        :param validate_task_cls: carbons validate task class
        :type validate_task_cls: object
        :param kwargs: additional key:value(s)
        :type kwargs: dict
        """
        super(Scenario, self).__init__(config=config, name=name, **kwargs)

        # set the scenario name attribute
        if not name:
            self._name = gen_random_str(15)

        # set the scenario description attribute
        self._description = parameters.pop('description', None)

        # External Dependency Component list of Scenario
        self.dep_check = ""

        self._credentials = list()

        # set resource attributes
        self._hosts = list()
        self._actions = list()
        self._executes = list()
        self._reports = list()
        self._yaml_data = dict()

        # set the carbon task classes for the scenario
        self._validate_task_cls = validate_task_cls

        # create the runtime data folder for the scenario life cycle
        # TODO: cleanup task should remove this directory after report task
        try:
            if not os.path.exists(self.data_folder):
                os.makedirs(self.data_folder)
        except OSError as ex:
            if ex.errno == errno.EACCES:
                raise ScenarioError('You do not have permission to create'
                                    ' the workspace.')
            else:
                raise ScenarioError('Error creating scenario workspace: '
                                    '%s' % ex)

        # reload construct task methods
        self.reload_tasks()

        # load the parameters set into the object itself
        if parameters:
            self.load(parameters)

    def add_resource(self, item):
        """Add a scenario resource to its corresponding list.

        :param item: resource data
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
        to it. Carbon then has no correlation with that updated resource.
        Which is why we need to refresh the scenario resources after run time.

        :param item: resource data
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
        """Reload scenario resources.

        :param tasks: task data returned by blaster
        :type tasks: list
        """
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
    def yaml_data(self):
        """Scenario file content property.

        :return: scenario file content
        :rtype: list
        """
        return self._yaml_data

    @yaml_data.setter
    def yaml_data(self, value):
        """Set scenario file content property."""
        self._yaml_data = value

    @property
    def hosts(self):
        """Hosts property

        :return: host resources associated to the scenario
        :rtype: list
        """
        return self._hosts

    @hosts.setter
    def hosts(self, value):
        """Set hosts property."""
        raise ValueError('You can not set hosts directly.'
                         'Use function ~Scenario.add_hosts')

    def add_hosts(self, host):
        """Add host resources to the scenario.

        :param host: host resource
        :type host: object
        """
        if not isinstance(host, Host):
            raise ValueError('Host must be of type %s ' % type(Host))
        self._hosts.append(host)

    @property
    def actions(self):
        """Actions property.

        :return: action resources associated to the scenario
        :rtype: list
        """
        return self._actions

    @actions.setter
    def actions(self, value):
        """Set actions property."""
        raise ValueError('You can not set actions directly.'
                         'Use function ~Scenario.add_actions')

    def add_actions(self, action):
        """Add action resources to the scenario.

        :param action: action resource
        :type action: object
        """
        if not isinstance(action, Action):
            raise ValueError('Action must be of type %s ' % type(Action))
        self._actions.append(action)

    @property
    def executes(self):
        """Executes property.

        :return: execute resources associated to the scenario
        :rtype: list
        """
        return self._executes

    @executes.setter
    def executes(self, value):
        """Set executes property."""
        raise ValueError('You can not set executes directly.'
                         'Use function ~Scenario.add_executes')

    def add_executes(self, execute):
        """Add execute resources to the scenario.

        :param execute: execute resource
        :type execute: object
        """
        if not isinstance(execute, Execute):
            raise ValueError('Execute must be of type %s ' % type(Execute))
        self._executes.append(execute)

    @property
    def reports(self):
        """Reports property.

        :return: report resources associated to the scenario
        :rtype: list
        """
        return self._reports

    @reports.setter
    def reports(self, value):
        """Set report property."""
        raise ValueError('You can not set reports directly.'
                         'Use function ~Scenario.add_reports')

    def add_reports(self, report):
        """Add report resources to the scenario.

        :param report: report resource
        :type report: object
        """
        if not isinstance(report, Report):
            raise ValueError('Execute must be of type %s ' % type(Execute))
        self._reports.append(report)

    @property
    def credentials(self):
        """Credentials property.

        :return: credentials associated to the scenario.
        :rtype: list
        """
        return self._credentials

    @credentials.setter
    def credentials(self, value):
        """Set credentials property."""
        raise ValueError('You cannot set credentials directly. '
                         'Use function ~Scenario.add_credentials')

    def add_credentials(self, data):
        """Add credentials to the scenario.

        :param data: credentials data
        :type data: dict
        """
        if self._credentials:
            for index, value in enumerate(self._credentials):
                # overwrite if exists
                if value["name"] == data["name"]:
                    self._credentials.pop(index)
            self._credentials.append(data)
        else:
            self._credentials.append(data)

    def validate(self):
        """Validate the scenario based on the default schema."""
        self.logger.debug('Validating scenario YAML file')

        msg = 'validated scenario YAML file against the schema!'

        try:
            c = Core(source_data=yaml.load(self.yaml_data),
                     schema_files=[SCENARIO_SCHEMA],
                     extensions=[SCHEMA_EXT])
            c.validate(raise_exception=True)

            self.logger.debug('Successfully %s' % msg)
        except (CoreError, SchemaError) as ex:
            self.logger.error('Unsuccessfully %s' % msg)
            raise ScenarioError(ex.msg)

        # Verify dependency check components are supported/valid then
        # Check status (UP/DOWN)
        # Only check if dependancy check endpoint set and components given
        # Else it is ignored
        if self.config['DEP_CHECK_ENDPOINT'] and self.dep_check:
            self.dep_check, dep_check_val = [x.lower().split(':', 1)[-1] for x in self.dep_check], \
                                            [x.lower().split(':', 1)[0] for x in self.dep_check]

            if all(x in DEP_CHECK_LIST for x in dep_check_val) is not True:
                self.logger.error('Invalid Dependency Check Component specified in descriptor of scenario '
                                    "'%s' Valid: %s - Supplied: %s." %
                                  (str(self.name), DEP_CHECK_LIST, dep_check_val))
                raise ScenarioError('Invalid Dependency Check Component specified in descriptor of scenario '
                                    "'%s' Valid: %s - Supplied: %s." %
                                    (str(self.name), DEP_CHECK_LIST, dep_check_val))

            # Check Status of components (UP/DOWN)
            dep_check(self, self.config)

    def profile(self):
        """Builds a profile which represents the scenario and its properties.

        :return: a dictionary representing the scenario
        :rtype: dict
        """
        profile = dict(
            name=self.name,
            description=self.description,
            dep_check=self.dep_check,
            credentials=self.credentials,
            provision=[host.profile() for host in self.hosts],
            orchestrate=[action.profile() for action in self.actions],
            execute=[execute.profile() for execute in self.executes],
            report=[report.profile() for report in self.reports]
        )
        return profile

    def _construct_validate_task(self):
        """Constructs the validate task associated to the scenario.

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
