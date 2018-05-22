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

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from copy import copy

from ..core import CarbonResource, CarbonResourceError
from ..helpers import get_provider_class, get_providers_list, gen_random_str
from ..helpers import get_provisioner_class, get_default_provisioner
from ..helpers import get_provisioners_list, filter_host_name
from ..tasks import ProvisionTask, CleanupTask, ValidateTask


class CarbonHostError(CarbonResourceError):
    """Host's base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        self.message = message
        super(CarbonHostError, self).__init__(message)


class Host(CarbonResource):

    _valid_tasks_types = ['validate', 'provision', 'cleanup']
    _fields = [
        'name',
        'ip_address',
        'metadata',
        'ansible_params'
    ]

    def __init__(self,
                 config=None,
                 name=None,
                 provider=None,
                 provisioner=None,
                 parameters={},
                 validate_task_cls=ValidateTask,
                 provision_task_cls=ProvisionTask,
                 cleanup_task_cls=CleanupTask,
                 **kwargs):

        super(Host, self).__init__(config=config, name=name, **kwargs)

        # The name set in the constructor has precedence over other names.
        # If no name is set in the constructor, then it will look for the
        # name set in the parameters (usually done via YAML descriptor).
        # If no name is set in the parameters, then it generates a 20
        # characters name. Any way it is set, it will pass through the
        # filter. See `filter_host_name` for more info.
        if name is None:
            self._name = parameters.pop('name', None)
            if self._name is None:
                self._name = 'hst{0}'.format(gen_random_str(10))
        else:
            self._name = name
        self._name = filter_host_name(self._name)

        # TODO: we must define what role means for a host and document it.
        self._role = parameters.pop('role', None)
        if self._role is None:
            raise CarbonHostError('A role must be set for host %s.' %
                                  str(self.name))

        # metadata will be defined via yaml file
        self._metadata = parameters.pop('metadata', {})

        # Ansible parameters will be defined via yaml file
        self._ansible_params = parameters.pop('ansible_params', {})

        # IP address
        self._ip_address = parameters.pop('ip_address', None)

        # we must have a provider set
        provider_param = parameters.pop('provider', provider)
        if provider_param is None:
            raise CarbonHostError('A provider must be set for the host '
                                      '%s.' % str(self.name))
        if provider_param not in get_providers_list():
            raise CarbonHostError('Invalid provider for host '
                                  '%s.' % str(self.name))
        else:
            self._provider = get_provider_class(provider_param)()

        # We must set the provisioner and validate it
        provisioner_param = parameters.pop('provisioner', provisioner)
        if provisioner_param is None:
            self._provisioner = get_default_provisioner(self.provider)
        elif provisioner_param not in get_provisioners_list():
            raise CarbonHostError('Invalid provisioner for host '
                                  '%s.' % str(self.name))
        else:
            self._provisioner = get_provisioner_class(provisioner_param)

        # We must set the providers credentials initially
        self._credential = parameters.pop('credential', None)
        if self._credential is None:
            raise CarbonHostError('A credential must be set for the hosts '
                                  'provider %s.' % provider)
        provider_creds = parameters.pop('provider_creds', None)
        if provider_creds is None:
            raise CarbonHostError('Provider credentials must be set for '
                                  'host %s.' % str(self.name))
        # Get the credentials for the host provider
        cdata = next(i for i in provider_creds if i['name'] == self._credential)

        # every provider has a name as mandatory field.
        # first check if name exist (probably because of reusing machine).
        # otherwise generate random bits to be added to provider instance name
        # and create the provider name
        p_name_param = '{}{}'.format(self.provider.__provider_prefix__, 'name')
        p_name_set = parameters.get(p_name_param, None)
        if not p_name_set:
            parameters.update(
                {p_name_param: 'cbn_{}_{}'.format(self.name, gen_random_str(5))})
        elif not p_name_set[:4] == 'cbn_':
            raise CarbonHostError('The {0} parameter for {1} should not be'
                                  ' set as it is under the framework\'s '
                                  'control'.format(p_name_param, self._name))

        # check if we have all the mandatory fields set
        missing_mandatory_fields = \
            self.provider.check_mandatory_parameters(parameters)
        if len(missing_mandatory_fields) > 0:
            raise CarbonHostError('Missing mandatory fields for node %s,'
                                  ' based on the %s provider:\n\n%s'
                                  % (self.name, self.provider.name,
                                     missing_mandatory_fields))

        # create the provider attributes in the host object
        for p in self.provider.get_all_parameters():
            setattr(self, p, parameters.get(p, None))

        # Every provider must have credentials.
        # Check if provider credentials have all the mandatory fields set
        missing_mandatory_creds_fields = \
            self.provider.check_mandatory_creds_parameters(cdata)
        if len(missing_mandatory_creds_fields) > 0:
            raise CarbonHostError('Missing mandatory credentials fields '
                                  'for credentials section %s, for node '
                                  '%s, based on the %s provider:\n\n%s' %
                                  (self._credential, self._name,
                                   self.provider.name,
                                   missing_mandatory_creds_fields))

        # create the provider credentials in provider object
        self.provider.set_credentials(cdata)

        self._validate_task_cls = validate_task_cls
        self._provision_task_cls = provision_task_cls
        self._cleanup_task_cls = cleanup_task_cls

        self.reload_tasks()

        if parameters:
            self.load(parameters)

    @property
    def name(self):
        """Return the name for the host."""
        return self._name

    @name.setter
    def name(self, value):
        """Raises an exception when trying to set the name for the host after
        the class has been instanciated.
        :param value: The name for host
        """
        raise AttributeError('You cannot set name after class is instanciated.')

    @property
    def ip_address(self):
        """Return the IP address for the host (if applicable)."""
        return self._ip_address

    @ip_address.setter
    def ip_address(self, value):
        """Raise an exception when setting IP address directly. Use the
        following method ~Host.set_ip_address().

        :param value: The IP address of the host.
        """
        raise AttributeError('You cannot set ip address directly! Please use'
                             ' ~Host.set_ip_address().')

    def set_ip_address(self, value):
        """Set the IP address for the host. Following attributes will be set:
            1. _ip_address
            2. <provider_prefix>_ip_address

        :param value: The IP address of the host.
        """
        attr = 'ip_address'
        setattr(self, '_' + attr, value)
        setattr(self, self.provider.prefix + attr, copy(value))

    @property
    def metadata(self):
        """Return the name for the host."""
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        """Raises an exception when trying to set the name for the host after
        the class has been instanciated.
        :param value: The name for host
        """
        raise AttributeError('You cannot set metadata. This is set via descriptor YAML file.')

    @property
    def ansible_params(self):
        """Return the Ansible parameters for the host."""
        return self._ansible_params

    @ansible_params.setter
    def ansible_params(self, value):
        """Raises an exception when trying to set the ansible parameters for
        the host after the class has been instanciated.
        :param value: The ansible parameters for the host.
        """
        raise AttributeError(
            'You cannot set ansible_params. This is set via the descriptor '
            'YAML file.'
        )

    @property
    def provider(self):
        """Return the provider object for the host."""
        return self._provider

    @provider.setter
    def provider(self, value):
        """Raises an exception when trying to set the provider for the host
        after the class has been instanciated.
        :param value: The provider name for the host
        """
        raise AttributeError('You cannot set provider after class is instanciated.')

    @property
    def provisioner(self):
        """Return the provisioner object for the host."""
        return self._provisioner

    @provisioner.setter
    def provisioner(self, value):
        """Raises an exception when trying to set the provisioner for the host
        after the class has been instantiated .
        :param value: The provisioner name for the host
        """
        raise AttributeError('You cannot set provider after class is instanciated.')

    @property
    def role(self):
        """Return the role for the host."""
        return self._role

    @role.setter
    def role(self, value):
        """Raises an exception when trying to set the role for the host after
        the class has been instanciated.
        :param value: The role for the host
        """
        raise AttributeError('You cant set role after class is instanciated.')

    @property
    def uid(self):
        """Return the unique ID for the host"""
        return getattr(self, '{}name'.format(self.provider.prefix))

    @uid.setter
    def uid(self, value):
        """Raises an exception when trying to set the uid
        :param value: uid
        """
        raise AttributeError('You cannot set uid.')

    def profile(self):
        """Builds a profile for the host.
        :return: The profile for the host
        """
        d = self.provider.build_profile(self)
        d.update({
            'name': self.name,
            'metadata': self.metadata,
            'ansible_params': self.ansible_params,
            'provider': self.provider.name,
            'credential': self._credential,
            'provisioner': self.provisioner.__provisioner_name__,
            'role': self._role,
            'data_folder': self.data_folder()
        })

        # Set ip address attribute (if applicable)
        if self.ip_address:
            d.update({'ip_address': self.ip_address})
        return d

    def validate(self):
        """Validate the host."""
        status = 0
        for item in self.provider.validate(self):
            status = 1
            self.logger.error('Error with parameter "%s": %s', item[0], item[1])

        if status > 0:
            raise CarbonHostError('Host %s validation failed!' % self.name)

    def data_folder(self):
        return str(self.config['DATA_FOLDER'])

    def get_assets_list(self):
        """
        Run through each asset parameter and add its value
        in the list if the parameter was set
        :return: list of assets
        """
        # first, get the list of assets from the provider parameters
        host_assets = [getattr(self, param) for param in
                       self.provider.get_assets_parameters()
                       if (hasattr(self, param) and
                           getattr(self, param) is not None)]

        # second, get the list of assets from the provider's credential
        # settings
        creds_assets = [self.provider.credentials[param] for param in
                        self.provider.get_assets_parameters()
                        if param in self.provider.credentials.keys() and
                        self.provider.credentials[param] is not None]

        # return a single list from the merge of both list
        return host_assets + creds_assets

    def _construct_validate_task(self):
        """Setup the validate task data structure.
        :return: The validate task dict
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
        :param: The provision task dict
        """
        task = {
            'task': self._provision_task_cls,
            'name': str(self.name),
            'host': self,
            'msg': '   provisioning host %s' % self.name,
            'methods': self._req_tasks_methods
        }
        return task

    def _construct_cleanup_task(self):
        """Setup the cleanup task data structure.
        :return: The cleanup task dict
        """
        task = {
            'task': self._cleanup_task_cls,
            'name': str(self.name),
            'host': self,
            'msg': '   cleanup host %s' % self.name,
            'methods': self._req_tasks_methods
        }
        return task