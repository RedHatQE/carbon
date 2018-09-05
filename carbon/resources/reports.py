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

    Module used for building carbon report compounds. A report's main goal is
    to handle reporting results to external resources.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..core import CarbonResource
from ..tasks import ReportTask, ValidateTask


class Report(CarbonResource):
    """
    The report resource class.
    """

    _valid_tasks_types = ['validate', 'report']
    _fields = ['name', 'description', 'type']

    def __init__(self,
                 config=None,
                 name=None,
                 parameters={},
                 validate_task_cls=ValidateTask,
                 report_task_cls=ReportTask,
                 **kwargs):
        """Constructor.

        :param config: carbon configuration
        :type config: dict
        :param name: report resource name
        :type name: str
        :param parameters: content which makes up the report resource
        :type parameters: dict
        :param validate_task_cls: carbons validate task class
        :type validate_task_cls: object
        :param report_task_cls: carbons report task class
        :type report_task_cls: object
        :param kwargs: additional key:value(s)
        :type kwargs: dict
        """
        super(Report, self).__init__(config=config, name=name, **kwargs)

        # set the carbon task classes for the resource
        self._validate_task_cls = validate_task_cls
        self._report_task_cls = report_task_cls

        # reload construct task methods
        self.reload_tasks()

        # load the parameters into the object itself
        if parameters:
            self.load(parameters)

    def profile(self):
        """Builds a profile for the report resource.

        :return: the report profile
        :rtype: dict
        """
        return {}

    def _construct_validate_task(self):
        """Constructs the validate task associated to the report resource.

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

    def _construct_report_task(self):
        """Constructs the report task associated to the report resource.

        :return: report task definition
        :rtype: dict
        """
        task = {
            'task': self._report_task_cls,
            'name': str(self.name),
            'package': self,
            'msg': '   reporting %s' % self.name,
            'methods': self._req_tasks_methods
        }
        return task
