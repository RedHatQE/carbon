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

from ..core import CarbonResource
from ..tasks import ValidateTask, TestTask, ReportTask
from ..resources import Host


class Scenario(CarbonResource):

    _validate_task_class = ValidateTask
    _test_task_class = TestTask
    _report_task_class = ReportTask

    def __init__(self, data={}):

        # if there's a package in the data, remove so we
        # do not conflict with the hosts list in the class.
        tmp_data = dict(data)
        tmp_data.pop('hosts', None)

        super(Scenario, self).__init__(tmp_data)

        self._hosts = list()

        self._add_task(self._make_validate_task())
        self._add_task(self._make_test_task())
        self._add_task(self._make_report_task())

    @property
    def hosts(self):
        return self._hosts

    @hosts.setter
    def hosts(self, value):
        raise ValueError("You can't set hosts directly. Use function add_hosts")

    def add_hosts(self, h):
        if not isinstance(h, Host):
            raise ValueError("Host must be of type %s " % type(Host))
        self._hosts.append(h)

    def _make_validate_task(self):
        """
        Used to create the provision attribute by the Host constructor.
        """
        task = {
            'task': self._validate_task_class,
            'name': str(self.name),
            'package': self,
            'msg': 'validating "%s"' % self.name,
            'clean_msg': 'cleanup after validating "%s"' % self.name
        }
        return task

    def _make_test_task(self):
        """
        Used to create the config attribute by the Host constructor.
        """
        task = {
            'task': self._test_task_class,
            'name': str(self.name),
            'package': self,
            'msg': 'running tests for "%s"' % self.name,
            'clean_msg': 'cleanup after running tests for "%s"' % self.name
        }
        return task

    def _make_report_task(self):
        """
        Used to create the config attribute by the Host constructor.
        """
        task = {
            'task': self._report_task_class,
            'name': str(self.name),
            'package': self,
            'msg': 'reporting "%s"' % self.name,
            'clean_msg': 'cleanup after reporting "%s"' % self.name
        }
        return task
