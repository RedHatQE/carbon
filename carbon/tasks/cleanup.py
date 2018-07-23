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
    carbon.tasks.cleanup

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..core import CarbonTask, CarbonOrchestratorError


class CleanupTask(CarbonTask):
    """Cleanup task."""
    __concurrent__ = False
    __task_name__ = 'cleanup'

    def __init__(self, msg, host=None, package=None, **kwargs):
        """Constructor.

        :param msg: task message
        :type msg: str
        :param host: host reference
        :type host: object
        :param package: package reference
        :type package: object
        :param kwargs: additional keyword arguments
        :type kwargs: dict
        """
        super(CleanupTask, self).__init__(**kwargs)

        # set attributes
        self.msg = msg
        self.host = host
        self.package = package

    def run(self):
        """Run.

        This method is the main entry point to the task.
        """
        self.logger.info(self.msg)

        # **** TASKS BELOW ONLY SHOULD BE RELATED TO THE ORCHESTRATOR ****
        if self.package and getattr(self.package, 'cleanup') is not None:
            # set package attributes to get actual host objects over strings
            cleanup = getattr(self.package, 'cleanup')
            setattr(cleanup, 'all_hosts', getattr(self.package, 'all_hosts'))
            setattr(cleanup, 'hosts', getattr(self.package, 'hosts'))

            # create the orchestrator object
            orchestrator = getattr(self.package, 'orchestrator')(cleanup)

            # perform final system configuration against test systems
            try:
                getattr(orchestrator, 'run')()
            except CarbonOrchestratorError:
                self.logger.warning(
                    'Errors raised during cleanup orchestrate tasks are '
                    'silenced. This allows all tasks to run through their '
                    'cleanup tasks.'
                )

        # **** TASKS BELOW ONLY SHOULD BE RELATED TO THE PROVISIONER ****
        if self.host:
            # create the provisioner object
            provisioner = getattr(self.host, 'provisioner')(self.host)

            # teardown the host
            getattr(provisioner, 'delete')()
