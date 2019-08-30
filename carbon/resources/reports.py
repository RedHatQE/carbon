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
    carbon.resources.actions

    Module used for building carbon report compounds. A report's main goal is
    to handle reporting results to external resources.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import sys
import re
import fnmatch
import glob
from os import path
from collections import OrderedDict

from ..core import CarbonResource
from ..tasks import ReportTask, ValidateTask
from ..exceptions import CarbonReportError
from ..helpers import get_importer_plugin_class, get_default_importer, get_default_importer_plugin, \
    get_importers_plugins_list, get_providers_list, get_provider_class
from .._compat import string_types


class Report(CarbonResource):
    """
    The report resource class.
    """

    _valid_tasks_types = ['validate', 'report']
    _fields = ['name', 'description', 'importer', 'execute_name', 'import_results']

    def __init__(self,
                 config=None,
                 name=None,
                 importer=None,
                 parameters={},
                 validate_task_cls=ValidateTask,
                 report_task_cls=ReportTask,
                 **kwargs):
        """Constructor.

        :param config: carbon configuration
        :type config: dict
        :param name: report resource name
        :type name: str
        :param parameters: content which makes up the report resource
        :type parameters: dict
        :param validate_task_cls: carbons validate task class
        :type validate_task_cls: object
        :param report_task_cls: carbons report task class
        :type report_task_cls: object
        :param kwargs: additional key:value(s)
        :type kwargs: dict
        """
        super(Report, self).__init__(config=config, name=name, **kwargs)

        # set the report resource name
        if name is None:
            self._name = parameters.pop('name', None)
            if self._name is None:
                raise CarbonReportError('Unable to build report object. Name'
                                        ' field missing!')
        else:
            self._name = name

        # set the report description
        self._description = parameters.pop('description', None)

        # set the execute that collected the artifacts
        self._executes = parameters.pop('executes')
        if self.executes is None:
            raise CarbonReportError('Unable to associate executes to report artifact:'
                                     '%s. No executes defined!' % self._name)

        # convert the executes into list format if executes defined as str format
        if isinstance(self.executes, string_types):
            self.executes = self.executes.replace(' ', '').split(',')

        # report needs to be imported, get the provider parameters
        parameters = self.__set_provider_attr__(parameters)

        # finally lets get the right importer to use
        importer_name = parameters.pop('importer', importer)
        self._importer = get_default_importer()
        if importer_name is None:
            self._importer_plugin = get_default_importer_plugin(self._provider)
        else:
            found_name = False
            for name in get_importers_plugins_list():
                if name.startswith(importer_name):
                    found_name = True

            if found_name:
                self._importer_plugin = get_importer_plugin_class(importer_name)
            else:
                self.logger.error('Importer %s for report artifacts %s is invalid.'
                                  % (importer_name, self.name))
                sys.exit(1)

        self._import_results = parameters.pop('import_results', [])

        # set the carbon task classes for the resource
        self._validate_task_cls = validate_task_cls
        self._report_task_cls = report_task_cls

        # reload construct task methods
        self.reload_tasks()

        # load the parameters into the object itself
        if parameters:
            self.load(parameters)

    def __set_provider_attr__(self, parameters):
        """Configure the report provider attributes.

        :param parameters: content which makes up the report resource
        :type parameters: dict
        :return: updated parameters
        :rtype: dict"""

        try:
            self.provider_params = parameters.pop('provider')
        except KeyError:
            self.logger.error('Provider parameter is required for reports being'
                              ' imported.')
            sys.exit(1)

        provider_name = self.provider_params['name']

        # lets verify the provider is valid
        if provider_name not in get_providers_list():
            self.logger.error('Provider %s for report artifacts %s is invalid.' %
                              (provider_name, self.name))
            sys.exit(1)

        # now that we have the provider, lets create the provider object
        self._provider = get_provider_class(provider_name)()

        # finally lets set the provider credentials
        try:
            self._credential = self.provider_params['credential']
            self.logger.debug(self._credential)
            provider_credentials = self.config['CREDENTIALS']
        except KeyError:
            self.logger.error('A credential must be set for the provider %s.'
                              % provider_name)
            sys.exit(1)

        try:
            for item in provider_credentials:
                if item['name'] == self._credential:
                    getattr(self.provider, 'set_credentials')(item)
                    break
        except KeyError:
            self.logger.error('The required credential parameters are not set correctly for the provider %s. Please '
                              'verify the carbon config file' % provider_name)
            sys.exit(1)

        return parameters

    def validate(self):
        """
        Only validating provider attributes
        """

        # validate provider properties
        self.logger.info('Validating report %s provider required parameters.' %
                         self.name)
        getattr(self.provider, 'validate_req_params')(self)

        self.logger.info('Validating report %s provider optional parameters.' %
                         self.name)
        getattr(self.provider, 'validate_opt_params')(self)

        self.logger.info('Validating report %s provider required credential '
                         'parameters.' % self.name)
        getattr(self.provider, 'validate_req_credential_params')(self)

        self.logger.info('Validating report %s provider optional credential '
                         'parameters.' % self.name)
        getattr(self.provider, 'validate_opt_credential_params')(self)

    @property
    def importer(self):
        """Importer property.

        :return: importer class
        :rtype: object
        """
        return self._importer

    @importer.setter
    def importer(self, value):
        """Set importer property."""
        raise AttributeError('You cannot set the report importer after report '
                             'class is instantiated.')

    @property
    def importer_plugin(self):
        """Importer plugin property.

        :return: importer plugin class
        :rtype: object
        """
        return self._importer_plugin

    @importer_plugin.setter
    def importer_plugin(self, value):
        """Set importer plugin property."""
        raise AttributeError('You cannot set the report importer plugin after report '
                             'class is instantiated.')

    @property
    def provider(self):
        """Provider property.

        :return: provider class
        :rtype: object
        """
        return self._provider

    @provider.setter
    def provider(self, value):
        """Set provider property."""
        raise AttributeError('You cannot set the report provider after report '
                             'class is instantiated.')

    @property
    def executes(self):
        """Execute resource property.

        :return: execute class
        :rtype: object
        """
        return self._executes

    @executes.setter
    def executes(self, value):
        """Set execute object property."""
        self._executes = value

    @property
    def import_results(self):
        """import_results resource property.

        :return: import results
        :rtype: list
        """
        return self._import_results

    @import_results.setter
    def import_results(self, value):
        """Set the import_results property."""
        self._import_results = value

    def profile(self):
        """Builds a profile for the report resource.

        :return: the report profile
        :rtype: OrderedDict
        """
        profile = OrderedDict()
        profile['name'] = self.name
        profile['description'] = self.description
        profile['importer'] = getattr(
                       self.importer_plugin, '__plugin_name__')
        profile['provider'] = self.provider_params

        # set the report's executes
        if all(isinstance(item, string_types) for item in self.executes):
            profile.update(executes=[execute for execute in self.executes])
        else:
            profile.update(dict(executes=[execute.name for execute in self.executes]))

        # set the report's import results
        profile.update({'import_results': self.import_results})

        return profile

    def _construct_validate_task(self):
        """Constructs the validate task associated to the report resource.

        :return: validate task definition
        :rtype: dict
        """
        task = {
            'task': self._validate_task_cls,
            'name': str(self.name),
            'resource': self,
            'methods': self._req_tasks_methods
        }
        return task

    def _construct_report_task(self):
        """Constructs the report task associated to the report resource.

        :return: report task definition
        :rtype: dict
        """
        task = {
            'task': self._report_task_cls,
            'name': str(self.name),
            'package': self,
            'msg': '   reporting %s' % self.name,
            'methods': self._req_tasks_methods
        }
        return task
