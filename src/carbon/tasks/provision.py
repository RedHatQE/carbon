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
    carbon.tasks.provision

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..core import CarbonTask


class ProvisionTask(CarbonTask):
    """The provision task object will call a provisioner to provision
    resources in their declared provider. By default Carbon will be
    using the linch-pin provisioner if no provisioner was declared.
    """

    def __init__(self, msg, clean_msg, host, **kwargs):
        super(ProvisionTask, self).__init__(**kwargs)
        self.msg = msg
        self.clean_msg = clean_msg
        self.host = host
        self._provisioner = host.provisioner
        self.provisioner = self._provisioner(host.profile())

    def run(self, context):
        print(self.msg)
        self.provisioner.create()

    def cleanup(self, context):
        print(self.clean_msg)
