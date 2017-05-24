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
from ..core import CarbonResource, CarbonException
from ..tasks import ProvisionTask, CleanupTask, ValidateTask
from ..helpers import get_provider_class, get_providers_list, gen_random_str
from ..helpers import get_provisioner_class, get_default_provisioner, get_provisioners_list


class CarbonHostException(CarbonException):
    pass


class Host(CarbonResource):

    _valid_tasks_types = ['validate', 'provision', 'cleanup']
    _valid_fields = ['name', 'ip_address']

    def __init__(self,
                 name=None,
                 parameters={},
                 validate_task_cls=ValidateTask,
                 provision_task_cls=ProvisionTask,
                 cleanup_task_cls=CleanupTask,
                 **kwargs):

        super(Host, self).__init__(name, **kwargs)

        # name can't be set after the host is instanciated
        # if no name is given, a uuid4 will be generated.
        if name is None:
            self._name = parameters.pop('name', None)
            if self._name is None:
                self._name = gen_random_str(12)
        else:
            self._name = name

        self._role = parameters.pop('role', None)
        if self._role is None:
            raise Exception('A role must be set for host %s.' % str(self.name))

        # Set the scenario id
        self._scenario_id = kwargs['scenario_id']

        # we must set provider initially and it can't be
        # changed afterwards.
        provider = parameters.pop('provider', None)
        if provider is None:
            raise Exception('A provider must be set for the host %s.' %
                            str(self.name))
        if provider not in get_providers_list():
            raise Exception('Invalid provider for host %s.' % str(self.name))
        else:
            self._provider = get_provider_class(provider)()

        # We must set the provisioner and validate it
        provisioner_set = parameters.pop('provisioner', None)

        if provisioner_set is None:
            self._provisioner = get_default_provisioner(self.provider)
        elif provisioner_set not in get_provisioners_list():
            raise Exception('Invalid provisioner for host %s.' % str(self.name))
        else:
            self._provisioner = get_provisioner_class(provisioner_set)

        # We must set the providers credentials initially
        provider_creds = parameters.pop('provider_creds', None)
        if provider_creds is None:
            raise Exception('Provider credentials must be set for host %s.' %
                            str(self.name))

        # every provider has a name as mandatory field.
        # first check if name exist (probably because of reusing machine).
        # otherwise generate random bits to be added to provider instance name
        # and create the provider name
        p_name_param = '{}{}'.format(self.provider.__provider_prefix__, 'name')
        if not parameters.get(p_name_param, None):
            parameters.update(
                {p_name_param: '{}-{}'.format(self.name, gen_random_str())})

        # check if we have all the mandatory fields set
        missing_mandatory_fields = \
            self.provider.check_mandatory_parameters(parameters)
        if len(missing_mandatory_fields) > 0:
            raise Exception('Missing mandatory fields for node %s,'
                            ' based on the %s provider:\n\n%s'
                            % (self.name, self.provider.name,
                               missing_mandatory_fields))

        # create the provider attributes in the host object
        for p in self.provider.get_all_parameters():
            setattr(self, p, parameters.get(p, None))

        # Every provider must have credentials.
        # Check if provider credentials have all the mandatory fields set
        missing_mandatory_creds_fields = \
            self.provider.check_mandatory_creds_parameters(
                provider_creds[parameters['credential']])
        if len(missing_mandatory_creds_fields) > 0:
            raise Exception('Missing mandatory credentials fields for '
                            'credentials section %s, for node %s, based on '
                            'the %s provider:\n\n%s'
                            % (parameters['credential'], self._name,
                               self.provider.name, missing_mandatory_creds_fields))

        # create the provider credentials in provider object
        self.provider.set_credentials(provider_creds[parameters['credential']])

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
    def scenario_id(self):
        """Return the scenario id the host is associated too."""
        return self._scenario_id

    @scenario_id.setter
    def scenario_id(self, value):
        """Raises an exception when trying to set the scenario id the host is
        associated too after the class has been instanciated.
        :param value: The scenario id for the host
        """
        raise AttributeError('You cannot set scenario id after class is instanciated.')

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

    def profile(self):
        """Builds a profile for the host.
        :return: The profile for the host
        """
        d = self.provider.build_profile(self)
        d.update({
            'name': self.name,
            'provider': self.provider.name(),
            'role': self._role,
            'provider_creds': self.provider.credentials,
            'scenario_id': self._scenario_id
        })
        return d

    def validate(self):
        """Validate the host."""
        status = 0
        for item in self.provider.validate(self):
            status = 1
            self.logger.error('Error with parameter "%s": %s', item[0], item[1])

        if status > 0:
            raise CarbonException('Host %s validation failed!' % self.name)

    def _construct_validate_task(self):
        """Setup the validate task data structure.
        :return: The validate task dict
        """
        task = {
            'task': self._validate_task_cls,
            'resource': self,
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
            'clean_msg': '   cleanup after provisioning host %s' % self.name
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
            'clean_msg': '   cleanup after cleanup host %s' % self.name
        }
        return task
