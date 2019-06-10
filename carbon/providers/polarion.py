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
    carbon.providers.polarion

    Carbon's polarion provider module which contains all the necessary
    classes and functions to process provider validation and requests.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from ..core import ReportProvider
from ..exceptions import CarbonError
from string import Template
from collections import OrderedDict


class PolarionProvider(ReportProvider):
    """Polarion provider class."""
    __provider_name__ = 'polarion'

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
        super(PolarionProvider, self).__init__()

        POLARION_PROPERTIES_SUFFIX = 'polarion-'

        self.opt_params = [
            ('project_id', [str]),
            ('testcase_csv_file', [str]),
            ('testsuite_properties', [OrderedDict, dict]),
            ('testcase_properties', [OrderedDict, dict])

        ]

        self.testsuite_params = [
            (POLARION_PROPERTIES_SUFFIX + 'custom', [str]),
            (POLARION_PROPERTIES_SUFFIX + 'create-defects', [str]),
            (POLARION_PROPERTIES_SUFFIX + 'group-id', [str]),
            (POLARION_PROPERTIES_SUFFIX + 'include-skipped', [str]),
            (POLARION_PROPERTIES_SUFFIX + 'lookup-method', [str]),
            (POLARION_PROPERTIES_SUFFIX + 'project-span-ids', [str]),
            (POLARION_PROPERTIES_SUFFIX + 'response', [str]),
            (POLARION_PROPERTIES_SUFFIX + 'testrun-id', [str]),
            (POLARION_PROPERTIES_SUFFIX + 'testrun-status-id', [str]),
            (POLARION_PROPERTIES_SUFFIX + 'testrun-template-id', [str]),
            (POLARION_PROPERTIES_SUFFIX + 'testrun-title', [str]),
            (POLARION_PROPERTIES_SUFFIX + 'testrun-type-id', [str]),

        ]

        self.testcase_params = [
            (POLARION_PROPERTIES_SUFFIX + 'testcase-id', [str]),
            (POLARION_PROPERTIES_SUFFIX + 'testcase-lookup-method', [str]),
            (POLARION_PROPERTIES_SUFFIX + 'testcase-comment', [str]),
            (POLARION_PROPERTIES_SUFFIX + 'testcase-project-id', [str]),
            (POLARION_PROPERTIES_SUFFIX + 'parameter', [str]),
        ]

        self.testcase_name = ('test_classname', [str])

        self.req_credential_params = [
            ('polarion_url', [str]),
            ('username', [str]),
            ('password', [str])
        ]

    def validate_opt_params(self, report):
        """Validate the optional parameters exists in the report resource.

        :param host: report resource
        :type host: object
        """
        for item in self.opt_params:
            name = getattr(report, 'name')
            param, param_type = item[0], item[1]
            msg = "Resource %s : optional param '%s' " % (name, param)
            try:
                param_value = getattr(report, 'provider_params')[param]
                self.logger.info(msg + 'exists.')

                if not type(param_value) in param_type:
                    self.logger.error(
                        '    - Type=%s, Optional Type=%s. (ERROR)' %
                        (type(param_value), param_type))
                    raise CarbonError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % getattr(report, 'name')
                    )
                if param == 'testsuite_properties' and param_value:
                    self.validate_testsuite_params(param_value, name)

                if param == 'testcase_properties' and param_value:
                    self.validate_testcase_params(param_value, name)
            except KeyError:
                self.logger.warning(msg + 'is undefined for resource.')

    def validate_testsuite_params(self, params, resource_name):
        """validate the testsuite params exist in the report resource
        :param params: testsuite properties
        :type dict: dictionary"""

        msg = Template("Resource $name : optional param '$param' $ending")
        total_params = len(params)
        checks = 0
        param = ''
        for item in self.testsuite_params:
            ts_param, ts_param_type = item[0], item[1]
            if 'custom' in ts_param:
                continue
            for k, v in params.items():
                if ts_param == k:
                    param = ts_param
                elif ts_param == k[:16] and 'response' in k:
                    param = k
                else:
                    checks += 1
                    continue

                self.logger.info(msg.substitute(name=resource_name, param=param, ending='exists.'))

                if not type(v) in ts_param_type:
                    self.logger.error(
                        '    - Type=%s, Optional Type=%s. (ERROR)' %
                        (type(v), ts_param_type))
                    raise CarbonError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % resource_name
                    )
                checks = 0
                break

            if checks == total_params:
                self.logger.warning(
                    msg.substitute(name=resource_name, param=ts_param, ending='is undefined for resource.'))
                checks = 0

        # perform same check but this time only focus on custom tags
        for item in self.testsuite_params:
            ts_param, ts_param_type = item[0], item[1]
            if 'custom' not in ts_param:
                continue
            for k, v in params.items():
                if ts_param == k[:15] and 'custom' in k:
                    param = k
                else:
                    checks += 1
                    continue

                self.logger.info(msg.substitute(name=resource_name, param=param, ending='exists.'))

                if not type(v) in ts_param_type:
                    self.logger.error(
                        '    - Type=%s, Optional Type=%s. (ERROR)' %
                        (type(v), ts_param_type))
                    raise CarbonError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % resource_name
                    )
                checks = 0
                continue

            if checks == total_params:
                self.logger.warning(
                    msg.substitute(name=resource_name, param=ts_param, ending='is undefined for resource.'))
                checks = 0

    def validate_testcase_params(self, params, resource_name):
        """validate the testcase params exist in the report resource
        :param params: testcase properties
        :type dict: dictionary"""

        msg = Template("Resource $name : optional param '$param' $ending")
        param = ''

        for k, v in params.items():
            if k:
                self.logger.info(msg.substitute(name=resource_name, param=k, ending='exists.'))
            if type(k) is not str:
                self.logger.error(
                    '    - Type=%s, Optional Type=%s. (ERROR)' %
                    (type(v), str))
                raise CarbonError(
                    'Error occurred while validating required provider '
                    'parameters for resource %s' % resource_name
                )
            if v:
                if type(v) is not dict:
                    self.logger.error(
                        '    - Type=%s, Optional Type=%s. (ERROR)' %
                        (type(v), dict))
                    raise CarbonError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % resource_name
                    )
                checks = 0
                for item in self.testcase_params:
                    tc_param, tc_param_type = item[0], item[1]
                    for z, y in v.items():
                        if z == tc_param:
                            param = tc_param
                        elif z[:18] == tc_param and 'parameter' in z:
                            param = z
                        else:
                            checks += 1
                            continue

                        self.logger.info(msg.substitute(name=resource_name, param=param, ending='exists.'))

                        if not type(y) in tc_param_type:
                            self.logger.error(
                                '    - Type=%s, Optional Type=%s. (ERROR)' %
                                (type(v), tc_param_type))
                            raise CarbonError(
                                'Error occurred while validating required provider '
                                'parameters for resource %s' % resource_name
                            )
                        checks = 0
                        break

                    if checks == len(v):
                        self.logger.warning(
                            msg.substitute(name=resource_name, param=tc_param, ending='is undefined for resource.'))
                        checks = 0
