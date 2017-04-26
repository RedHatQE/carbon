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

    Here you add brief description of what this module is about

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
        'arch',
        'tag',
        'family',
        'variant',
    )

    _mandatory_creds_parameters = ()

    def __init__(self, **kwargs):
        super(BeakerProvider, self).__init__(**kwargs)

    @classmethod
    def validate_arch(cls, value):
        return isinstance(value, string_types)

    @classmethod
    def validate_tag(cls, value):
        return isinstance(value, list)

    @classmethod
    def validate_family(cls, value):
        return isinstance(value, string_types)

    @classmethod
    def validate_variant(cls, value):
        return isinstance(value, string_types)
