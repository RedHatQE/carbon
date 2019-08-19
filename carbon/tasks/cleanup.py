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
from ..core import CarbonTask
from ..exceptions import CarbonOrchestratorError


class CleanupTask(CarbonTask):
    """Cleanup task."""
    __concurrent__ = False
    __task_name__ = 'cleanup'

    def __init__(self, msg, asset=None, package=None, **kwargs):
        """Constructor.

        :param msg: task message
        :type msg: str
        :param asset: asset reference
        :type asset: object
        :param package: package reference
        :type package: object
        :param kwargs: additional keyword arguments
        :type kwargs: dict
        """
        super(CleanupTask, self).__init__(**kwargs)

        # set attributes
        self.msg = msg
        self.asset = asset
        self.package = package

    def _get_orchestrator_instance(self):
        """Get the orchestrator instance to perform clean up actions with.

        :return: orchestrator class instance
        :rtype: object
        """
        # set package attributes to get actual asset objects over strings
        cleanup = getattr(self.package, 'cleanup')
        setattr(cleanup, 'all_assets', getattr(self.package, 'all_assets'))
        setattr(cleanup, 'assets', getattr(self.package, 'assets'))

        # create the orchestrator object
        return getattr(self.package, 'orchestrator')(cleanup)

    def run(self):
        """Run.

        This method is the main entry point to the task.
        """
        self.logger.info(self.msg)

        # **** TASKS BELOW ONLY SHOULD BE RELATED TO THE ORCHESTRATOR ****
        if self.package and getattr(self.package, 'cleanup') is not None:
            # get the orchestrator to invoke
            orchestrator = self._get_orchestrator_instance()

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
        if self.asset:
            try:

                # let's try to create the provisioner gateway implementation first
                if getattr(self.asset, 'provisioner_plugin') is not None:
                    plugin = getattr(self.asset, 'provisioner_plugin')(self.asset)
                    self.logger.debug('Asset loaded the following provisioner plugin: %s' % plugin.__plugin_name__)
                    provisioner = getattr(self.asset, 'provisioner')(self.asset, plugin)
                    self.logger.debug('Asset loaded the following provisioner interface: %s'
                                      % provisioner.__provisioner_name__)
                else:
                    # create the provisioner object
                    provisioner = getattr(self.asset, 'provisioner')(self.asset)
                    self.logger.debug('Asset loaded the following provisioner interface: %s'
                                      % provisioner.__provisioner_name__)

                # teardown the asset
                getattr(provisioner, 'delete')()
            except AttributeError:
                self.logger.warning('Asset %s is static, skipping teardown.' %
                                    getattr(self.asset, 'name'))
