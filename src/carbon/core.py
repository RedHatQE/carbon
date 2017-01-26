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
    carbon.core

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import inspect

from taskrunner import Task
from .helpers import CustomDict, get_valid_tasks_types


class CarbonTask(Task):

    def __init__(self, name=None, **kwargs):
        super(CarbonTask, self).__init__(**kwargs)

        if name is not None:
            self.name = name

    def run(self, context):
        pass

    def cleanup(self, context):
        pass

    def __str__(self):
        return self.name


class CarbonResource(CustomDict):

    def __init__(self, data={}):
        super(CarbonResource, self).__init__(data)

        # A list of tasks that will be executed upon the reource.
        self._tasks = []

    def _add_task(self, t):
        """
        Add a task to the list of tasks for the resource
        """
        if t['task'] not in set(get_valid_tasks_types()):
            raise Exception("The task is not a valid type.")

        self._tasks.append(t)

    def get_tasks(self):
        return self._tasks

    def _extract_tasks_from_resource(self):
        lst = []
        for name, obj in inspect.getmembers(self, inspect.isclass):
            if issubclass(obj, CarbonTask):
                lst.append(name)
        return lst
