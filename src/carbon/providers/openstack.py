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

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..core import CarbonProvider
from .._compat import string_types


class OpenstackProvider(CarbonProvider):
    """
    Openstack provider implementation.
    The following fields are supported:

        os_flavor: (mandatory) The Flavor to boot onto.

        os_image: (mandatory) The Image to boot with.

        os_nics: (mandatory) An ordered list of nics (dicts) to be
                 added to this server, with information about connected
                 networks, fixed IPs, port etc. his field is required and
                 also supports a single string value of ‘auto’ or ‘none’.
                 The ‘auto’ value means the Compute service will
                 automatically allocate a network for the project if one is
                 not available. The ‘none’ value tells the Compute service
                 to not allocate any networking for the server.

        os_count: (mandatory) The number of resources to create.

        os_floating_ip_pool: (mandatory) The floating ip pool to use to create
                             a floating IP.

        os_key_name: (optional) name of previously created keypair to
                     inject into the instance

        os_admin_pass: (optional) add a user supplied admin password.

        os_description: (optional) description of the server.

        os_files: (optional) A dict of files to overwrite on the server
                  upon boot. Keys are file names (i.e. /etc/passwd) and
                  values are the file contents (either as a string or as
                  a file-like object). A maximum of five entries is
                  allowed, and each file must be 10k or less.

        os_security_groups: (optional)

        To add more fields for the provider, you have to also create a
        validate_* function for the field. The signature for the function
        must be validate_<paramenter_name> and the return must be True for
        valid or False if the validation fails.

        For instance, the field 'flavor' has the function 'validate_flavor'.

    """
    __provider_name__ = 'openstack'
    __provider_prefix__ = 'os_'

    _mandatory_parameters = (
        'name',
        'count',
        'flavor',
        'image',
        'networks',
        'floating_ip_pool'
    )

    _optional_parameters = (
        'key_name',
        'admin_pass',
        'description',
        'files',
        'security_groups',
    )

    _mandatory_creds_parameters = (
        'auth_url',
        'tenant_name',
        'tenant_id',
        'username',
        'password'
    )

    def __init__(self, **kwargs):
        super(OpenstackProvider, self).__init__(**kwargs)

    @classmethod
    def validate_name(cls, value):
        return isinstance(value, string_types)

    @classmethod
    def validate_flavor(cls, value):
        return isinstance(value, string_types)

    @classmethod
    def validate_image(cls, value):
        return isinstance(value, string_types)

    @classmethod
    def validate_networks(cls, value):
        return isinstance(value, list)

    @classmethod
    def validate_key_name(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_admin_pass(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_description(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_files(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_security_groups(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_count(cls, value):
        if value:
            return isinstance(value, int)
        else:
            return True

    @classmethod
    def validate_floating_ip_pool(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True
