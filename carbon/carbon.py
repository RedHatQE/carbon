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
    carbon.scenario

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import os
import sys
from threading import Lock

from .config import Config, ConfigAttribute
from .helpers import _PackageBoundObject, get_root_path, LockedCachedProperty
from .tasks import ValidateTask, CheckTask, ProvisionTask
from .tasks import ConfigTask, InstallTask, TestTask
from .tasks import ReportTask, TeardownTask

#: a lock used for logger initialization
_logger_lock = Lock()

_MASTER_PIPELINE = [
    {'name': 'validate',  'type': ValidateTask,  'pipeline': []},
    {'name': 'check',     'type': CheckTask,     'pipeline': []},
    {'name': 'provision', 'type': ProvisionTask, 'pipeline': []},
    {'name': 'config',    'type': ConfigTask,    'pipeline': []},
    {'name': 'install',   'type': InstallTask,   'pipeline': []},
    {'name': 'test',      'type': TestTask,      'pipeline': []},
    {'name': 'report',    'type': ReportTask,    'pipeline': []},
    {'name': 'teardown',  'type': TeardownTask,  'pipeline': []},
]


class Carbon(_PackageBoundObject):
    """The Carbon object acts as the central object."""

    #: The class that is used for the ``config`` attribute of this app.
    #: Defaults to :class:`~carbon.Config`.
    #:
    #: Example use cases for a custom class:
    #:
    #: 1. Default values for certain config options.
    #: 2. Access to config values through attributes in addition to keys.
    config_class = Config

    #: The debug flag.  Set this to ``True`` to enable debugging of the
    #: application.  In debug mode the debugger will kick in when an unhandled
    #: exception occurs and the integrated server will automatically reload
    #: the application if changes in the code are detected.
    #:
    #: This attribute can also be configured from the config with the ``DEBUG``
    #: configuration key.  Defaults to ``False``.
    debug = ConfigAttribute('DEBUG')

    #: The name of the logger to use.  By default the logger name is the
    #: package name passed to the constructor.
    logger_name = ConfigAttribute('LOGGER_NAME')

    #: If a secret key is set, cryptographic components can use this to
    #: sign messages and other things.
    secret_key = ConfigAttribute('SECRET_KEY')

    #: Default configuration parameters.
    default_config = {
        'DEBUG':                   False,
        'LOGGER_NAME':             None,
        'LOGGER_HANDLER_POLICY':   'always',
        'SECRET_KEY':              'secret-key',
    }

    def __init__(self, import_name, root_path=None):

        _PackageBoundObject.__init__(self, import_name, root_path=root_path)

        if root_path is None:
            root_path = get_root_path(self.import_name)

        #: Where is the app root located?
        self.root_path = root_path

        self.config = self.make_config()

        self.nodes = list()

        #: Prepare the deferred setup of the logger.
        self._logger = None
        self.logger_name = self.import_name

        self.workflow = _WORKFLOW

    @LockedCachedProperty
    def name(self):
        """The name of the application.  This is usually the import name
        with the difference that it's guessed from the run file if the
        import name is main.  This name is used as a display name when
        Carbon needs the name of the scenario.  It can be set and overridden
        to change the value.
        """
        if self.import_name == '__main__':
            fn = getattr(sys.modules['__main__'], '__file__', None)
            if fn is None:
                return '__main__'
            return os.path.splitext(os.path.basename(fn))[0]
        return self.import_name

    @property
    def logger(self):
        """
        A :class:`logging.Logger` object for this application.  The
        default configuration is to log to stderr if the application is
        in debug mode. This is used to log messages.

        Here some examples::

            app.logger.debug('A value for debugging')
            app.logger.warning('A warning occurred (%d apples)', 42)
            app.logger.error('An error occurred')
        """
        if self._logger and self._logger.name == self.logger_name:
            return self._logger
        with _logger_lock:
            if self._logger and self._logger.name == self.logger_name:
                return self._logger
            from carbon.logging import create_logger
            self._logger = rv = create_logger(self)
            return rv

    def make_config(self):
        """
        Used to create the config attribute by the Carbon constructor.
        """
        root_path = self.root_path
        return self.config_class(root_path, self.default_config)

    def load_from_yaml(self):
        """
        Loads the scenario from a yaml file.
        """
        raise NotImplementedError

    def run(self):
        """
        Run the carbon compound
        """
        raise NotImplementedError
