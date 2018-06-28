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
    carbon.provisioners.openstack

    Carbon's own OpenStack provisioner. This module handles everything from
    authentication to creating/deleting resources in OpenStack.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..core import CarbonProvisioner


class OpenstackProvisioner(CarbonProvisioner):
    """Carbon's openstack provisioner.

    This class is a base which calls openstack provider methods to perform
    the actions to create and delete resources.
    """
    __provisioner_name__ = 'openstack'

    def __init__(self, host):
        """Constructor.

        :param host: The host object.
        """
        super(OpenstackProvisioner, self).__init__()
        self.host = host

    def _create(self):
        """Create a node in openstack.

        This method will call the openstack provider create method. The
        provider class handles all interactions with the provider.
        """
        self.logger.info('Provisioning machines from %s', self.__class__)

        _ip, _id = self.host.provider._create(
            self.host.os_name,
            self.host.os_image,
            self.host.os_flavor,
            self.host.os_networks,
            self.host.os_keypair,
            self.host.os_floating_ip_pool
        )

        # set new attributes in host object
        self.host.set_ip_address([str(_ip)])
        self.host.os_node_id = str(_id)

    def _delete(self):
        """Delete a node in openstack.

        This method will call the openstack provider delete method. The
        provider class handles all interactions with the provider.
        """
        self.logger.info('Tearing down machines from %s', self.__class__)

        self.host.provider._delete(self.host.os_name)
