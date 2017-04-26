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
    carbon.providers.digitalocean

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..core import CarbonProvider


class DigitalOceanProvider(CarbonProvider):
    """
    Digital Ocean provider implementation.
    The following fields are supported:

        do_name:

        ...

    """
    __provider_name__ = 'digitalocean'
    __provider_prefix__ = 'do_'

    _mandatory_parameters = ()

    _optional_parameters = ()

    _mandatory_creds_parameters = ()

    def __init__(self, **kwargs):
        super(DigitalOceanProvider, self).__init__(**kwargs)
