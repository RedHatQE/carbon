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

from ..core import CarbonResource
from ..tasks import OrchestrateTask, ValidateTask


class Action(CarbonResource):

    _valid_tasks_types = ['validate', 'orchestrate']
    _fields = [
        'name',
        'hosts',
        'vars',
    ]

    def __init__(self,
                 config=None,
                 name=None,
                 parameters={},
                 validate_task_cls=ValidateTask,
                 orchestrate_task_cls=OrchestrateTask,
                 **kwargs):

        super(Action, self).__init__(config=config, name=name, **kwargs)

        self._validate_task_cls = validate_task_cls
        self._orchestrate_task_cls = orchestrate_task_cls

        self.hosts = []

        self.reload_tasks()

        if parameters:
            self.load(parameters)

    def _construct_validate_task(self):
        task = {
            'task': self._validate_task_cls,
            'name': str(self.name),
            'resource': self,
            'methods': self._req_tasks_methods
        }
        return task

    def _construct_orchestrate_task(self):
        """
        Used to create the create attribute by the Host constructor.
        """
        task = {
            'task': self._orchestrate_task_cls,
            'name': str(self.name),
            'package': self,
            'msg': '   running orchestration %s for %s' % (self.name, self.hosts),
            'methods': self._req_tasks_methods
        }
        return task
