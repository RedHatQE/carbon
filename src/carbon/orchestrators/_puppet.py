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
    carbon.orchestrators._puppet

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from ..core import CarbonOrchestrator


class PuppetOrchestrator(CarbonOrchestrator):
    """Puppet orchestrator."""

    __orchestrator_name__ = 'puppet'

    def __init__(self, action, hosts, **kwargs):
        """Constructor.

        :param action: action to be executed
        :param hosts: action runs against these hosts
        :param kwargs: action parameters
        """
        super(PuppetOrchestrator, self).__init__(action, hosts, **kwargs)

    def validate(self):
        """Validate."""
        raise NotImplementedError

    def run(self):
        """Run."""
        raise NotImplementedError
