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
    carbon.tasks.validate

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..core import CarbonTask
from ..signals import task_validation_started, task_validation_finished


class ValidateTask(CarbonTask):
    """Validate task."""
    __task_name__ = 'validate'

    def __init__(self, resource, **kwargs):
        super(ValidateTask, self).__init__(**kwargs)
        self.resource = resource

    def run(self):
        task_validation_started.send(self, resource=self.resource)
        self.logger.info(
            'Validating %s (%s)', self.resource.__class__, self.resource.name
        )
        self.resource.validate()
        task_validation_finished.send(self, resource=self.resource)
