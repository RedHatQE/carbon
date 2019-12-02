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
    carbon.resources.host

    Module used for building carbon host compounds. Hosts are the base to a
    scenario object. The remaining compounds that make up a scenario are
    processed against the hosts defined.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import sys

from ..core import CarbonResource
from ..helpers import get_provider_plugin_class, get_provider_plugin_list, gen_random_str
from ..helpers import filter_host_name
from ..helpers import get_provisioners_plugins_list, get_provisioner_plugin_class, get_default_provisioner_plugin, \
    is_provider_mapped_to_provisioner
from ..tasks import ProvisionTask, CleanupTask, ValidateTask
from .._compat import string_types
from collections import OrderedDict


class Asset(CarbonResource):
    """
    The asset resource class. The carbon compound can contain x amount of hosts or
    other asset types (i.e. virtual networks, storage, etc.).
    Their primary responsibility is to define details about the system resource
    to be created in their declared provider. Along with saving information
    such as (ip addresses, etc) for use by the action or execute compounds of
    carbon.
    """

    _valid_tasks_types = ['validate', 'provision', 'cleanup']
    _fields = [
        'name',
        'description',
        'ip_address',
        'metadata',
        'ansible_params'
    ]

    def __init__(self,
                 config=None,
                 name=None,
                 provisioner=None,
                 parameters={},
                 validate_task_cls=ValidateTask,
                 provision_task_cls=ProvisionTask,
                 cleanup_task_cls=CleanupTask,
                 **kwargs):
        """Constructor.

        :param config: carbon configuration
        :type config: dict
        :param name: host resource name
        :type name: str
        :param provisioner: provisioner name used to create the host in the
            defined provider
        :type provisioner: str
        :param parameters: content which makes up the host resource
        :type parameters: dict
        :param validate_task_cls: carbons validate task class
        :type validate_task_cls: object
        :param provision_task_cls: carbons provision task class
        :type provision_task_cls: object
        :param cleanup_task_cls: carbons cleanup task class
        :type cleanup_task_cls: object
        :param kwargs: additional key:value(s)
        :type kwargs: dict
        """
        super(Asset, self).__init__(config=config, name=name, **kwargs)

        # set name attribute & apply filter
        if name is None:
            self._name = parameters.pop('name', None)
            if self._name is None:
                self._name = 'hst{0}'.format(gen_random_str(10))
        else:
            self._name = name

        # set description attribute
        self._description = parameters.pop('description', None)

        # preset role/groups attribute
        self._role = None
        self._groups = None
        try:
            # convert the groups into list format if groups defined as str format
            self._groups = parameters.pop('groups')
            if isinstance(self._groups, string_types):
                self._groups = self._groups.replace(' ', '').split(',')
            del self.role
        except KeyError:
            try:
                # convert the roles into list format if roles defined as str format
                self._role = parameters.pop('role')
                if isinstance(self._role, string_types):
                    self._role = self._role.replace(' ', '').split(',')
                self.logger.warning('A role has been found. This parameter will be deprecated'
                                    ' it is recommend to change over to groups.')
                del self.groups
            except KeyError:
                self.logger.warning('A group or a role was not set for asset %s.' % self.name)
                del self.role, self.groups

        # set metadata attribute (data pass-through)
        self._metadata = parameters.pop('metadata', {})

        # set ansible parameters
        self._ansible_params = parameters.pop('ansible_params', {})

        # determine if the host is a static machine already provisioned
        # how? if the ip_address param is defined and provider is not defined
        # then we can be safe to say the machine is static
        if 'ip_address' in parameters and 'provider' not in parameters:
            self._ip_address = parameters.pop('ip_address')
            # set flag to control whether the host is static or not
            self.is_static = True
        else:
            # set flag to control whether the host is static or not
            self.is_static = False
            # host needs to be provisioned, get the provider parameters
            parameters = self.__set_provider_attr_(parameters)

            # lets setup any feature toggles that we defined in the configuration file
            self.__set_feature_toggles_()

            # finally lets get the right provisioner to use
            provisioner_name = parameters.pop('provisioner', provisioner)

            # TODO: Should we instantiate here rather just getting the classes
            if provisioner_name is None:
                self._provisioner_plugin = get_default_provisioner_plugin(self._provider)
            else:
                found_name = False
                for name in get_provisioners_plugins_list():
                    if name.startswith(provisioner_name):
                        found_name = True
                        break

                if found_name and is_provider_mapped_to_provisioner(self._provider, provisioner_name):
                    self._provisioner_plugin = get_provisioner_plugin_class(provisioner_name)
                else:
                    self.logger.error('Provisioner %s for asset %s is invalid.'
                                      % (provisioner_name, self.name))
                    sys.exit(1)

            self._ip_address = parameters.pop('ip_address', None)

        # set the carbon task classes for the resource
        self._validate_task_cls = validate_task_cls
        self._provision_task_cls = provision_task_cls
        self._cleanup_task_cls = cleanup_task_cls

        # reload construct task methods
        self.reload_tasks()

        # load the parameters set into the object itself
        if parameters:
            self.load(parameters)

    def __set_feature_toggles_(self):

        self._feature_toggles = None

        for item in self.config['TOGGLES']:
            if item['name'] == 'host':
                self._feature_toggles = item

    def __set_provider_attr_(self, parameters):
        """Configure the host provider attributes.

        :param parameters: content which makes up the host resource
        :type parameters: dict
        :return: updated parameters
        :rtype: dict
        """
        try:
            self.provider_params = parameters.pop('provider')
        except KeyError:
            self.logger.error('Provider parameter is required for assets being'
                              ' provisioned.')
            sys.exit(1)

        provider_name = self.provider_params['name']

        # lets verify the provider is valid
        if provider_name not in get_provider_plugin_list():
            self.logger.error('Provider %s for host %s is invalid.' %
                              (provider_name, self.name))
            sys.exit(1)

        # now that we have the provider, lets create the provider object
        self._provider = get_provider_plugin_class(provider_name)()

        # finally lets set the provider credentials
        try:
            self._credential = self.provider_params['credential']
            provider_credentials = self.config['CREDENTIALS']
        except KeyError:
            self.logger.error('A credential must be set for the provider %s.'
                              % provider_name)
            sys.exit(1)

        for item in provider_credentials:
            if item['name'] == self._credential:
                getattr(self.provider, 'set_credentials')(item)
                break

        # determine hostname for the host
        if 'hostname' not in self.provider_params:
            self.provider_params['hostname'] = \
                filter_host_name(self.name) + '_%s' % gen_random_str(5)

        return parameters

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        raise AttributeError("Cannot set name of the asset resource")

    @property
    def ip_address(self):
        """IP address property.

        :return: host ip address
        :rtype: str
        """
        return self._ip_address

    @ip_address.setter
    def ip_address(self, value):
        """Set ip address property."""
        self._ip_address = value

    @property
    def metadata(self):
        """Metadata property.

        :return: host metadata
        :rtype: dict
        """
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        """Set metadata property."""
        raise AttributeError('You cannot set metadata directly. '
                             'Use function ~Asset.set_metadata')

    def set_metadata(self):
        """Set host metadata.

        This method probably will be helpful when passing data between
        action executions.
        """
        raise NotImplementedError

    @property
    def ansible_params(self):
        """Ansible parameters property.

        :return: ansible parameters for the host resource
        :rtype: dict
        """
        return self._ansible_params

    @ansible_params.setter
    def ansible_params(self, value):
        """Set ansible parameters property."""
        raise AttributeError('You cannot set the ansible parameters directly.'
                             ' This is set one time within the YAML input.')

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
        raise AttributeError('You cannot set the asset provider after asset '
                             'class is instantiated.')

    @property
    def provisioner_plugin(self):
        """Provisioner plugin property.

        :return: provisioner plugin class
        :rtype: object
        """
        return self._provisioner_plugin

    @provisioner_plugin.setter
    def provisioner_plugin(self, value):
        """Set provisioner plugin property."""
        raise AttributeError('You cannot set the asset provisioner plugin after asset '
                             'class is instantiated.')

    @property
    def role(self):
        """Role property.

        :return: role of the host
        :rtype: str
        """
        return self._role

    @role.setter
    def role(self, value):
        """Set role property."""
        raise AttributeError('You cannot set the role after asset class is '
                             'instantiated.')

    @role.deleter
    def role(self):
        """
        delete the role property
        :return:
        """
        del self._role

    @property
    def groups(self):
        """Groups property.

        :return: groups the host belongs to.
        :rtype: str
        """
        return self._groups

    @groups.setter
    def groups(self, value):
        """Set groups property."""
        raise AttributeError('You cannot set the groups after asset class is '
                             'instantiated.')

    @groups.deleter
    def groups(self):
        """
        delete the role property
        :return:
        """
        del self._groups

    def profile(self):
        """Builds a profile for the host resource.

        :return: the host profile
        :rtype: OrderedDict
        """
        profile = OrderedDict()
        profile['name'] = self.name
        profile['description'] = self.description

        # set the hosts's roles
        if hasattr(self, 'role'):
            if all(isinstance(item, string_types) for item in self.role):
                profile.update(role=[role for role in self.role])
        elif hasattr(self, 'groups'):
            if all(isinstance(item, string_types) for item in self.groups):
                profile.update(groups=[group for group in self.groups])

        try:
            if getattr(self, 'provisioner_plugin')is not None:
                profile.update({'provisioner': getattr(
                        self.provisioner_plugin, '__plugin_name__')})
                profile.update({'provider': self.provider_params})
        except AttributeError:
            self.logger.debug('Asset is static, no need to profile provider '
                              'facts.')
        finally:
            if self.ip_address:
                profile.update({'ip_address': self.ip_address})

        profile['ansible_params'] = self.ansible_params
        profile['metadata'] = self.metadata
        profile['workspace'] = self.workspace
        profile['data_folder'] = self.data_folder

        return profile

    def validate(self):
        """Validate the host."""
        if self.is_static:
            self.logger.debug('Validation is not required for static hosts!')
            return

        self.logger.info('Validating asset %s provider required parameters.' %
                         self.name)
        getattr(self.provider, 'validate_req_params')(self)

        self.logger.info('Validating asset %s provider optional parameters.' %
                         self.name)
        getattr(self.provider, 'validate_opt_params')(self)

        self.logger.info('Validating asset %s provider required credential '
                         'parameters.' % self.name)
        getattr(self.provider, 'validate_req_credential_params')(self)

        self.logger.info('Validating asset %s provider optional credential '
                         'parameters.' % self.name)
        getattr(self.provider, 'validate_opt_credential_params')(self)

    def _construct_validate_task(self):
        """Setup the validate task data structure.

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

    def _construct_provision_task(self):
        """Setup the provision task data structure.

        :return: provision task definition
        :rtype: dict
        """
        task = {
            'task': self._provision_task_cls,
            'name': str(self.name),
            'asset': self,
            'msg': '   provisioning asset %s' % self.name,
            'methods': self._req_tasks_methods
        }
        return task

    def _construct_cleanup_task(self):
        """Setup the cleanup task data structure.

        :return: cleanup task definition
        :rtype: dict
        """
        task = {
            'task': self._cleanup_task_cls,
            'name': str(self.name),
            'asset': self,
            'msg': '   cleanup asset %s' % self.name,
            'methods': self._req_tasks_methods
        }
        return task
