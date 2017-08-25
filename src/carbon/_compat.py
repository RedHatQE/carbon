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
    carbon._compat

    This is a compatibility module that assists on keeping the Carbon
    Framework compatible with python 2.x and python 3.x.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import sys

_ver = sys.version_info

# Python 2.x?
is_py2 = (_ver[0] == 2)

# Python 3.x?
is_py3 = (_ver[0] == 3)

# Windows
is_win = sys.platform.startswith('win')

try:
    import simplejson as json
except (ImportError, SyntaxError):
    # simplejson does not support Python 3.2, it throws a SyntaxError
    # because of u'...' Unicode literals.
    import json

try:
    import builtins
except ImportError:
    import __builtin__ as builtins

if is_py2:
    string_types = (str, unicode)
else:
    string_types = (str, )
