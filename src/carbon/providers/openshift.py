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
    )

    _optional_parameters = (
        'image',
        'git',
        'template_name',
        'env_vars',
        'labels'
    )

    _mandatory_creds_parameters = (
        'auth_url',
        'project',
        'username',
        'token'
    )

    def __init__(self, **kwargs):
        super(OpenshiftProvider, self).__init__(**kwargs)
