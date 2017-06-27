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

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..core import CarbonProvider
from .._compat import string_types


class BeakerProvider(CarbonProvider):
    """
    Beaker provider implementation
    """
    __provider_name__ = 'beaker'
    __provider_prefix__ = 'bkr_'

    _mandatory_parameters = (
        'name',
        'arch',
        'variant'
    )

    _optional_parameters = (
        'distro',
        'family',
        'whiteboard',
        'kernel_options',
        'kernel_post_options',
        'host_requires_options',
        'distro_requires_options',
        'virtual_machine',
        'virt_capable',
        'retention_tag',
        'tag',
        'priority',
        'kdump',
        'ndump',
        'jobgroup',
        'key_values',
        'timeout',
        'hostname',
        'ip_address',
        'job_id',
        'ssh_key',
        'keytab',
    )

    _output_parameters = (
        'hostname',
        'ip_address',
        'job_id',
    )

    _mandatory_creds_parameters = ()

    _optional_creds_parameters = (
        'keytab',
        'keytab_principal',
        'username',
        'password'
    )

    _assets_parameters = (
        'ssh_key',
        'keytab',
    )

    def __init__(self, **kwargs):
        super(BeakerProvider, self).__init__(**kwargs)

    def validate_name(self, value):
        """Validate the resource name.
        :param value: The resource name
        :return: A boolean, true = valid, false = invalid
        """
        self.logger.info("Validating Name: {0}".format(value))
        # Quit when no value given
        if not value:
            self.logger.warn('Invalid data for name!')
            return False

        # Name must be a string
        if not isinstance(value, string_types):
            self.logger.warn("Name is required to be a string type!")
            return False

        return True

    def validate_timeout(self, value):
        if value:
            self.logger.info("Validating env vars: {0}".format(value))
            if isinstance(value, int) and (3600 <= value <= 172800):
                return True
            else:
                self.logger.warn("Beaker timeout must be between 3600(1hr)"
                                 " and 172800(48hrs)")
                return False
        else:
            return True

    @classmethod
    def validate_arch(cls, value):
        return isinstance(value, string_types)

    @classmethod
    def validate_tag(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_family(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_variant(cls, value):
        return isinstance(value, string_types)

    @classmethod
    def validate_distro(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_kernel_options(cls, value):
        if value:
            return isinstance(value, list)
        else:
            return True

    @classmethod
    def validate_kernel_post_options(cls, value):
        if value:
            return isinstance(value, list)
        else:
            return True

    @classmethod
    def validate_host_requires_options(cls, value):
        if value:
            return isinstance(value, list)
        else:
            return True

    @classmethod
    def validate_distro_requires_options(cls, value):
        if value:
            return isinstance(value, list)
        else:
            return True

    @classmethod
    def validate_virtual_machine(cls, value):
        if value:
            return isinstance(value, bool)
        else:
            return True

    @classmethod
    def validate_virt_capable(cls, value):
        if value:
            return isinstance(value, bool)
        else:
            return True

    @classmethod
    def validate_retention_tag(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_kdump(cls, value):
        if value:
            return isinstance(value, bool)
        else:
            return True

    @classmethod
    def validate_ndump(cls, value):
        if value:
            return isinstance(value, bool)
        else:
            return True

    @classmethod
    def validate_priority(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_whiteboard(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_jobgroup(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_key_values(cls, value):
        if value:
            return isinstance(value, list)
        else:
            return True

    @classmethod
    def validate_keytab(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_ssh_key(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_hostname(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_ip_address(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_job_id(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True
