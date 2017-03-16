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
import uuid

from ..core import CarbonResource
from ..tasks import ReportTask, ValidateTask


class Report(CarbonResource):

    _valid_tasks_types = ['validate', 'report']
    _fields = ['name', 'type']

    def __init__(self,
                 name=None,
                 parameters={},
                 validate_task_cls=ValidateTask,
                 report_task_cls=ReportTask,
                 **kwargs):

        super(Report, self).__init__(name, **kwargs)

        self._validate_task_cls = validate_task_cls
        self._report_task_cls = report_task_cls

        self.reload_tasks()

        if parameters:
            self.load(parameters)

    def _construct_validate_task(self):
        task = {
            'task': self._validate_task_cls,
            'name': str(self.name),
            'package': self,
            'msg': '   validating package %s' % self.name,
            'clean_msg': '   cleanup after validating package %s' % self.name
        }
        return task

    def _construct_report_task(self):
        task = {
            'task': self._report_task_cls,
            'name': str(self.name),
            'package': self,
            'msg': '   reporting %s' % self.name,
            'clean_msg': '   cleanup after reporting %s' % self.name
        }
        return task
