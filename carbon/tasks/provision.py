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
    carbon.tasks.provision

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..core import CarbonTask
import time


class ProvisionTask(CarbonTask):
    """Provision task."""
    __task_name__ = 'provision'
    __concurrent__ = True

    def __init__(self, msg, host, **kwargs):
        """Constructor.

        :param msg: task message
        :type msg: str
        :param host: host reference
        :type host: str
        :param kwargs: additional keyword arguments
        :type kwargs: dict
        """
        super(ProvisionTask, self).__init__(**kwargs)
        self.msg = msg
        self.provision = True

        if not host.is_static:
            # create the provisioner object to create hosts
            try:
                # TODO We should move this code out into the Host Resource to instantiate there?
                # let's try to create the provisioner gateway implementation first
                if getattr(host, 'provisioner_plugin') is not None:
                    plugin = getattr(host, 'provisioner_plugin')(host)
                    self.logger.debug('Host loaded the following provisioner plugin: %s'
                                      % plugin.__plugin_name__)
                    self.provisioner = getattr(host, 'provisioner')(host, plugin)
                    self.logger.debug('Host loaded the following provisioner interface: %s'
                                      % self.provisioner.__provisioner_name__)
                else:
                    self.provisioner = getattr(host, 'provisioner')(host)
                    self.logger.debug('Host loaded the following provisioner interface: %s'
                                      % self.provisioner.__provisioner_name__)
            except AttributeError as ex:
                self.logger.error(ex)
                raise
        else:
            self.provision = False
            self.logger.warning('Host %s is static, provision will be '
                                'skipped.' % getattr(host, 'name'))

    def run(self):
        """Run.

        This method is the main entry point to the task.
        """
        # provision the host given in their declared provider
        if self.provision:
            self.logger.info(self.msg)
            try:
                self.provisioner.create()
            except Exception as ex:
                self.logger.error('Failed to provision node %s' % self.name)
                stackmsg = self.get_formatted_traceback()
                self.logger.error(ex)
                self.logger.error(stackmsg)
                raise
