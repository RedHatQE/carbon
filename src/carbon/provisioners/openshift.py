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
    carbon.provisioners.carbon_openshift

    Carbons own openshift provisioner. This module handles everything from
    authentication to creating/deleting resources in an openshift server.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..controllers import AnsibleController
from ..controllers import DockerController, DockerControllerException
from ..core import CarbonProvisioner, CarbonException
from ..helpers import get_ansible_inventory_script


class OpenshiftProvisionerException(CarbonException):
    """Base class for openshift provisioner exceptions."""
    pass


class OpenshiftProvisioner(CarbonProvisioner, AnsibleController,
                           DockerController):
    """The main class for carbon openshift provisioner.

    This provisioner will interact with an openshift server using the
    openshift client (oc) tool to create applications in projects. As of
    now it will not create projects (projects must exist).

    The openshift client tool login (authentication) is by one of the
    following:

    1. username/password
    2. token

    Once login is successfully, it will save the connection into the
    configuration file stored at the user home directory: ~/.kube/config.

    Clashing (potential loss of data) will occur when trying to perform
    multiple requests with different authentication in the same namespace
    (with same config file). In order to handle this, we need to isolate
    each session with different namespaces. This will be handled by each
    scenario will have its own dedicated container to perform all the request
    to openshift server. This will isolate multiple scenarios runs on the
    same server.

    Please see the diagram below for an example:

    ------------      ------------
    | Scenario | --> | Container |
    ------------      ------------
         |                  |     ------------------------
    ------------            | --> | $ oc new-app app1 .. |
    | - app1   |            |     ------------------------
    | - app2   |            |
    ------------            |     ------------------------
                            | --> | $ oc new-app app2 .. |
                                  ------------------------

    This provisioner assumes that on the server, docker is installed and
    running.

    Docker has their own Python SDK that could be used to run the oc commands
    inside a container. From trying out the SDK, there is a big limitation
    around getting the return code (status code) from the command run inside
    the container. They only return a string and it would be challenging to
    parse that since each oc command may log different results. We will be
    able to take advtange of using Ansible to run commands into a running
    container. This way we can get both the stdout/stderr plus the return
    code to determine pass or fail.
    """
    __provisioner_name__ = "openshift"
    __provisioner_prefix__ = 'oc_'

    _oc_image = "rywillia/openshift-client"

    _app_choices = ['image', 'git', 'template']

    def __init__(self, host_desc):
        """Constructor.

        When the carbon openshift provisioner class is instantiated, it will
        perform the following tasks:

        * Create the container to handle executing all oc commands.
        * Authenticate with the openshift server.
        * Change projects to use the one declared in the scenario.
        * Setup the label to associate an application and its resources with.

        :param host_desc: A host description in (dict form) based on a Carbon
            host object.
        """
        super(OpenshiftProvisioner, self).__init__()
        self.host_desc = host_desc

        # Set name for container
        # TODO: Set actual name based on scenario name + uuid
        self._name = 'KEVIN'

        # Set label for application and its resources
        # TODO: Read labels from self.host_desc and set
        self._label = 'MINIONS'

        # Set ansible inventory file
        self.ansible_inventory = get_ansible_inventory_script('docker')

        # Run container
        try:
            self.run_container(self.name, self._oc_image, entrypoint='bash')
        except DockerControllerException as ex:
            print(ex)

        # Authenticate with openshift
        self.authenticate()

        # Select project to use
        self.select_project()

        self.setup_label()

    @property
    def name(self):
        """Return the name for the container."""
        return self._name

    @name.setter
    def name(self, value):
        """Raises an exception when trying to set the name for the container
        after the class has been instanciated.
        :param value: The name for container.
        """
        raise AttributeError('You cannot set name for container after the '
                             'class is instanciated.')

    @property
    def label(self):
        """Return the label name to be associated with an apps resources."""
        return self._label

    @label.setter
    def label(self, value):
        """Raises an exception when trying to set label name for application
        after the class has been instanciated.
        """
        raise AttributeError('You cannot set the label name for the '
                             'application after the class is instanciated.')

    def authenticate(self):
        """Establish an authenticated session with openshift server.

        Connection will be saved to the default configuration file under the
        users home directory.
        """
        _auth_url = self.host_desc['provider_creds']['auth_url']
        _token = self.host_desc['provider_creds']['token']

        _cmd = "oc login {0} --insecure-skip-tls-verify\=True --token\={1}".\
            format(_auth_url, _token)
        results = self.run_module(
            dict(name='oc authenticate', hosts=self.name, gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args=_cmd))])
        )

        self.results_analyzer(results['status'])
        if results['status'] != 0:
            raise OpenshiftProvisionerException

    def select_project(self):
        """Switch to another project.

        Scenario is declared within the scenario openshift credentials section.
        Once project is switched it will become the default project.
        """
        _cmd = "oc project {0}".format(
            self.host_desc['provider_creds']['project'])
        results = self.run_module(
            dict(name='oc project', hosts=self.name, gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args=_cmd))])
        )

        self.results_analyzer(results['status'])
        if results['status'] != 0:
            raise OpenshiftProvisionerException

    def create(self):
        """Create a new application in openshift based on the type of
        application declared in the scenario.

        First we will determine which application method to call based on the
        application declared in the host profile. If a profile has multiple
        application types declared, an exception will be raised. We are not
        able to tell which one the user actually wanted to use.
        """
        print('Create application from {klass}'.format(klass=self.__class__))

        newapp = None
        count = 0
        for app in self._app_choices:
            _app = self.__provisioner_prefix__ + app
            if _app in self.host_desc and not self.host_desc[_app] is None:
                count += 1
                newapp = app

        if count > 1:
            raise OpenshiftProvisionerException(
                'More than one application type are declard for resource. '
                'Unable to determine which one to use.')

        if newapp is None:
            raise OpenshiftProvisionerException(
                'Application type not defined for resource. Available choices'
                ' ~ %s' % self._app_choices)

        try:
            getattr(self, 'app_by_%s' % newapp)()
        except AttributeError:
            raise OpenshiftProvisionerException(
                'Openshift provisioner does not have a method for application'
                ' by %s' % newapp)

    def delete(self):
        """Delete all resources associated with an application. It will
        delete all resources for an application using the label assocaited to
        it. This ensures no stale resources are left laying around.
        """
        print('Deleting application from {klass}'.format(klass=self.__class__))

    def app_by_image(self):
        """Create a new application in an openshift server from a docker image.

        E.g. $ oc new-app --docker-image=<image> -l app=<label>
        """
        # TODO: Setup the oc new-app command
        # TODO: Run the command inside container by Ansible
        # TODO: Call the expose_route method to have external access?
        raise NotImplementedError

    def app_by_git(self):
        """Create a new application in an openshift server from a git
        repository (source code).

        E.g. $ oc new-app <git_url> -l app=<label>
        """
        # TODO: Setup the oc new-app command
        # TODO: Run the command inside container by Ansible
        raise NotImplementedError

    def app_by_template(self):
        """Create a new application in openshift from a template. This can
        either use an existing template stored in openshift or a local
        template.

        E.g. $ oc new-app --template=<name> --env=[] -l app=<label>
        E.g. $ oc new-app --file=./template --env=[] -l app=<label>
        """
        # TODO: Setup the oc new-app command
        # TODO: Run the command inside container by Ansible
        raise NotImplementedError

    def expose_route(self):
        """Expose an existing container externally via routes.

        E.g. $ oc expose server <name>
        """
        # TODO: Setup the oc new-app command
        # TODO: Run the command inside container by Ansible
        raise NotImplementedError
