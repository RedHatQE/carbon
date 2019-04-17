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
    carbon.providers.beaker

    Carbon's beaker provider module which contains all the necessary
    classes and functions to process provider validation and requests.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from ..core import PhysicalProvider


class BeakerProvider(PhysicalProvider):
    """Beaker provider class."""
    __provider_name__ = 'beaker'

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
        super(BeakerProvider, self).__init__()

        self.req_params = [
            ('name', [str]),
            ('arch', [str]),
            ('variant', [str])
        ]

        self.opt_params = [
            ('distro', [str]),
            ('family', [str]),
            ('whiteboard', [str]),
            ('kernel_options', [list]),
            ('kernel_post_options', [list]),
            ('host_requires_options', [list]),
            ('distro_requires_options', [list]),
            ('virtual_machine', [bool]),
            ('virt_capable', [bool]),
            ('retention_tag', [str]),
            ('tag', [str]),
            ('priority', [str]),
            ('jobgroup', [str]),
            ('key_values', [list]),
            ('timeout', [int]),
            ('hostname', [str]),
            ('ip_address', [str]),
            ('job_id', [str]),
            ('ssh_key', [str]),
            ('username', [str]),
            ('password', [str]),
            ('taskparam', [list]),
            ('ignore_panic', [str]),
            ('kickstart', [str]),
            ('ksmeta', [list])
        ]

        self.req_credential_params = [
            ('hub_url', [str])
        ]

        self.opt_credential_params = [
            ('keytab_principal', [str]),
            ('keytab', [str]),
            ('username', [str]),
            ('password', [str]),
            ('ca_path', [str]),
            ('realm', [str]),
            ('service', [str]),
            ('ccache', [str])
        ]
