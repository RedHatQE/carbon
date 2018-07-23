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
from ..core import CarbonError
from ..helpers import fetch_hosts, get_core_tasks_classes
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
        :type scenario: object
        :return: carbon pipeline to run for the given task.
        :rtype: namedtuple
        """
        # pipeline init
        pipeline = self.pipeline_template(
            self.name,
            self.task_cls_lookup(),
            list()
        )

        # scenario resource
        for task in getattr(scenario, 'get_tasks')():
            if task['task'].__task_name__ == self.name:
                pipeline.tasks.append(task)

        # host resource
        for host in getattr(scenario, 'hosts'):
            for task in host.get_tasks():
                if task['task'].__task_name__ == self.name:
                    pipeline.tasks.append(task)

        # action resource
        for action in getattr(scenario, 'actions'):
            for task in action.get_tasks():
                if task['task'].__task_name__ == self.name:
                    # fetch & set hosts for the given action task
                    task = fetch_hosts(getattr(scenario, 'hosts'), task)
                    pipeline.tasks.append(task)

        # execute resource
        for execute in getattr(scenario, 'executes'):
            for task in execute.get_tasks():
                if task['task'].__task_name__ == self.name:
                    pipeline.tasks.append(task)

        # report resource
        for report in getattr(scenario, 'reports'):
            for task in report.get_tasks():
                if task['task'].__task_name__ == self.name:
                    pipeline.tasks.append(task)

        # reverse the order of the tasks to be executed for cleanup task
        if self.name == CleanupTask.__task_name__:
            pipeline.tasks.reverse()

        return pipeline
