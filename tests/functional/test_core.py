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
    Unit tests to test carbon core.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from time import time, sleep
from unittest import TestCase

try:
    from test.test_support import EnvironmentVarGuard
except ImportError:
    from test.support import EnvironmentVarGuard

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

from carbon.core import TimeMixin, CarbonError

from nose.tools import assert_is_instance
from nose.tools import raises


class TestTimeMixin(TestCase):
    """Test carbon's time mixin class.

    This class contains unit tests to verify the time mixin class is
    functioning okay.
    """

    def setUp(self):
        """Setup tasks to be run before each test case."""
        self.time_mixin = TimeMixin()

    @raises(CarbonError)
    def test_set_start_time(self):
        """Test method to set start time."""
        self.time_mixin.start_time = time()

    @raises(CarbonError)
    def test_set_end_time(self):
        """Test method to set start time."""
        self.time_mixin.end_time = time()

    def test_start_time(self):
        """Test method to get start time."""
        self.time_mixin.start()
        sleep(1)
        self.time_mixin.end()
        assert_is_instance(self.time_mixin.start_time, float)

    def test_end_time(self):
        """Test method to get end time."""
        self.time_mixin.start()
        sleep(1)
        self.time_mixin.end()
        assert_is_instance(self.time_mixin.end_time, float)

    def test_hours(self):
        """Test hours property."""
        self.time_mixin.start()
        sleep(1)
        self.time_mixin.end()
        assert_is_instance(self.time_mixin.hours, float)

    def test_minutes(self):
        """Test minutes property."""
        self.time_mixin.start()
        sleep(1)
        self.time_mixin.end()
        assert_is_instance(self.time_mixin.minutes, float)

    def test_seconds(self):
        """Test seconds property."""
        self.time_mixin.start()
        sleep(1)
        self.time_mixin.end()
        assert_is_instance(self.time_mixin.seconds, float)
