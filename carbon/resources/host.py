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
from copy import copy

from ..core import CarbonResource
from ..exceptions import CarbonHostError
from ..helpers import get_provider_class, get_providers_list, gen_random_str
from ..helpers import get_provisioner_class, get_default_provisioner
from ..helpers import get_provisioners_list, filter_host_name
from ..tasks import ProvisionTask, CleanupTask, ValidateTask


class Host(CarbonResource):
    """
    The host resource class. The carbon compound can contain x amount of hosts.
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
                 provider=None,
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
        :param provider: provider name where host lives
        :type provider: str
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

        # apply filter to the hosts name
        self._name = filter_host_name(self._name)

        # set host description
        self._description = parameters.pop('description', None)

        # set the hosts role
        # TODO: we must define what role means for a host and document it.
        self._role = parameters.pop('role', None)
        if self._role is None:
            raise CarbonHostError('A role must be set for host %s.' %
                                  str(self.name))

        # set host metadata attribute (data pass-through)
        self._metadata = parameters.pop('metadata', {})

        # set host ansible parameters for later use by carbon actions
        self._ansible_params = parameters.pop('ansible_params', {})

        # set host ip address attribute (updated with ip after provisioning)
        self._ip_address = parameters.pop('ip_address', None)

        # (mandatory) set host provider
        provider_param = parameters.pop('provider', provider)
        if provider_param is None:
            raise CarbonHostError('A provider must be set for the host '
                                  '%s.' % str(self.name))

        # verify provider is supported by carbon
        if provider_param not in get_providers_list():
            raise CarbonHostError('Invalid provider for host '
                                  '%s.' % str(self.name))
        else:
            self._provider = get_provider_class(provider_param)()

        # (mandatory) set the provisioner and validate
        provisioner_param = parameters.pop('provisioner', provisioner)
        if provisioner_param is None:
            self._provisioner = get_default_provisioner(self.provider)
        elif provisioner_param not in get_provisioners_list():
            raise CarbonHostError('Invalid provisioner for host '
                                  '%s.' % str(self.name))
        else:
            self._provisioner = get_provisioner_class(provisioner_param)

        # Get required credentials for all providers other than Static
        # Static is user defined
        if provider_param != 'static':
            # (mandatory if not static) get the host provider credential name
            self._credential = parameters.pop('credential', None)
            if self._credential is None:
                raise CarbonHostError('A credential must be set for the hosts '
                                      'provider %s.' % provider)

            # (mandatory) set host provider credentials
            provider_creds = parameters.pop('provider_creds', None)
            if provider_creds is None:
                raise CarbonHostError('Provider credentials must be set for '
                                      'host %s.' % str(self.name))

            # get the credentials for the host provider
            cdata = next(i for i in provider_creds if i['name'] == self._credential)

        # every provider has a name as mandatory field.
        # first check if name exist (probably because of reusing machine).
        # otherwise generate random bits to be added to provider instance name
        # and create the provider name
        p_name_param = '{}{}'.format(getattr(self.provider,
                                             '__provider_prefix__'), 'name')
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
            getattr(self.provider, 'check_mandatory_parameters')(parameters)
        if len(missing_mandatory_fields) > 0:
            raise CarbonHostError('Missing mandatory fields for node %s,'
                                  ' based on the %s provider:\n\n%s'
                                  % (self.name, getattr(self.provider, 'name'),
                                     missing_mandatory_fields))

        # create the provider attributes in the host object
        for p in getattr(self.provider, 'get_all_parameters')():
            setattr(self, p, parameters.get(p, None))

        # every provider other than Static must have credentials
        # check if non Static provider credentials have all the mandatory fields set
        if provider_param != 'static':
            missing_mandatory_creds_fields = \
                getattr(self.provider, 'check_mandatory_creds_parameters')(cdata)
            if len(missing_mandatory_creds_fields) > 0:
                raise CarbonHostError('Missing mandatory credentials fields '
                                      'for credentials section %s, for node '
                                      '%s, based on the %s provider:\n\n%s' %
                                      (self._credential, self._name,
                                       getattr(self.provider, 'name'),
                                       missing_mandatory_creds_fields))

            # create the provider credentials in provider object
            getattr(self.provider, 'set_credentials')(cdata)
        else:
            self._credential = None

        # set the carbon task classes for the resource
        self._validate_task_cls = validate_task_cls
        self._provision_task_cls = provision_task_cls
        self._cleanup_task_cls = cleanup_task_cls

        # reload construct task methods
        self.reload_tasks()

        # load the parameters set into the object itself
        if parameters:
            self.load(parameters)

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
        raise AttributeError('You cannot set ip address directly. '
                             'Use function ~Host.set_ip_address')

    def set_ip_address(self, value):
        """Set the ip address for the host.

        Following attributes will be set:
            1. _ip_address
            2. <provider_prefix>_ip_address

        :param value: The IP address of the host.
        :type value: str
        """
        attr = 'ip_address'
        setattr(self, '_' + attr, value)
        setattr(self, getattr(self.provider, 'prefix') + attr, copy(value))

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
                             'Use function ~Host.set_metadata')

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
        raise AttributeError('You cannot set the host provider after host '
                             'class is instantiated.')

    @property
    def provisioner(self):
        """Provisioner property.

        :return: provisioner class
        :rtype: object
        """
        return self._provisioner

    @provisioner.setter
    def provisioner(self, value):
        """Set provisioner property."""
        raise AttributeError('You cannot set the host provisioner after host '
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
        raise AttributeError('You cannot set the role after host class is '
                             'instantiated.')

    @property
    def uid(self):
        """UID property.

        :return: the unique ID for the host
        :rtype: str
        """
        return getattr(self, '{}name'.format(getattr(self.provider, 'prefix')))

    @uid.setter
    def uid(self, value):
        """Set UID property."""
        raise AttributeError('You cannot set the uid for the host.')

    def profile(self):
        """Builds a profile for the host resource.

        :return: the host profile
        :rtype: dict
        """
        # initialize the profile with the provider properties
        profile = getattr(self.provider, 'build_profile')(self)

        # set additional host properties
        profile.update({
            'name': self.name,
            'description': self.description,
            'metadata': self.metadata,
            'ansible_params': self.ansible_params,
            'provider': getattr(self.provider, 'name'),
            'credential': self._credential,
            'provisioner': getattr(self.provisioner, '__provisioner_name__'),
            'role': self._role,
            'data_folder': self.data_folder,
            'workspace': self.workspace
        })

        # set ip address attribute (if applicable)
        if self.ip_address:
            profile.update({'ip_address': self.ip_address})

        return profile

    def validate(self):
        """Validate the host."""
        status = 0
        for item in getattr(self.provider, 'validate')(self):
            status = 1
            self.logger.error('Parameter error: "%s": %s' % (item[0], item[1]))

        if status > 0:
            raise CarbonHostError('Host %s validation failed!' % self.name)

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
            'host': self,
            'msg': '   provisioning host %s' % self.name,
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
            'host': self,
            'msg': '   cleanup host %s' % self.name,
            'methods': self._req_tasks_methods
        }
        return task
