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

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..core import CarbonProvisioner


class OpenstackProvisioner(CarbonProvisioner):
    """
    Carbon's own openstack provisioner
    """
    __provisioner_name__ = 'openstack'

    def __init__(self, **kwargs):
        super(OpenstackProvisioner, self).__init__(**kwargs)

    def create(self):
        print('Provisioning machines from {klass}'
              .format(klass=self.__class__))

    def delete(self):
        print('Tearing down machines from {klass}'
              .format(klass=self.__class__))
