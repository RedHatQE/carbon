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
    carbon.core

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import sys
import inspect

from taskrunner import Task
from .helpers import get_core_tasks_classes


class CarbonException(Exception):
    pass


class CarbonTask(Task):

    def __init__(self, name=None, **kwargs):
        super(CarbonTask, self).__init__(**kwargs)

        if name is not None:
            self.name = name

    def run(self, context):
        pass

    def cleanup(self, context):
        pass

    def __str__(self):
        return self.name


class CarbonResource(object):

    _valid_tasks_types = []
    _fields = []

    def __init__(self, name=None, **kwargs):

        self._name = name

        # A list of tasks that will be executed upon the reource.
        self._tasks = []

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        raise AttributeError('You can set name after class is instanciated.')

    def _add_task(self, t):
        """
        Add a task to the list of tasks for the resource
        """
        if t['task'] not in set(get_core_tasks_classes()):
            raise CarbonException('The task class "%s" used is not valid.'
                                  % t['task'])
        self._tasks.append(t)

    def _extract_tasks_from_resource(self):
        lst = []
        for name, obj in inspect.getmembers(self, inspect.isclass):
            if issubclass(obj, CarbonTask):
                lst.append(name)
        return lst

    def load(self, data):
        for key, value in data.items():
            # name has precedence when coming from a YAML file
            # if name is set through name=, it will be overwritten
            # by the YAML file properties.
            if key == 'name':
                self._name = value
            elif key in self._fields:
                setattr(self, key, value)
        if data:
            self.reload_tasks()

    def _get_task_constructors(self):
        return [getattr(self, "_construct_%s_task" % task_type)
                for task_type in self._valid_tasks_types]

    def reload_tasks(self):
        self._tasks = []
        for task_constructor in self._get_task_constructors():
            self._add_task(task_constructor())

    def dump(self):
        pass

    def get_tasks(self):
        return self._tasks

    def profile(self):
        raise NotImplementedError


class Provisioner(object):
    """
    This is the base class for all provisioners for provisioning machines
    """
    def create(self):
        raise NotImplementedError


class CarbonProvider(object):
    """
    This is the base class for all providers
    """
    # the YAML definition uses this value to reference to this class.
    # you have to override this variable in the subclasses so it can be
    # referenced within the YAML definition with provider=...
    __provider_name__ = None
    __provider_prefix__ = None

    _mandatory_parameters = ()
    _optional_parameters = ()

    def __init__(self, **kwargs):
        # I care only about the parameters set on ~self._parameters
        params = {k for k, v in kwargs.items()}\
            .intersection({'{}{}'.format(self.__provider_prefix__, k) for k in self._mandatory_parameters})
        for k, v in kwargs.items():
            if k in params:
                setattr(self, k, v)

    def __str__(self):
        return '<Provider: %s>' % self.__provider_name__

    @classmethod
    def name(cls):
        return cls.__provider_name__

    @classmethod
    def check_mandatory_parameters(cls, parameters):
        """
        Validates the parameters against the mandatory parameters set
        by the class.
        :param parameters: a dictionary of parameters
        :return: an empty set if all mandatory fields satisfy or the list of
                 fields that needs to be filled.
        """
        intersec = {k for k, v in parameters.items()}\
            .intersection({'{}{}'.format(cls.__provider_prefix__, k) for k in cls._mandatory_parameters})
        return {'{}{}'.format(cls.__provider_prefix__, k) for k in cls._mandatory_parameters}.difference(intersec)

    @classmethod
    def get_mandatory_parameters(cls):
        """
        Get the list of the mandatory parameters
        :return: a tuple of the mandatory paramaters.
        """
        return ('{}{}'.format(cls.__provider_prefix__, k) for k in cls._mandatory_parameters)

    @classmethod
    def get_optional_parameters(cls):
        """
        Get the list of the optional parameters
        :return: a tuple of the optional paramaters.
        """
        return ('{}{}'.format(cls.__provider_prefix__, k) for k in cls._optional_parameters)

    @classmethod
    def get_all_parameters(cls):
        """
        Return the list of all possible parameters for the provider.
        :return: a tuple with all parameters
        """
        all_params = {'{}{}'.format(cls.__provider_prefix__, k) for k in cls._mandatory_parameters}\
            .union({'{}{}'.format(cls.__provider_prefix__, k) for k in cls._optional_parameters})
        return (param for param in all_params)

    @classmethod
    def build_profile(cls, host):
        """
        Builds a dictionary with with all parameters for the provider
        :param host: a Host object
        :return: a dictionary with all parameters
        """
        profile = {}
        for param in cls.get_all_parameters():
            profile.update({
                param: getattr(host, param, None)
            })
        return profile
