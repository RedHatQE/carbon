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
    carbon.logging

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from __future__ import absolute_import

from logging import getLogger, StreamHandler, Formatter, getLoggerClass, \
    DEBUG

DEBUG_LOG_FORMAT = (
    '-' * 80 + '\n' +
    '%(levelname)s in %(module)s [%(pathname)s:%(lineno)d]:\n' +
    '%(message)s\n' +
    '-' * 80
)


def _should_log_for(app, mode):
    policy = app.config['LOGGER_HANDLER_POLICY']
    if policy == mode or policy == 'always':
        return True
    return False


def create_logger(app):
    """Creates a logger for the given application.  This logger works
    similar to a regular Python logger but changes the effective logging
    level based on the application's debug flag.  Furthermore this
    function also removes all attached handlers in case there was a
    logger with the log name before.

    :copyright: (c) 2015 by Armin Ronacher.
    """
    logger_cls = getLoggerClass()

    class DebugLogger(logger_cls):
        def getEffectiveLevel(self):
            if self.level == 0 and app.debug:
                return DEBUG
            return logger_cls.getEffectiveLevel(self)

    class DebugHandler(StreamHandler):
        def emit(self, record):
            if app.debug and _should_log_for(app, 'debug'):
                StreamHandler.emit(self, record)

    debug_handler = DebugHandler()
    debug_handler.setLevel(DEBUG)
    debug_handler.setFormatter(Formatter(DEBUG_LOG_FORMAT))

    logger = getLogger(app.logger_name)
    # just in case that was not a new logger, get rid of all the handlers
    # already attached to it.
    del logger.handlers[:]
    logger.__class__ = DebugLogger
    logger.addHandler(debug_handler)
    return logger
