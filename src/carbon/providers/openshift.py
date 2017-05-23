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
from ..core import CarbonProvider
from .._compat import string_types
from ..helpers import check_is_gitrepo_fine


class OpenshiftProvider(CarbonProvider):
    """
    Openshift provider implementation.
    The following fields are supported:

        oc_name: (manadatory) The resource name.

        oc_image: (optional) The docker image used to create an application.

        oc_git: (optional) The git url (source code) used to create an
                application.

        oc_template_name: (optional) The template name used to create an
                          application.

        oc_env_vars: (optional) A dict of environment variables that are
                     needed by the components created when creating a new
                     application.

        oc_labels: (optional) A dict of labels to be associated with an
                   application. The labels will be associated with all
                   components of the application.

        To add more fields for the provider, you have to also create a
        validate_* function for the field. The signature for the function
        must be validate_<paramenter_name> and the return must be True for
        valid or False if the validation fails.

        For instance, the field 'image' has the function 'validate_image'.

    """
    __provider_name__ = 'openshift'
    __provider_prefix__ = 'oc_'

    _mandatory_parameters = (
        'name',
        'labels'
    )

    _optional_parameters = (
        'image',
        'git',
        'template',
        'env_vars',
    )

    _mandatory_creds_parameters = (
        'auth_url',
        'project',
        'username',
        'token'
    )

    def __init__(self, **kwargs):
        super(OpenshiftProvider, self).__init__(**kwargs)

    @classmethod
    def validate_name(cls, value):
        """Validate the resource name.
        :param value: The resource name
        :return: A boolean, true = valid, false = invalid
        """
        print("Validating Name: {}".format(value))
        # Quit when no value given
        if not value:
            print('Invalid data for name!')
            return False

        # Name must be a string
        if not isinstance(value, string_types):
            print("Name is required to be a string type!")
            return False

        return True

    @classmethod
    def validate_image(cls, value):
        """Validate the image, if set.
        :param value: The resource image name
        :return: A boolean, true = valid, false = invalid
        """
        if value:
            print("Validating image: {}".format(value))
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_git(cls, value):
        """Validate the git, if set.
        :param value: The resource git name
        :return: A boolean, true = valid, false = invalid
        """
        if value:
            print("Validating git: {}".format(value))
            if isinstance(value, string_types):
                return check_is_gitrepo_fine(value)
            else:
                return False
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_template(cls, value):
        """Validate the template, if set.
        :param value: The resource template name
        :return: A boolean, true = valid, false = invalid
        """
        if value:
            #             print("Validating template name: {}".format(value))
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_env_vars(cls, value):
        """Validate the environment variables.
        :param value: The environment variables
        :return: A boolean, true = valid, false = invalid
        """
        if value:
            #             print("Validating env vars: {}".format(value))
            return isinstance(value, dict)
        else:
            return True

    @classmethod
    def validate_labels(cls, value):
        """Validate the labels, list of single dictionaries.
        :param value: The label list
        :return: A boolean, true = valid, false = invalid
        """
        if value:
            #             print("Validating labels: {}".format(value))
            if isinstance(value, list):
                for val in value:
                    if isinstance(val, dict):
                        k, v = val.items()[0]
                        # check valid values and the list only has one item
                        if k and v and len(val.items()) == 1:
                            pass
                        else:
                            return False
                    else:
                        return False
                return True
            else:
                return False
        else:
            return True
