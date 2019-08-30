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
from collections import OrderedDict
from pykwalify.core import Core
from pykwalify.errors import CoreError, SchemaError

from .actions import Action
from .executes import Execute
from .assets import Asset
from .reports import Report
from ..constants import SCENARIO_SCHEMA, SCHEMA_EXT, \
    SET_CREDENTIALS_OPTIONS
from ..core import CarbonResource
from ..exceptions import ScenarioError
from ..helpers import gen_random_str, resource_check
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
        'resource_check',    # external dependency check resources
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
        else:
            self._name = name

        # set the scenario description attribute
        self._description = parameters.pop('description', None)

        # External Dependency Component list of Scenario
        self.resource_check = []

        # set resource attributes
        self._assets = list()
        self._actions = list()
        self._executes = list()
        self._reports = list()
        self._yaml_data = dict()
        # Properties to take care of included scenarios
        self._child_scenarios = list()
        self._included_scenario_names = list()

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

    def get_all_assets(self):
        if self.child_scenarios:
            all_assets = list()
            for sc in self.child_scenarios:
                all_assets.extend([item for item in getattr(sc, 'assets')])
            all_assets.extend([item for item in getattr(self, 'assets')])
            return all_assets
        return getattr(self, 'assets')

    def get_all_actions(self):
        if self.child_scenarios:
            all_actions = list()
            for sc in self.child_scenarios:
                all_actions.extend([item for item in getattr(sc, 'actions')])
            all_actions.extend([item for item in getattr(self, 'actions')])
            return all_actions
        return getattr(self, 'actions')

    def get_all_executes(self):
        if self.child_scenarios:
            all_executes = list()
            for sc in self.child_scenarios:
                all_executes.extend([item for item in getattr(sc, 'executes')])
            all_executes.extend([item for item in getattr(self, 'executes')])
            return all_executes
        return getattr(self, 'executes')

    def get_all_reports(self):
        if self.child_scenarios:
            all_reports = list()
            for sc in self.child_scenarios:
                all_reports.extend([item for item in getattr(sc, 'reports')])
            all_reports.extend([item for item in getattr(self, 'reports')])
            return all_reports
        return getattr(self, 'reports')

    def add_resource(self, item):
        """Add a scenario resource to its corresponding list.

        :param item: resource data
        :type item: object
        """
        if isinstance(item, Asset):
            self._assets.append(item)
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
        if isinstance(item, Asset):
            self._assets = list()
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
        This method is used to reload host and report resources after they have been provisioned or imported.
        Prior to adding the host/report resource to the scenario, it filters the list by checking if the resource
        belongs to that scenario by comparing the names.

        Then it filters the task list even more extracting the resource and the data in rvalue.
        If rvalue is present then linchpin count feature was used and that more new host resources will be
        created. If rvalue is not present then assume it is either a report resource or from a provisioning perspective
        linchpin count was either not used (which is equivalent of count==1), or using old provisioners.

        :param tasks: task data returned by blaster
        :type tasks: list
        """
        count = 0
        filtered_task_list = list()
        filtered_task_list.extend(
            [task for task in tasks if task.get('asset') and getattr(task.get('asset'), 'name')
             in [h.name for h in self.assets]]
        )
        filtered_task_list.extend(
            [task for task in tasks if isinstance(task.get('package'), Report) and getattr(task.get('package'), 'name')
             in [r.name for r in self.reports]]
        )

        for res, rvalue in [(res, item['rvalue']) for task in filtered_task_list
                            for res in [task.get(r) for r in ['asset', 'package'] if r in task.keys()]
                            for item in task.get('methods')]:
            if count == 0:
                if rvalue is not None:
                    # initialize the host resource list to remove any previous host resources
                    self.initialize_resource(res)
                    # load the new host resources using the parameters from item['rvalue']
                    self.load_resources(Asset, rvalue)
                    count += 1
                else:
                    self.initialize_resource(res)
                    self.add_resource(res)
                    count += 1
            else:
                if rvalue is not None:
                    self.load_resources(Asset, rvalue)
                else:
                    self.add_resource(res)

        return

    @property
    def name(self):
        """Scenario object name
        :return: scenario name
        :rtype: basestring
        """
        return self._name

    @name.setter
    def name(self, value):
        raise ValueError("you cannot set name of the scenario")

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
    def assets(self):
        """Hosts property

        :return: host resources associated to the scenario
        :rtype: list
        """
        return self._assets

    @assets.setter
    def assets(self, value):
        """Set hosts property."""
        raise ValueError('You can not set assets directly.'
                         'Use function ~Scenario.add_assets')

    def add_assets(self, host):
        """Add host resources to the scenario.

        :param host: host resource
        :type host: object
        """
        if not isinstance(host, Asset):
            raise ValueError('Asset must be of type %s ' % type(Asset))
        self._assets.append(host)

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

    @property
    def child_scenarios(self):
        """
        List of child scenarios for the master scenario
        :rtype: List
        """
        return self._child_scenarios

    @child_scenarios.setter
    def child_scenarios(self, value):
        """Set child_scenarios property."""
        raise ValueError('You can not set child_scenarios directly.'
                         'Use function ~Scenario.add_child_scenario')

    def add_child_scenario(self, scenario):
        """Add child/included scenarios to the master scenario resource.
        :param scenario: scenario resource
        :type scenario: object
        """
        if not isinstance(scenario, Scenario):
            raise ValueError('scenario must be of type %s ' % type(Scenario))
        self._child_scenarios.append(scenario)

    @property
    def included_scenario_names(self):
        """
        List of files which are put in the include section of the scenario
        :return: list of files
        :rtype: list
        """
        return self._included_scenario_names

    @included_scenario_names.setter
    def included_scenario_names(self, inc_name_list):
        """Add included file names as list
        :param inc_name_list: list of names
        :type inc_name_list: list
        """
        if inc_name_list:
            for item in inc_name_list:
                self.included_scenario_names.append(item)
        else:
            raise ValueError("Included scenario list cannot be empty")

    def add_reports(self, report):
        """Add report resources to the scenario.

        :param report: report resource
        :type report: object
        """
        if not isinstance(report, Report):
            raise ValueError('Execute must be of type %s ' % type(Execute))
        self._reports.append(report)

    def validate(self):
        """Validate the scenario based on the default schema."""
        self.logger.debug('Validating scenario YAML file')

        msg = 'validated scenario YAML file against the schema!'

        try:
            c = Core(source_data=yaml.safe_load(self.yaml_data),
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
        if self.config['RESOURCE_CHECK_ENDPOINT'] and self.resource_check:
            # Check Status of components (UP/DOWN)
            resource_check(self, self.config)

    def profile(self):
        """Builds a profile which represents the scenario and its properties.

        :return: a dictionary representing the scenario
        :rtype: OrderedDict
        """
        profile = OrderedDict()
        profile['name'] = self.name
        profile['description'] = self.description
        if self.child_scenarios:
            profile['include'] = self.included_scenario_names
        profile['resource_check'] = self.resource_check
        profile['provision'] = [asset.profile() for asset in self.assets]
        profile['orchestrate'] = [action.profile() for action in self.actions]
        profile['execute'] = [execute.profile() for execute in self.executes]
        profile['report'] = [report.profile() for report in self.reports]

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

    def load_resources(self, res_type, res_list):
        """
        Load the resource in the scenario list of `res_type`.

        The scenario holds a list of each resource type: hosts, actions,
        reports, etc. This function takes what type of resource is in
        list it calls ~self.scenario.add_resource for each item in the
        list of the given resources.

        For example, if we call load_resources(Asset, hosts_list), the
        function will go through each item in the list, create the
        resource with Asset(parameter=item) and load it within the list
        ~self.hosts.

        :param res_type: The type of resources the function will load into its
            list
        :param res_list: A list of resources dict
        :return: None
        """
        # No resources defined, then exit
        if not res_list:
            return

        for item in res_list:
            self.add_resource(
                res_type(config=self.config,
                         parameters=item))
