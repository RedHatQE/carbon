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
    carbon.resources.host

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..core import CarbonResource
from ..tasks import ProvisionTask, TeardownTask, ConfigTask, ValidateTask


class Host(CarbonResource):

    _validate_task_class = ValidateTask
    _provision_task_class = ProvisionTask
    _config_task_class = ConfigTask
    _teardown_task_class = TeardownTask

    def __init__(self, data={}):
        # if there's a package in the data, remove so we
        # do not conflict with the packages list in the class.
        tmp_data = dict(data)
        tmp_data.pop('packages', None)

        super(Host, self).__init__(tmp_data)

        self.packages = list()

        self._add_task(self._make_validate_task())
        self._add_task(self._make_provision_task())
        self._add_task(self._make_config_task())
        self._add_task(self._make_teardown_task())

    def _make_validate_task(self):
        """
        Used to create the config attribute by the Host constructor.
        """
        task = {
            'task': self._validate_task_class,
            'name': str(self.name),
            'package': self,
            'msg': 'validating host %s' % self.name,
            'clean_msg': 'cleanup after validating host %s' % self.name
        }
        return task

    def _make_provision_task(self):
        """
        Used to create the provision attribute by the Host constructor.
        """
        task = {
            'task': self._provision_task_class,
            'name': str(self.name),
            'host': self,
            'msg': 'provisioning %s' % self.name,
            'clean_msg': 'cleanup after provisioning %s' % self.name
        }
        return task

    def _make_config_task(self):
        """
        Used to create the config attribute by the Host constructor.
        """
        task = {
            'task': self._config_task_class,
            'name': str(self.name),
            'host': self,
            'msg': 'configuring %s' % self.name,
            'clean_msg': 'cleanup after configuring %s' % self.name
        }
        return task

    def _make_teardown_task(self):
        """
        Used to create the teardown attribute by the Host constructor.
        """
        task = {
            'task': self._teardown_task_class,
            'name': str(self.name),
            'host': self,
            'msg': 'teardown %s' % self.name,
            'clean_msg': 'cleanup after teardown %s' % self.name
        }
        return task
