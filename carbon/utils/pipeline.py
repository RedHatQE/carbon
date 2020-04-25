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

from ..constants import TASKLIST, NOTIFYSTATES
from ..exceptions import CarbonError
from ..helpers import fetch_assets, get_core_tasks_classes, fetch_executes, filter_actions_on_failed_status, \
    set_task_class_concurrency, filter_resources_labels, filter_notifications_to_skip, filter_notifications_on_trigger
from ..tasks import CleanupTask


class PipelineFactory(object):

    @staticmethod
    def get_pipeline(task):
        if task in TASKLIST:
            return PipelineBuilder(task)
        else:
            return NotificationPipelineBuilder(task)


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

    def build(self, scenario, carbon_options):
        """Build carbon pipeline.

        This method first collects scenario tasks and resources for each scenario(child and master). It filters out
        specific resources for the scenario based on if labels or skip_labels are provided in carbon options.
        If no labels/ skip_labels are provided all resources for that scenario are picked.
        Then for each of the resource/scenario task the method checks if that resource/scenario tasks has any tasks
        with name matching the name for self.task(the task for which the pipeline is getting built). If it has then that
        tasks gets added to the pipeline and that gets returned

        :param scenario: carbon scenario object containing all scenario
               data.
        :type scenario: scenario object
        :param carbon_options: extra options provided during carbon run
        :type carbon_options: dict
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
        scenario_assets = list()
        scenario_actions = list()
        scenario_executes = list()
        scenario_reports = list()

        # Get all tasks for the scenario and its included scenarios
        if scenario.child_scenarios:
            for sc in scenario.child_scenarios:
                scenario_get_tasks.extend([item for item in getattr(sc, 'get_tasks')()])
        # only master scenario no child scenarios
        scenario_get_tasks.extend([item for item in getattr(scenario, 'get_tasks')()])

        # get all resources for scenario/included scenario validated and filtered using labels
        scenario_assets.extend([item for item in filter_resources_labels(scenario.get_all_assets(), carbon_options)])
        scenario_actions.extend([item for item in filter_resources_labels(scenario.get_all_actions(), carbon_options)])
        scenario_executes.extend([item for item in filter_resources_labels(scenario.get_all_executes(),
                                                                           carbon_options)])
        scenario_reports.extend([item for item in filter_resources_labels(scenario.get_all_reports(), carbon_options)])

        # get notifications
        scenario_notifications = [item for item in filter_notifications_to_skip(scenario.get_all_notifications(),
                                                                                carbon_options)]

        # scenario resource
        for task in scenario_get_tasks:
            if task['task'].__task_name__ == self.name:
                pipeline.tasks.append(set_task_class_concurrency(task, task['resource']))

        # asset resource
        for asset in scenario_assets:
            for task in asset.get_tasks():
                if task['task'].__task_name__ == self.name:
                    pipeline.tasks.append(set_task_class_concurrency(task, asset))

        # action resource
        # get action resource based on if its status
        # check if cleanup task do NOT filter by status
        if self.name != 'cleanup':
            scenario_actions = filter_actions_on_failed_status(scenario_actions)
        for action in scenario_actions:
            for task in action.get_tasks():
                if task['task'].__task_name__ == self.name:
                    # fetch & set hosts for the given action task
                    task = fetch_assets(scenario_assets, task)
                    pipeline.tasks.append(set_task_class_concurrency(task, action))

        # execute resource
        for execute in scenario_executes:
            for task in execute.get_tasks():
                if task['task'].__task_name__ == self.name:
                    # fetch & set hosts for the given executes task
                    task = fetch_assets(scenario_assets, task)
                    pipeline.tasks.append(set_task_class_concurrency(task, execute))

        # report resource
        for report in scenario_reports:
            for task in report.get_tasks():
                if task['task'].__task_name__ == self.name:
                    # fetch & set hosts and executes for the given reports task
                    task = fetch_executes(scenario_executes, scenario_assets, task)
                    pipeline.tasks.append(set_task_class_concurrency(task, report))

        # reverse the order of the tasks to be executed for cleanup task
        if self.name == CleanupTask.__task_name__:
            pipeline.tasks.reverse()

        # notification resource
        for notification in scenario_notifications:
            for task in notification.get_tasks():
                if task['task'].__task_name__ == self.name:
                    task['resource'].scenario = scenario
                    pipeline.tasks.append(task)

        return pipeline


class NotificationPipelineBuilder(PipelineBuilder):

    """
    The primary class for building carbons notification pipelines to execute.
    """

    def __init__(self, trigger):

        super(NotificationPipelineBuilder, self).__init__('notify')
        self.trigger = trigger

    def is_task_valid(self):
        """Check if the pipeline task name is valid for carbon.

        :return: whether task is valid or not.
        :rtype: bool
        """
        try:
            NOTIFYSTATES.index(self.trigger)
        except ValueError:
            return False
        return True

    def build(self, scenario, carbon_options):
        """Build carbon notification pipeline.

        This method first collects scenario tasks and resources for each scenario(child and master). It filters out
        specific resources for the scenario based on if labels or skip_labels are provided in carbon options.
        If no labels/ skip_labels are provided all resources for that scenario are picked.
        Then for each of the resource/scenario task the method checks if that resource/scenario tasks has any tasks
        with name matching the name for self.task(the task for which the pipeline is getting built). If it has then that
        tasks gets added to the pipeline and that gets returned

        :param scenario: carbon scenario object containing all scenario
               data.
        :type scenario: scenario object
        :param carbon_options: extra options provided during carbon run
        :type carbon_options: dict
        :return: carbon notification pipeline to run for the given task for all the scenarios
        :rtype: namedtuple
        """

        # pipeline init
        pipeline = self.pipeline_template(
            self.name,
            self.task_cls_lookup(),
            list()
        )

        # get notifications
        scenario_notifications = [item for item in filter_notifications_to_skip(scenario.get_all_notifications(),
                                                                                carbon_options)]
        scenario_notifications = [item for item in
                                  filter_notifications_on_trigger(self.trigger, scenario_notifications,
                                                                  getattr(scenario, 'passed_tasks'),
                                                                  getattr(scenario, 'failed_tasks'))
                                  ]

        # notification resource
        for notification in scenario_notifications:
            for task in notification.get_tasks():
                if task['task'].__task_name__ == self.name:
                    task['resource'].scenario = scenario
                    pipeline.tasks.append(task)

        return pipeline
