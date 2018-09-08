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
    carbon.providers.static

    Carbon's static provider module which contains all the necessary
    classes and functions to process provider validation and requests.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from .._compat import string_types
from ..core import CarbonProvider


class StaticProvider(CarbonProvider):
    """
    STATIC provider implementation.
    The following fields are supported:

        name
        static_ip_address
        static_hostname

    """
    __provider_name__ = 'static'
    __provider_prefix__ = 'static_'

    _mandatory_parameters = (
        'name',
        'ip_address',
        'hostname',
    )

    _optional_parameters = ()

    _output_parameters = (
        'name',
        'hostname',
        'ip_address',
    )

    _mandatory_creds_parameters = ()

    _optional_creds_parameters = ()

    def __init__(self, **kwargs):
        super(StaticProvider, self).__init__(**kwargs)

    def validate_name(self, value):
        """Validate the resource name.

        :param value: The resource name
        :return: A boolean, true = valid, false = invalid
        """
        # Quit when no value given
        if not value:
            self.logger.warning('Invalid data for name!')
            return False

        # Name must be a string
        if not isinstance(value, string_types):
            self.logger.warning('Name is required to be a string type!')
            return False
        return True

    def validate_ip_address(self, value):
        """Validate ip address."""
        return True

    @classmethod
    def validate_hostname(cls, value):
        """Validate hostname."""
        if value:
            return isinstance(value, string_types)
        else:
            return True
