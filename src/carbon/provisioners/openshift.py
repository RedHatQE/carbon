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
import os

from ..constants import CARBON_ROOT
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

        # Set ansible inventory file
        self.ansible_inventory = get_ansible_inventory_script('docker')

        # Run container
        try:
            self.run_container(self.name, self._oc_image, entrypoint='bash')
        except DockerControllerException as ex:
            self.logger.warn(ex)

        # Authenticate with openshift
        self.authenticate()

        # Select project to use
        self.select_project()

        # Set a normalized label list
        self.setup_label()

        # set the labels
        self.get_final_label()

        # set the env_vars if set
        self.env_opts()

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

    def setup_label(self):
        """
        Sets a normalized list of key, values for the label, which is a list
        The keys cannot have spaces, they will be replaced w/an underscore
        """
        label_list_original = self.host_desc["oc_labels"]
        label_list_final = []

        for label in label_list_original:
            k, v = label.items()[0]
            normalized_key = k.strip().replace(" ", "_")
            label_list_final.append(str(normalized_key) + "=" + str(v))
        self._label = label_list_final

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
        self.logger.info('Create application from %s', self.__class__)

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

        # added temporarily to delete while testing
#         self.delete()

    def delete(self):
        """Delete all resources associated with an application. It will
        delete all resources for an application using the label assocaited to
        it. This ensures no stale resources are left laying around.
        """
        self.logger.info('Deleting application from %s', self.__class__)

        _cmd = 'oc delete all -l {0}'.\
            format(self._finallabel)

        results = self.run_module(
            dict(name='oc delete all', hosts=self.name, gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args=_cmd))])
        )

        self.results_analyzer(results['status'])
        if results['status'] != 0:
            raise OpenshiftProvisionerException

    def app_by_image(self):
        """Create a new application in an openshift server from a docker image.

        E.g. $ oc new-app --docker-image=<image> -l app=<label>
        """
        image = self.host_desc["oc_image"]
        image_call = "--docker-image\={}".format(image)

        # call oc new-app
        self.newapp("image", image_call)

    def app_by_git(self):
        """Create a new application in an openshift server from a git
        repository (source code).

        E.g. $ oc new-app <git_url> -l app=<label>
        """
        git_url = self.host_desc["oc_git"]

        # call oc new-app
        self.newapp("git", git_url)

    def app_by_template(self):
        """Create a new application in openshift from a template. This can
        either use an existing template stored in openshift or a local
        template.

        E.g. $ oc new-app --template=<name> --env=[] -l app=<label>
        E.g. $ oc new-app --file=./template --env=[] -l app=<label>
        """
        _template = self.host_desc["oc_template"]
        _template_file = None
        _template_filename = None

        # check in the carbon root dir for the file as .yml or yaml
        filepath1 = os.path.join(CARBON_ROOT, _template + ".yaml")
        filepath2 = os.path.join(CARBON_ROOT, _template + ".yml")

        # checks for a custom template
        if os.path.isfile(filepath1):
            _template_file = filepath1
            _template_filename = os.path.basename(filepath1)
        elif os.path.isfile(filepath2):
            _template_file = filepath2
            _template_filename = os.path.basename(filepath2)

        # copy file to container
        if _template_file:

            src_file_path = _template_file
            dest_full_path_file = '/tmp/'

            cp_args = 'src={0} dest={1} mode=0755'.format(src_file_path, dest_full_path_file)

            results = self.run_module(
                dict(name='copy file', hosts=self.name, gather_facts='no',
                     tasks=[dict(action=dict(module='copy', args=cp_args))])
            )

            if results['status'] != 0:
                raise OpenshiftProvisionerException

            custom_template_file = os.path.join("/tmp", _template_filename)
            custom_template_call = "--file\={}".format(custom_template_file)

            # we will not use env vars for custom templates
            # as they can be set in the template itself
            self._env_opts = ""
            self.newapp("custom_template", custom_template_call)

        else:
            self.newapp("template", _template)

    def newapp(self, oc_type, value):
        """
        generic newapp call that should work for almost all use cases that we support

        :param oc_type: used for the name of the call
        :param value: data that will be passed in after oc new-app <value>
        """
        _cmd = 'oc new-app {0} -l {1} {2}'.\
            format(value, self._finallabel, self._env_opts)

        self.logger.debug(_cmd)
        results = self.run_module(
            dict(name='oc new-app {}'.format(oc_type), hosts=self.name, gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args=_cmd))])
        )

        self.results_analyzer(results['status'])
        if results['status'] != 0:
            raise OpenshiftProvisionerException

    def env_opts(self):
        self._env_opts = ""
        # get the env vars if set
        if "oc_env_vars" in self.host_desc:
            env_vars = self.host_desc["oc_env_vars"]

            for env_key in env_vars:
                self._env_opts = self._env_opts + "-p " + env_key + "=" + env_vars[env_key] + " "
            self._env_opts = self._env_opts.strip().replace("=", "\=")

    def expose_route(self):
        """Expose an existing container externally via routes.

        E.g. $ oc expose server <name>
        """
        # TODO: Setup the oc new-app command
        # TODO: Run the command inside container by Ansible
        raise NotImplementedError

    def get_final_label(self):
        '''get the required label(s) in the format expected by oc
        '''
        labels = ""
        for label in self.label:
            labels = labels + label + ","
        labels = labels[:-1]
        finallabel = "'" + labels + "'"
        finallabel = finallabel.replace("=", "\=")
        self._finallabel = finallabel
