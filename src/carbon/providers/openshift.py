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
    carbon.providers.openshift

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from .._compat import string_types
from ..core import CarbonProvider
from ..helpers import is_url_valid


class OpenshiftProvider(CarbonProvider):
    """
    Openshift provider implementation.
    The following fields are supported:

        oc_name: (manadatory) The resource name.

        oc_image: (optional) The docker image used to create an application.

        oc_git: (optional) The git url (source code) used to create an
                application.

        oc_template: (optional) The template name used to create an
                          application.

        oc_custom_template (optional) A template file that will be used to
                                      create the application.

        oc_env_vars: (optional) A dict of environment variables that are
                     needed by the components created when creating a new
                     application.

        oc_labels: (optional) A dict of labels to be associated with an
                   application. The labels will be associated with all
                   components of the application.

        oc_build_timeout: (optional) The duration to wait for a pod to be
                          up and running.

        To add more fields for the provider, you have to also create a
        validate_* function for the field. The signature for the function
        must be validate_<paramenter_name> and the return must be True for
        valid or False if the validation fails.

        For instance, the field 'image' has the function 'validate_image'.

        The following fields are returned for provisioned applications:

            oc_app_name: The application name for the provisioned application.

            oc_routes: The routes for the application provisioned.
    """
    __provider_name__ = 'openshift'
    __provider_prefix__ = 'oc_'

    _mandatory_parameters = (
        'name',
        'labels',
    )

    _optional_parameters = (
        'image',
        'git',
        'template',
        'env_vars',
        'build_timeout',
        'app_name',
        'routes',
        'custom_template',
    )

    _output_parameters = (
        'app_name',
        'routes',
    )

    _mandatory_creds_parameters = (
        'auth_url',
        'project',
    )

    _optional_creds_parameters = (
        'token',
        'username',
        'password',
    )

    _assets_parameters = (
        'custom_template',
    )

    def __init__(self, **kwargs):
        super(OpenshiftProvider, self).__init__(**kwargs)

    def validate_name(self, value):
        """Validate the resource name.
        :param value: The resource name
        :return: A boolean, true = valid, false = invalid
        """
        self.logger.debug("Validating Name: {0}".format(value))
        # Quit when no value given
        if not value:
            self.logger.warn('Invalid data for name!')
            return False

        # Name must be a string
        if not isinstance(value, string_types):
            self.logger.warn("Name is required to be a string type!")
            return False

        return True

    def validate_image(self, value):
        """Validate the image, if set.
        :param value: The resource image name
        :return: A boolean, true = valid, false = invalid
        """
        if value:
            self.logger.debug("Validating image: {0}".format(value))
            return isinstance(value, string_types)
        else:
            return True

    def validate_git(self, value):
        """Validate the git, if set.
        :param value: The resource git name
        :return: A boolean, true = valid, false = invalid
        """
        if value:
            self.logger.debug("Validating git: {0}".format(value))
            if isinstance(value, string_types):
                return is_url_valid(value)
            else:
                return False
        else:
            return True

    def validate_template(self, value):
        """Validate the template, if set.
        :param value: The resource template name
        :return: A boolean, true = valid, false = invalid
        """
        if value:
            self.logger.debug("Validating template name: {0}".format(value))
            return isinstance(value, string_types)
        else:
            return True

    def validate_custom_template(self, value):
        """Validate the custom template, if set.
        :param value: The resource template name
        :return: A boolean, true = valid, false = invalid
        """
        if value:
            self.logger.debug("Validating template name: {0}".format(value))
            return isinstance(value, string_types)
        else:
            return True

    def validate_env_vars(self, value):
        """Validate the environment variables.
        :param value: The environment variables
        :return: A boolean, true = valid, false = invalid
        """
        if value:
            self.logger.debug("Validating env vars: {0}".format(value))
            return isinstance(value, dict)
        else:
            return True

    def validate_build_timeout(self, value):
        """Validate the build timeout, how long to wait for the build to complete.
        :param value: A timeout value if specified
        :return: A boolean, true = valid, false = invalid
        """
        if value:
            self.logger.debug("Validating env vars: {0}".format(value))
            if isinstance(value, int) and value > 0:
                return True
            else:
                return False
        else:
            return True

    def validate_labels(self, value):
        """Validate the labels, list of single dictionaries.
        :param value: The label list
        :return: A boolean, true = valid, false = invalid
        """
        if value:
            self.logger.debug("Validating labels: {0}".format(value))

            # Labels must be a list data type
            if not isinstance(value, list):
                return False

            for val in value:
                # Elements in labels list must be a dict data type
                if not isinstance(val, dict):
                    return False

                # Dict cannot have more than one key:value declared
                if len(list(val)) != 1:
                    return False

                # Check key:value is valid
                for k, v in val.items():
                    if not k or not v:
                        return False
            return True
        else:
            return True

    @classmethod
    def validate_routes(cls, value):
        return True

    @classmethod
    def validate_custom_templates(cls, value):
        return True

    @classmethod
    def validate_app_name(cls, value):
        return True
