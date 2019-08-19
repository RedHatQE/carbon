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
    carbon.utils.pipeline

    Module containing classes and functions for building pipelines of resources
    and tasks for carbon to run.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from collections import namedtuple

from ..constants import TASKLIST
from ..exceptions import CarbonError
from ..helpers import fetch_hosts, get_core_tasks_classes, fetch_executes, get_actions_failed_status, \
    set_task_class_concurrency
from ..tasks import CleanupTask


class PipelineBuilder(object):
    """
    The primary class for building carbons pipelines to execute. A pipeline
    will exists for each carbon task. Within each pipeline consists of all
    resources for that specific task to process.
    """

    def __init__(self, name):
        """Constructor.

        :param name: carbon task name
        :type name: str
        """
        self._name = name

        # pipelines are a tuple data structure consisting of a name, type and
        # list of tasks
        self.pipeline_template = namedtuple(
            'Pipeline', ('name', 'type', 'tasks'))

    @property
    def name(self):
        """Return the pipeline name"""
        return self._name

    def is_task_valid(self):
        """Check if the pipeline task name is valid for carbon.

        :return: whether task is valid or not.
        :rtype: bool
        """
        try:
            TASKLIST.index(self.name)
        except ValueError:
            return False
        return True

    def task_cls_lookup(self):
        """Lookup the pipeline task class type.

        :return: the class associated for the pipeline task.
        :rtype: class
        """
        for cls in get_core_tasks_classes():
            if cls.__task_name__ == self.name:
                return cls
        raise CarbonError('Unable to lookup task %s class.' % self.name)

    def build(self, scenario):
        """Build carbon pipeline.

        :param scenario: carbon scenario object containing all scenario
               data.
        :type scenario: scenario object
        :return: carbon pipeline to run for the given task for all the scenarios
        :rtype: namedtuple
        """
        # pipeline init
        pipeline = self.pipeline_template(
            self.name,
            self.task_cls_lookup(),
            list()
        )

        scenario_get_tasks = list()
        scenario_hosts = list()
        scenario_actions = list()
        scenario_executes = list()
        scenario_reports = list()

        # Check if there are any child/included scenarios
        if scenario.child_scenarios:
            for sc in scenario.child_scenarios:
                scenario_get_tasks.extend([item for item in getattr(sc, 'get_tasks')()])
                scenario_hosts.extend([item for item in getattr(sc, 'hosts')])
                scenario_actions.extend([item for item in getattr(sc, 'actions')])
                scenario_executes.extend([item for item in getattr(sc, 'executes')])
                scenario_reports.extend([item for item in getattr(sc, 'reports')])

        # only master scenario no child scenarios
        scenario_get_tasks.extend([item for item in getattr(scenario, 'get_tasks')()])
        scenario_hosts.extend([item for item in getattr(scenario, 'hosts')])
        scenario_actions.extend([item for item in getattr(scenario, 'actions')])
        scenario_executes.extend([item for item in getattr(scenario, 'executes')])
        scenario_reports.extend([item for item in getattr(scenario, 'reports')])

        # scenario resource
        for task in scenario_get_tasks:
            if task['task'].__task_name__ == self.name:
                pipeline.tasks.append(task)

        # host resource
        for host in scenario_hosts:
            for task in host.get_tasks():
                if task['task'].__task_name__ == self.name:
                    pipeline.tasks.append(set_task_class_concurrency(task, host))

        # action resource
        # get action resource based on if its status
        for action in get_actions_failed_status(scenario_actions):
            for task in action.get_tasks():
                if task['task'].__task_name__ == self.name:
                    # fetch & set hosts for the given action task
                    task = fetch_hosts(scenario_hosts, task)
                    pipeline.tasks.append(task)

        # execute resource
        for execute in scenario_executes:
            for task in execute.get_tasks():
                # fetch & set hosts for the given executes task
                task = fetch_hosts(scenario_hosts, task)
                if task['task'].__task_name__ == self.name:
                    pipeline.tasks.append(task)

        # report resource
        for report in scenario_reports:
            for task in report.get_tasks():
                # fetch & set hosts and executes for the given reports task
                task = fetch_executes(scenario_executes, scenario_hosts, task)
                if task['task'].__task_name__ == self.name:
                    pipeline.tasks.append(task)

        # reverse the order of the tasks to be executed for cleanup task
        if self.name == CleanupTask.__task_name__:
            pipeline.tasks.reverse()

        return pipeline
