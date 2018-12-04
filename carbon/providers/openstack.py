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
    carbon.providers.openstack

    Carbon's openstack provider module which contains all the necessary
    classes and functions to process provider validation and requests.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from ..core import CloudProvider


class OpenstackProvider(CloudProvider):
    """OpenStack Provider class."""
    __provider_name__ = 'openstack'

    def __init__(self):
        """Constructor.

        Sets the following attributes:
            - required provider parameters
            - optional provider parameters
            - required provider credential parameters
            - optional provider credential parameters

        Each attribute is a list of tuples. Within the tuple index 0 is the
        parameter name and the index 1 is the data type for the parameter.
        """
        super(OpenstackProvider, self).__init__()

        self.opt_params = [
            ('floating_ip_pool', [str]),
            ('keypair', [str])
        ]

        self.req_credential_params = [
            ('auth_url', [str]),
            ('tenant_name', [str]),
            ('username', [str]),
            ('password', [str])
        ]

        self.opt_credential_params = [
            ('region', [str]),
            ('domain_name', [str])
        ]
