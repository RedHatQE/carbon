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
    carbon.utils.config

    Carbons own config module for loading configuration settings defined by
    the user.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import os

from .._compat import RawConfigParser
from ..constants import DEFAULT_CONFIG, DEFAULT_CONFIG_SECTIONS, DEFAULT_TASK_CONCURRENCY


class Config(dict):
    """The config class.

    Its desired state is for loading the configuration settings supplied by
    the user. The config object is based on pythons dictionary data structure.
    """
    def __init__(self):
        """Constructor."""
        super(Config, self).__init__(DEFAULT_CONFIG)
        self.__set_parser__()

    def __set_parser__(self):
        """Set the raw config parser."""
        self.parser = RawConfigParser()

    def __del_parser__(self):
        """Delete the raw config parser."""
        del self.parser

    def __set_defaults__(self):
        """Set the default configuration settings."""
        for k, v in getattr(self.parser, '_sections')['defaults'].items():
            if k == '__name__':
                continue
            self.__setitem__(k.upper(), v)

    def __set_credentials__(self):
        """Set the credentials configuration settings."""
        credentials = []

        for section in getattr(self.parser, '_sections'):
            if not section.startswith('credentials'):
                continue

            _credentials = {}

            for option in self.parser.options(section):
                _credentials[option] = \
                    self.parser.get(section, option)
            _credentials['name'] = section.split(':')[-1]
            credentials.append(_credentials)

        self.__setitem__('CREDENTIALS', credentials)

    def __set_orchestrator__(self):
        """Set the orchestrator configuration settings."""
        for section in getattr(self.parser, '_sections'):
            if not section.startswith('orchestrator'):
                continue

            orchestrator = section.split(':')[-1]

            for option in self.parser.options(section):
                self.__setitem__(
                    (orchestrator + '_' + option).upper(),
                    self.parser.get(section, option)
                )

    def __set_executor__(self):
        """Set the executor configuration settings."""
        for section in getattr(self.parser, '_sections'):
            if not section.startswith('executor'):
                continue

            executor = section.split(':')[-1]

            for option in self.parser.options(section):
                self.__setitem__(
                    (executor + '_' + option).upper(),
                    self.parser.get(section, option)
                )

    def __set_importer__(self):
        """Set the importer configuration settings."""
        for section in getattr(self.parser, '_sections'):
            if not section.startswith('importer'):
                continue

            importer = section.split(':')[-1]

            for option in self.parser.options(section):
                self.__setitem__(
                    (importer + '_' + option).upper(),
                    self.parser.get(section, option)
                )

    def __set_feature_toggles__(self):
        """Set the feature toggle configuration settings."""
        toggles = []

        for section in getattr(self.parser, '_sections'):
            if not section.startswith('feature_toggles'):
                continue

            _toggles = {}

            for option in self.parser.options(section):
                _toggles[option] = \
                    self.parser.get(section, option)
                _toggles['name'] = section.split(':')[-1]
                toggles.append(_toggles)

        self.__setitem__('TOGGLES', toggles)

    def __set_task_concurrency__(self):
        """Set the task if it should be executed concurrently."""

        _concurrency_settings = DEFAULT_TASK_CONCURRENCY

        for section in getattr(self.parser, '_sections'):
            if not section.startswith('task_concurrency'):
                continue

            for option in self.parser.options(section):
                _concurrency_settings.update({option.upper(): self.parser.get(section, option)})

        self.__setitem__('TASK_CONCURRENCY', _concurrency_settings)

    def __set_setup_logger__(self):
        """
        Set new loggers that carbon should configure logging. This
        is so those libraries/utils log their logger output to
        carbon's console and filehandler using carbon's formatter.
        """
        _logging_settings = []

        for section in getattr(self.parser, '_sections'):
            if not section.startswith('setup_logger'):
                continue

            for option in self.parser.options(section):
                _logging_settings.append(self.parser.get(section, option))

        self.__setitem__('SETUP_LOGGER', _logging_settings)

    def __set_notifications__(self):
        """Set the notification configuration settings."""
        notifications = []

        for section in getattr(self.parser, '_sections'):
            if not section.startswith('notifier'):
                continue

            _notifications = {}

            for option in self.parser.options(section):
                _notifications[option] = \
                    self.parser.get(section, option)
            _notifications['name'] = section.split(':')[-1]
            notifications.append(_notifications)

        self.__setitem__('NOTIFICATIONS', notifications)

    def __set_provisioner__(self):
        """Set the provisioner configuration settings."""
        provisioner_options = []

        for section in getattr(self.parser, '_sections'):
            if not section.startswith('provisioner'):
                continue

            _provisioner_options = {}

            for option in self.parser.options(section):
                _provisioner_options[option] = \
                    self.parser.get(section, option)
            _provisioner_options['name'] = section.split(':')[-1]
            provisioner_options.append(_provisioner_options)

        self.__setitem__('PROVISIONER_OPTIONS', provisioner_options)

    def load(self):
        """Load configuration settings.

        Configuration will be loaded from the following order:
            - /etc/carbon/carbon.cfg
            - ./carbon.cfg
            - CARBON_SETTINGS env variable setting the config file
        """
        files = [
            '/etc/carbon/carbon.cfg',
            os.path.join(os.getcwd(), 'carbon.cfg')
        ]

        if os.getenv('CARBON_SETTINGS'):
            files.append(os.getenv('CARBON_SETTINGS'))

        for filename in files:
            if not os.path.exists(filename):
                # file not found
                continue

            # read the file
            self.parser.read(filename)

            # set user supplied configuration settings overriding defaults
            for config in DEFAULT_CONFIG_SECTIONS:
                getattr(self, '__set_%s__' % config)()
