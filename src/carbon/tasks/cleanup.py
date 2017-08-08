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
    carbon.tasks.teardown

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..constants import TASK_CLEANUP_CHOICES
from ..core import CarbonTask
from ..signals import task_cleanup_started, task_cleanup_finished


class CleanupTask(CarbonTask):

    def __init__(self, msg, clean_msg, host, **kwargs):
        super(CleanupTask, self).__init__(**kwargs)
        self.msg = msg
        self.clean_msg = clean_msg
        self.provisioner = host.provisioner(host)
        self.cleanup_level = kwargs['cleanup']

    def run(self, context):
        task_cleanup_started.send(self, context=context)
        self.logger.info(self.msg)

        # Delete resources when cleanup level is not never or on_failure
        # Should always be the last action to be run for ~CleanupTask.run()
        if self.cleanup_level == TASK_CLEANUP_CHOICES[1] or self.cleanup_level\
                == TASK_CLEANUP_CHOICES[4]:
            self.logger.warn('Skipping resource deletion.')
        else:
            self.provisioner.delete()
        task_cleanup_finished.send(self, context=context)

    def cleanup(self, context):
        self.logger.info(self.clean_msg)
