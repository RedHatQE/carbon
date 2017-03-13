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
import uuid

from ..core import CarbonResource
from ..tasks import ProvisionTask, CleanupTask, ValidateTask


class Host(CarbonResource):

    _valid_tasks_types = ['validate', 'provision', 'cleanup']
    _valid_fields = ['name']

    def __init__(self,
                 name=None,
                 validate_task_cls=ValidateTask,
                 provision_task_cls=ProvisionTask,
                 cleanup_task_cls=CleanupTask,
                 data={},
                 **kwargs):
        super(Host, self).__init__(name, **kwargs)

        if name is None:
            self._name = str(uuid.uuid4())

        self._validate_task_cls = validate_task_cls
        self._provision_task_cls = provision_task_cls
        self._cleanup_task_cls = cleanup_task_cls

        self.reload_tasks()

        if data:
            self.load(data)

    def _construct_validate_task(self):
        task = {
            'task': self._validate_task_cls,
            'name': str(self.name),
            'package': self,
            'msg': '   validating host %s' % self.name,
            'clean_msg': '   cleanup after validating host %s' % self.name
        }
        return task

    def _construct_provision_task(self):
        task = {
            'task': self._provision_task_cls,
            'name': str(self.name),
            'host': self,
            'msg': '   provisioning host %s' % self.name,
            'clean_msg': '   cleanup after provisioning host %s' % self.name
        }
        return task

    def _construct_cleanup_task(self):
        task = {
            'task': self._cleanup_task_cls,
            'name': str(self.name),
            'host': self,
            'msg': '   cleanup host %s' % self.name,
            'clean_msg': '   cleanup after cleanup host %s' % self.name
        }
        return task
