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
    carbon.providers.report_portal

    Carbon's report_portal provider module which contains all the necessary
    classes and functions to process provider validation and requests for the report portal client.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..core import ReportProvider
from ..exceptions import CarbonProviderError


class ReportPortalProvider(ReportProvider):
    """ReportPortal provider class."""
    __provider_name__ = 'reportportal'

    def __init__(self):
        """Constructor.

        Sets the following attributes:
            - required provider parameters
            - optional provider parameters
            - required provider credential parameters
            - optional provider credential parameters

        Each attribute is a list of tuples. Within the tuple index 0 is the
        parameter name and the index 1 is the data type for the parameter.
        """
        super(ReportPortalProvider, self).__init__()
        self._req_params = [

            ('json_path', [str]),
            ('rp_project', [str]),
            ('launch_name', [str])

        ]
        self._opt_params = [
            ('tags', [list]),
            ('service', [bool]),
            ('merge_launches', [bool]),
            ('simple_xml', [bool]),
            ('launch_description', [str]),
            ('auto_dashboard', [bool])

        ]
        self._opt_credential_params = [
            ('rp_url', [str]),
            ('api_token', [str]),
            ('service_url', [str])
        ]

        self.req_credential_params = [
            ('create_creds', [str])
        ]

    @property
    def name(self):
        """Return the provider name."""
        return self.__provider_name__

    @name.setter
    def name(self, value):
        """Raises an exception when trying to set the name for the provider
        :param value: name
        """
        raise AttributeError('You cannot set provider name.')

    def validate_opt_credential_params(self, report):
        """Validate the optional credential parameters exists in the report resource.

        :param report: report resource
        :type report: object
        """
        name = getattr(report, 'name')
        provider = getattr(report, 'provider')
        req_cred = self.req_credential_params[0]
        if req_cred[0] == 'create_creds' and getattr(provider, 'credentials')['create_creds'] == 'True':
            for item in self.opt_credential_params:
                param, param_type = item[0], item[1]
                msg = "Resource %s : optional credential param '%s' " % (name, param)
                try:
                    param_value = getattr(provider, 'credentials')[param]
                    if param_value:
                        self.logger.info(msg + 'exists.')
                    else:
                        raise CarbonProviderError(
                            'Error occurred while validating required provider '
                            'parameter %s for resource %s' % (param, getattr(report, 'name'))
                        )
                    if not type(param_value) in param_type:
                        self.logger.error(
                            '    - Type=%s, Optional Type=%s. (ERROR)' %
                            (type(param_value), param_type)
                        )
                        raise CarbonProviderError(
                            'Error occurred while validating required provider '
                            'parameter %s for resources %s' % (param, getattr(report, 'name'))
                        )
                except (AttributeError, KeyError):
                    self.logger.warning(msg + 'does not exist.')
        else:
            self.logger.info("create_creds parameter is set to False. "
                             "Optional credential parameters will not be validated")

    def validate_req_params(self, report):
        """Validate the required parameters exists in the report resource.

        :param report: report resource
        :type report: object
        """
        for item in self.req_params:
            name = getattr(report, 'name')
            param, param_type = item[0], item[1]
            msg = "Resource %s : required param '%s' " % (name, param)
            if param == 'json_path':
                try:
                    param_value = getattr(report, 'provider_params')[param]
                    self.logger.info(msg + 'exists.')

                    if not type(param_value) in param_type:
                        self.logger.error(
                            '    - Type=%s, Required Type=%s. (ERROR)' %
                            (type(param_value), param_type))
                        raise CarbonProviderError(
                            'Error occurred while validating required provider '
                            'parameter %s for resource %s' % (param, getattr(report, 'name'))
                        )
                    self.logger.info('Parameter json_path is provided and will be used as report portal config file.'
                                     ' Other required parameters will be ignored')
                    break
                except KeyError:
                    msg = msg + 'does not exist.'
                    self.logger.info(msg)
                    continue
            else:
                try:
                    param_value = getattr(report, 'provider_params')[param]
                    self.logger.info(msg + 'exists.')

                    if not type(param_value) in param_type:
                        self.logger.error(
                            '    - Type=%s, Required Type=%s. (ERROR)' %
                            (type(param_value), param_type))
                        raise CarbonProviderError(
                            'Error occurred while validating required provider '
                            'parameter %s for resource %s' % (param, getattr(report, 'name'))
                        )
                except KeyError:
                    msg = msg + 'does not exist.'
                    self.logger.error(msg)
                    raise CarbonProviderError(msg)

    def validate_opt_params(self, report):
        """Validate the optional parameters exists in the report resource.

        :param report: report resource
        :type report: object
        """

        if 'json_path' not in getattr(report, 'provider_params').keys():
            for item in self.opt_params:
                name = getattr(report, 'name')
                param, param_type = item[0], item[1]
                msg = "Resource %s : optional param '%s' " % (name, param)
                try:
                    param_value = getattr(report, 'provider_params')[param]
                    self.logger.info(msg + 'exists.')

                    if not type(param_value) in param_type:
                        self.logger.error('    - Type=%s, Optional Type=%s. (ERROR)' %
                                          (type(param_value), param_type))
                        raise CarbonProviderError(
                            'Error occurred while validating required provider '
                            'parameter %s  for resource %s' % (param, getattr(report, 'name'))
                        )
                except KeyError:
                    self.logger.warning(msg + 'is undefined for resource.')
        else:
            self.logger.info('Parameter json_path is provided and will be used as report portal config file.'
                             ' Other optional parameters will be ignored')
