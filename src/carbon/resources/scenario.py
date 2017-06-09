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
import os
import sys
import errno

from pykwalify.core import Core
from ..constants import SCENARIO_SCHEMA
from ..core import CarbonResource, CarbonException
from ..helpers import gen_random_str
from ..tasks import ValidateTask
from .actions import Action
from .host import Host
from .executes import Execute
from .reports import Report


class Scenario(CarbonResource):

    _valid_tasks_types = ['validate']

    _fields = [
        'name',         # the name of the scenario
        'description',  # a brief description of what the scenario is
        'filename',  # location of the file that is the scenario
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
                raise CarbonException('You do not have permission to create'
                                      ' the workspace.')
            else:
                raise CarbonException('Error creating scenario workspace: '
                                      '%s' % ex.message)

    def add_resource(self, item):
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
        self._credentials.append(data)

    @staticmethod
    def yaml_validate(yaml_file):
        """
        Validating the scenario yaml
        """
        c = Core(source_file=yaml_file, schema_files=[SCENARIO_SCHEMA])

        try:
            c.validate(raise_exception=True)
        except:
            e = sys.exc_info()[1]
            return 1, e
        return 0, "Successful validation of the yaml file"

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
        self.logger.info("Validate the file %s", self.filename)
        val = self.yaml_validate(self.filename)
        if val[0]:
            self.logger.error("error occurred during file validation: %s",
                              val[1])
            raise CarbonException('Error occurred during file schema validation')
        else:
            self.logger.info("Successful validation of the yaml according to "
                             "our schema")

    def _construct_validate_task(self):
        task = {
            'task': self._validate_task_cls,
            'resource': self,
        }

        return task
