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


class ProvisionTask(CarbonTask):
    """Provision task."""
    __task_name__ = 'provision'

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

        # create the provisioner object to create hosts
        try:
            self.provisioner = getattr(host, 'provisioner')(host)
        except AttributeError:
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
            self.provisioner.create()
