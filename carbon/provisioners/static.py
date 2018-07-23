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
    carbon.provisioners.static

    Carbon's own Static provisioner. This module handles everything from
    to creating/deleting resources in .

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..core import CarbonProvisioner


class StaticProvisioner(CarbonProvisioner):
    """Carbon's static provisioner.

    This class is a base which calls static provider methods to perform
    the actions to create and delete resources.
    """
    __provisioner_name__ = 'static'

    def __init__(self, host):
        """Constructor.

        :param host: The host object.
        """
        super(StaticProvisioner, self).__init__()
        self.host = host

    def _create(self):
        """Create a static node 

        This method will call the static provider create method. The
        provider class handles all interactions with the provider.
        """
        self.logger.info('Provisioning static machines %s', self.__class__)

        # set new attributes in host object
        self.host.set_ip_address([str(self.host.static_ip_address)])
        self.host.hostname = str(self.host.static_hostname)

        self.logger.info("Successfully provisioned static machine %s." % self.host.hostname)

    def _delete(self):
        """Delete a static node.

        This method will call the static provider delete method. The
        provider class handles all interactions with the provider.
        """
        self.logger.info('Tearing down static machines from %s', self.__class__)
        self.logger.info('Nothing to do. Machines user defined. Not tearing down static machine %s' % self.host.hostname)
