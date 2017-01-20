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
    carbon.resources.scenario

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from ..helpers import Resource
from ..tasks import ValidateTask, TestTask, ReportTask


class Scenario(Resource):

    _task_validate_class = ValidateTask
    _task_test_class = TestTask
    _task_report_class = ReportTask

    def __init__(self, data={}):
        super(Scenario, self).__init__(data)

    def validate(self):
        raise NotImplementedError

    def test(self):
        raise NotImplementedError

    def report(self):
        raise NotImplementedError
