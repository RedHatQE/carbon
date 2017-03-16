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
import uuid
import random
import string

from ..core import CarbonResource
from ..tasks import ProvisionTask, CleanupTask, ValidateTask
from ..helpers import get_provider_class, get_providers_list


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
                self._name = str(uuid.uuid4())
        else:
            self._name = name

        # we must set provider initially and it can't be
        # changed afterwards.
        provider = parameters.pop('provider', None)
        if provider is None:
            raise Exception('A provider must be set for the host.')
        if provider not in get_providers_list():
            raise Exception('Invalid provider for host %s.' % str(self.name))
        else:
            self._provider_cls = get_provider_class(provider)

        # every provider has a name as mandatory field.
        # first check if name exist (probably because of reusing machine).
        # otherwise generate random bits to be added to provider instance name
        # and create the provider name
        p_name_param = '{}{}'.format(self.provider.__provider_prefix__, 'name')
        if not parameters.get(p_name_param, None):
            # random bits - http://stackoverflow.com/a/23728630
            rnd_bits = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(8))
            parameters.update(
                {p_name_param: '{}-{}'.format(self.name, rnd_bits)})

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

        self._validate_task_cls = validate_task_cls
        self._provision_task_cls = provision_task_cls
        self._cleanup_task_cls = cleanup_task_cls

        self.reload_tasks()

        if parameters:
            self.load(parameters)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        raise AttributeError('You can set name after class is instanciated.')

    @property
    def provider(self):
        return self._provider_cls

    @provider.setter
    def provider(self, value):
        raise AttributeError('You can set provider after class is instanciated.')

    def profile(self):
        d = self.provider.build_profile(self)
        d.update({
            'name': self.name,
            'provider': self.provider.name(),
        })
        return d

    def _construct_validate_task(self):
        task = {
            'task': self._validate_task_cls,
            'name': str(self.name),
            'package': self,
            'msg': '   validating host %s' % self.name,
            'clean_msg': '   cleanup after validating host %s' % self.name
        }
        return task

    def _construct_provision_task(self):
        task = {
            'task': self._provision_task_cls,
            'name': str(self.name),
            'host': self,
            'msg': '   provisioning host %s' % self.name,
            'clean_msg': '   cleanup after provisioning host %s' % self.name
        }
        return task

    def _construct_cleanup_task(self):
        task = {
            'task': self._cleanup_task_cls,
            'name': str(self.name),
            'host': self,
            'msg': '   cleanup host %s' % self.name,
            'clean_msg': '   cleanup after cleanup host %s' % self.name
        }
        return task
