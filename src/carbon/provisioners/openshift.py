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
from ..core import CarbonProvisioner


class OpenshiftProvisioner(CarbonProvisioner):
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

    _oc_image = "rywillia/openshift-client"

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

        # TODO: Instantiate the AnsibleWorker class

        self.create_container()
        self.authenticate()
        self.select_project()
        self.setup_label()

    def create_container(self):
        """Create the container based on the image which already has the
        openshift client (oc) tool installed.

        It will first check to see if an existing container is running with
        the same name. If found it will re-use the conatiner else create a new
        container.

        http://docs.ansible.com/ansible/docker_container_module.html
        """
        # TODO: Ansible call to check container running
        # TODO: Based on results, either return or create a new container
        raise NotImplementedError

    def authenticate(self):
        """Create the authenticated session to the openshift server. The
        session will be saved to the default configuration file stored at the
        user home directory.
        """
        # _auth_url = self.host_desc['provider_creds']['auth_url']
        # _token = self.host_desc['provider_creds']['token']

        # _cmd = "oc login {0} --insecure-skip-tls-verify=True --token={1}".\
        #    format(_auth_url, _token)

        # TODO: Run command inside container by Ansible

    def select_project(self):
        """Select the project to use on the openshift server based on the one
        declared inside the scenario file. This will become the default
        project.
        """
        # _cmd = "oc project {0}".format(
        #    self.host_desc['provider_creds']['project'])

        # TODO: Run command inside container by Ansible

    def setup_label(self):
        """Create the label to be associated to an application when created.
        This label may be either pre-defined (declared inside the scenario) or
        can be generated by carbon at run time.
        """
        # TODO: Code to create the label and save into memory for later use
        self._label = 'testlabel'

    @property
    def label(self):
        """Return the label associated with an application."""
        return self._label

    @label.setter
    @staticmethod
    def label(value):
        """Raise an exception when trying to update the label for an
        application after the carbon openshift provisioner class was
        instantiated.
        """
        raise ValueError('Unable to set application label too {0}. You '
                         'cannot set the label after the class is '
                         'instanticated.'.format(value))

    def create(self):
        """Create a new application in openshift based on the type of
        application declared in the scenario.
        """
        print('Provisioning machines from {klass}'
              .format(klass=self.__class__))

    def delete(self):
        """Delete all resources associated with an application. It will
        delete all resources for an application using the label assocaited to
        it. This ensures no stale resources are left laying around.
        """
        print('Tearing down machines from {klass}'
              .format(klass=self.__class__))

    def create_oc_image(self):
        """Create a new application in an openshift server from a docker image.

        E.g. $ oc new-app --docker-image=<image> -l app=<label>
        """
        # TODO: Setup the oc new-app command
        # TODO: Run the command inside container by Ansible
        # TODO: Call the expose_route method to have external access?
        raise NotImplementedError

    def create_oc_git(self):
        """Create a new application in an openshift server from a git
        repository (source code).

        E.g. $ oc new-app <git_url> -l app=<label>
        """
        # TODO: Setup the oc new-app command
        # TODO: Run the command inside container by Ansible
        raise NotImplementedError

    def create_oc_template_name(self):
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
