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
import time

import os
import yaml

from ..controllers import AnsibleController
from ..controllers import DockerController, DockerControllerError
from ..core import CarbonProvisioner, CarbonProvisionerError
from ..helpers import get_ansible_inventory_script


class OpenshiftProvisionerError(CarbonProvisionerError):
    """Base class for openshift provisioner exceptions."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        self.message = message
        super(OpenshiftProvisionerError, self).__init__(message)


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
    __provisioner_prefix__ = 'oc_'

    _oc_image = "rywillia/openshift-client"
    _app_choices = ['image', 'git', 'template']

    def __init__(self, host):
        """Constructor.

        When the carbon openshift provisioner class is instantiated, it will
        perform the following tasks:

        * Create the container to handle executing all oc commands.

        :param host: The host object.
        """
        super(OpenshiftProvisioner, self).__init__()
        self.host = host
        self._data_folder = host.data_folder()

        self._routes = []
        self._labels = []
        self._finallabels = []
        self._app_name = ""
        self._env_opts = ""

        # Create controller objects
        self._docker = DockerController(cname=self.host.oc_name)
        self._ansible = AnsibleController(
            inventory=get_ansible_inventory_script(self.docker.name.lower())
        )

        # Run container
        try:
            self.docker.run_container(self._oc_image, entrypoint='bash')
        except DockerControllerError as ex:
            self.logger.warn(ex)

    @property
    def docker(self):
        """Return the docker object."""
        return self._docker

    @docker.setter
    def docker(self, value):
        """Raises an exception when trying to instantiate docker controller
        after provisioner class has been instantiated.

        :param value: The name for docker container.
        """
        raise ValueError('You cannot create a docker controller object after '
                         'provisioner class has been instantiated.')

    @property
    def ansible(self):
        """Return the ansible object."""
        return self._ansible

    @ansible.setter
    def ansible(self, value):
        """Raises an exception when trying to instantiate the ansible
        controller after provisioner class has been instantiated.
        """
        raise ValueError(
            'You cannot create a ansible controller object after provisioner '
            'class has been instantiated.'
        )

    @property
    def labels(self):
        """Return the label name to be associated with an apps resources."""
        return self._labels

    @labels.setter
    def labels(self, value):
        """Raises an exception when trying to set lebels for application
        after the class has been instanciated.
        """
        raise AttributeError('You cannot set the labels through the '
                             'provisioning classes. Use the scenario '
                             'descriptor instead.')

    def setup_labels(self):
        """Sets a normalized list of key:values for the label, which is a list.
        The keys cannot have spaces, they will be replaced w/an underscore
        """
        for label in self.host.oc_labels:
            for k, v in label.items():
                self._labels.append(
                    str(k.strip().replace(' ', '_')) + '=' + str(v)
                )

    def authenticate(self):
        """Establish an authenticated session with openshift server.

        Connection will be saved to the default configuration file under the
        users home directory.
        """
        _cmd = 'oc login %s --insecure-skip-tls-verify\=True' % \
               self.host.provider.credentials['auth_url']

        # Choose which authentication to use. Token will always be used first.
        if 'token' in self.host.provider.credentials:
            _cmd += ' --token\=%s' % self.host.provider.credentials['token']
        elif 'username' and 'password' in self.host.provider.credentials:
            _cmd += ' --username\=%s --password\=%s' % \
                    (self.host.provider.credentials['username'],
                     self.host.provider.credentials['password'])
        else:
            self.logger.error('Authentication type not found. Supported types:'
                              ' <token|username/password>.')
            # Stop/remove container
            self.docker.stop_container()
            self.docker.remove_container()
            raise OpenshiftProvisionerError(
                'Authentication type not found. Supported types:'
                ' <token|username/password>.')

        results = self.ansible.run_module(
            dict(name='oc authenticate', hosts=self.host.oc_name, gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args=_cmd))])
        )

        self.ansible.results_analyzer(results['status'])
        if results['status'] != 0:
            try:
                # Stop/remove container
                self.docker.stop_container()
                self.docker.remove_container()
            except DockerControllerError as ex:
                raise OpenshiftProvisionerError(ex.message)
            finally:
                raise OpenshiftProvisionerError(
                    'Could not authenticate. Please check credentials.')

    def select_project(self):
        """Switch to another project.

        Scenario is declared within the scenario openshift credentials section.
        Once project is switched it will become the default project.
        """
        _cmd = "oc project {0}".format(
            self.host.provider.credentials['project'])
        results = self.ansible.run_module(
            dict(name='oc project', hosts=self.host.oc_name, gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args=_cmd))])
        )

        self.ansible.results_analyzer(results['status'])
        try:
            if results['status'] != 0:
                # Stop/remove container
                self.docker.stop_container()
                self.docker.remove_container()
                raise OpenshiftProvisionerError('Failed to select project')
        except DockerControllerError as ex:
            raise OpenshiftProvisionerError(ex)

    def create(self):
        """Create a new application in openshift based on the type of
        application declared in the scenario.

        First we will determine which application method to call based on the
        application declared in the host profile. If a profile has multiple
        application types declared, an exception will be raised. We are not
        able to tell which one the user actually wanted to use.
        """
        self.logger.info('Create application from %s', self.__class__)

        # Authenticate with openshift
        self.authenticate()

        # Select project to use
        self.select_project()

        # Set a normalized label list
        self.setup_labels()

        # set the labels
        self.get_final_labels()

        # set the env_vars if set
        self.env_opts()

        newapp = None
        count = 0
        for app in self._app_choices:
            _app = self.__provisioner_prefix__ + app
            val = getattr(self.host, _app, None)
            if val and val is not None:
                count += 1
                newapp = app

        try:
            try:
                if count > 1:
                    self.logger.error('More than one application type are '
                                      'declared for resource. Unable to '
                                      'determine which one to use.')
                    raise OpenshiftProvisionerError('More than one application type are '
                                                    'declared for resource. Unable to '
                                                    'determine which one to use.')

                if newapp is None:
                    # check for custom template
                    if getattr(self.host, "oc_custom_template", None):
                        newapp = "template"
                    else:
                        self.logger.error('Application type not defined for '
                                          'resource. Available choices ~ %s' %
                                          self._app_choices)
                        raise OpenshiftProvisionerError('Application type not '
                                                        'defined for resource.')

                getattr(self, 'app_by_%s' % newapp)()
            finally:
                # Stop/remove container
                self.docker.stop_container()
                self.docker.remove_container()
        except DockerControllerError as ex:
            raise OpenshiftProvisionerError('Docker error. - %s' % ex.message)

    def delete(self):
        """Delete all resources associated with an application. It will
        delete all resources for an application using the label associated to
        it. This ensures no stale resources are left laying around.
        """
        self.logger.info('Deleting application from %s', self.__class__)

        # Authenticate with openshift
        self.authenticate()

        # Select project to use
        self.select_project()

        # Set a normalized label list
        self.setup_labels()

        # set the labels
        self.get_final_labels()

        _cmd = 'oc delete all -l app\={appname}'. \
            format(appname=str(self.host.oc_name).replace("_", "-"))

        results = self.ansible.run_module(
            dict(name='oc delete all', hosts=self.host.oc_name, gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args=_cmd))])
        )

        self.ansible.results_analyzer(results['status'])

        try:
            # Stop/remove container
            self.docker.stop_container()
            self.docker.remove_container()

            if results['status'] != 0:
                raise OpenshiftProvisionerError(
                    'Failed to delete application.'
                )
        except DockerControllerError as ex:
            raise OpenshiftProvisionerError(ex)

    def app_by_image(self):
        """Create a new application in an openshift server from a docker image.

        E.g. $ oc new-app --docker-image=<image> -l app=<label>
        """
        image = self.host.oc_image
        image_call = "--docker-image\={}".format(image)

        # call oc new-app
        self.newapp("image", image_call)

        # wait for all pods to be up
        self.wait_for_pods()

        # expose routes
        self.expose_route()

        # show results for the app
        self.show_results()

    def app_by_git(self):
        """Create a new application in an openshift server from a git
        repository (source code).

        E.g. $ oc new-app <git_url> -l app=<label>
        """
        git_url = self.host.oc_git

        # call oc new-app
        self.newapp("git", git_url)

        # wait for all pods to be up
        self.wait_for_pods()

        # expose routes
        self.expose_route()

        # show results for the app
        self.show_results()

    def app_by_template(self):
        """Create a new application in openshift from a template. This can
        either use an existing template stored in openshift or a local
        template.

        E.g. $ oc new-app --template=<name> --env=[] -l app=<label>
        E.g. $ oc new-app --file=./template --env=[] -l app=<label>
        """
        if self.host.oc_template:
            _template = self.host.oc_template
        else:
            _template = self.host.oc_custom_template
        _template_file = None
        _template_filename = None

        filepath = os.path.join(self._data_folder, "assets", _template)

        if os.path.isfile(filepath):
            _template_file = filepath
            _template_filename = os.path.basename(filepath)

        # copy file to container
        if _template_file:

            src_file_path = _template_file
            dest_full_path_file = '/tmp/'

            cp_args = 'src={0} dest={1} mode=0755'.format(src_file_path, dest_full_path_file)

            results = self.ansible.run_module(
                dict(name='copy file', hosts=self.host.oc_name, gather_facts='no',
                     tasks=[dict(action=dict(module='copy', args=cp_args))])
            )

            if results['status'] != 0:
                raise OpenshiftProvisionerError(
                    'Failed to create new application by template.'
                )

            custom_template_file = os.path.join("/tmp", _template_filename)
            custom_template_call = "--file\={}".format(custom_template_file)

            # we will not use env vars for custom templates
            # as they can be set in the template itself
            self.newapp("custom_template", custom_template_call)

        else:
            self.newapp("template", _template)

        # wait for all pods to be up
        self.wait_for_pods()

        # show results for the app
        self.show_results()

    def newapp(self, oc_type, value):
        """
        generic newapp call that should work for almost all use cases that we support

        :param oc_type: used for the name of the call
        :param value: data that will be passed in after oc new-app <value>
        """
        _cmd = 'oc new-app {value} -l {labels} --name\={appname} {opts}'.\
            format(value=value,
                   labels=self._finallabels,
                   opts=self._env_opts,
                   appname=str(self.host.oc_name).replace("_", "-"))

        self.logger.debug(_cmd)
        results = self.ansible.run_module(
            dict(name='oc new-app {}'.format(oc_type), hosts=self.host.oc_name, gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args=_cmd))])
        )

        self.ansible.results_analyzer(results['status'])
        if results['status'] != 0:
            raise OpenshiftProvisionerError('Error creating app. %s' % results)

    def env_opts(self):
        self._env_opts = ""
        # get the env vars if set
        env_vars = getattr(self.host, 'oc_env_vars', None)
        if env_vars is not None:
            for env_key in env_vars:
                self._env_opts = self._env_opts + "-p " + env_key + "=" + env_vars[env_key] + " "
            self._env_opts = self._env_opts.strip().replace("=", "\=")

    def wait_for_pods(self):
        """ waiting for all pods to be up
        also need to check to see if any builds are running, as they need
        to be complete before any pods will come up.
        """
        self.logger.info("Sleeping for 10 secs for buildconfigs to be started")
        time.sleep(10)

        # default max wait time of 30 mins
        wait = getattr(self.host, 'oc_build_timeout', None)
        if wait is None:
            wait = 1800

        # new attempt every 10 seconds
        total_attempts = wait / 10

        errcheck = 0
        attempt = 0
        while wait > 0:
            if errcheck > 4:
                raise OpenshiftProvisionerError("pods never came up")
            buildcheck = True
            podcheck = True
            attempt += 1
            self.logger.info("Attempt {0} of {1}: Checking for pods to all "
                             "be running".format(attempt, total_attempts))

            # check the build status, which needs to be No resources found or Complete

            _cmd = 'oc get builds -l app\={appname} -o yaml'. \
                format(appname=str(self.host.oc_name).replace("_", "-"))

#             self.logger.debug(_cmd)
            results = self.ansible.run_module(
                dict(name='oc get builds {}', hosts=self.host.oc_name, gather_facts='no',
                     tasks=[dict(action=dict(module='shell', args=_cmd))])
            )
            self.ansible.results_analyzer(results['status'])
            if len(results["callback"].contacted) == 1:
                parsed_results = results["callback"].contacted[0]["results"]
            else:
                raise OpenshiftProvisionerError("Unexpected Error")
            if "stdout" in parsed_results and "stderr" in parsed_results["stdout"]:
                if "No resources" in parsed_results["stdout"]["stderr"]:
                    pass
                else:
                    raise OpenshiftProvisionerError(
                        "Unexpected Error checking builds: {}".format(
                            parsed_results["stdout"]["stderr"])
                    )
            elif "stdout" in parsed_results:
                mydict = yaml.load(parsed_results["stdout"])
                for item in mydict["items"]:
                    build_status = item['status']['phase']
                    if build_status == "Complete":
                        buildcheck = buildcheck and True
                    elif build_status == "Failed":
                        self.logger.error("The build failed")
                        raise OpenshiftProvisionerError('The build failed')
                    else:
                        # Build is still in progress
                        buildcheck = False
                # if all builds are not Complete, retry, else continue
                if not buildcheck:
                    self.logger.info("Sleeping for 10 secs for all builds to complete")
                    time.sleep(10)
                    wait -= 10
                    continue
            elif "stderr_lines" in parsed_results and parsed_results["stderr_lines"]:
                raise OpenshiftProvisionerError(
                    "Unexpected Error when Checking the build:: {}".format(
                        parsed_results["stderr_lines"])
                )
            else:
                raise OpenshiftProvisionerError(
                    "Unexpected Error when Checking the build: {}".format(
                        parsed_results)
                )

            _cmd = 'oc get pods -l app\={appname} -o yaml'. \
                format(appname=str(self.host.oc_name).replace("_", "-"))

#             self.logger.debug(_cmd)
            results = self.ansible.run_module(
                dict(name='oc get pods', hosts=self.host.oc_name, gather_facts='no',
                     tasks=[dict(action=dict(module='shell', args=_cmd))])
            )

            if len(results["callback"].contacted) == 1:
                parsed_results2 = results["callback"].contacted[0]["results"]
            else:
                raise OpenshiftProvisionerError("Unexpected Error")
            if "stderr" in parsed_results2 and parsed_results2["stderr"]:
                # check if pods have not been created yet
                if "No resources" in parsed_results2["stderr"]:
                    self.logger.info("Pod not created yet")
                    errcheck += 1
                    time.sleep(10)
                    wait -= 10
                    continue
                else:
                    raise OpenshiftProvisionerError(
                        "Unexpected output when checking for created pods: "
                        "{}".format(parsed_results2["stderr"]))
            elif "stdout" in parsed_results2 and parsed_results2["stdout"]:
                mydict = {}
                mydict = yaml.load(parsed_results2["stdout"])

#                 self.logger.debug(len(mydict["items"]))
                for item in mydict["items"]:
                    build_status = item['status']['phase']
                    if build_status == "Running":
                        # set the app name
                        self._app_name = item["metadata"]["labels"]["app"]
                        podcheck = podcheck and True
                    else:
                        # Build is still in progress
                        podcheck = False
                # if all pods are Running, retry, else continue
                if not podcheck:
                    self.logger.debug("Sleeping for 10 secs waiting for all pods to be Running")
                    time.sleep(10)
                    wait -= 10
                    continue
            elif "stderr_lines" in parsed_results2 and parsed_results2["stderr_lines"]:
                raise OpenshiftProvisionerError(
                    "Unexpected Error when Checking the pod: {}".format(
                        parsed_results["stderr_lines"])
                )
            else:
                raise OpenshiftProvisionerError(
                    "Unexpected Error when Checking the build: {}".format(
                        parsed_results)
                )

            # complete if all conditions passed and no Exceptions thrown
            self.logger.info("Build Complete and all pods are up")
            return
        # timeout reached
        raise OpenshiftProvisionerError("Timeout reached waiting for builds"
                                        "to complete and pods to come up")

    def expose_route(self):
        """Expose an existing container externally via routes.

        E.g. $ oc expose server <name>
        oc get svc -l -> extract app name
        oc expose svc <app_name>
        """
        _cmd = 'oc get svc -l app\={appname} -o yaml'. \
            format(appname=str(self.host.oc_name).replace("_", "-"))

#             self.logger.debug(_cmd)
        results = self.ansible.run_module(
            dict(name='oc get svc -l', hosts=self.host.oc_name, gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args=_cmd))])
        )

        if len(results["callback"].contacted) == 1:
            parsed_results = results["callback"].contacted[0]["results"]
        else:
            raise OpenshiftProvisionerError("Unexpected Error")
        mydict = yaml.load(parsed_results["stdout"])
        try:
            app_name = mydict["items"][0]["metadata"]["name"]
        except:
            # this may be the case where there is no svc for the application
            self.logger.warn("unable to get application name " + parsed_results)

        if app_name:
            _cmd = 'oc expose svc {0}'.format(self._app_name)

            results = self.ansible.run_module(
                dict(name='oc expose svc', hosts=self.host.oc_name, gather_facts='no',
                     tasks=[dict(action=dict(module='shell', args=_cmd))])
            )
            self.ansible.results_analyzer(results['status'])

    def show_results(self):
        """return the data from the creation of pods (App name & routes if exist)
        oc get pod -l -> extract app name from any pod
        oc get route -l -> extract all routes that are set
        TODO: this function should set these vals in a temporary yaml of the input
              will wait for the implementation of where to update before adding that
              functionality.
        """
        # app name should already be set
        self.logger.debug("return app name: {}".format(self._app_name))

        _cmd = 'oc get route -l app\={appname} -o yaml'.\
            format(appname=str(self.host.oc_name).replace("_", "-"))

        results = self.ansible.run_module(
            dict(name='oc get route', hosts=self.host.oc_name, gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args=_cmd))])
        )

        if len(results["callback"].contacted) == 1:
            parsed_results = results["callback"].contacted[0]["results"]
        else:
            raise OpenshiftProvisionerError("Unexpected Error")
        self.ansible.results_analyzer(results['status'])
        mydict = yaml.load(parsed_results["stdout"])

        if mydict["items"]:
            for item in mydict["items"]:
                if "spec" in item and "host" in item["spec"]:
                    self._routes.append(item["spec"]["host"])
            self.logger.debug("returning routes: {}".format(self._routes))
        else:
            self.logger.debug("returning no routes: {}".format(self._routes))

        # update output values for the user
        self.host.oc_app_name = self._app_name
        self.host.oc_routes = self._routes

    def get_final_labels(self):
        """get the required label(s) in the format expected by oc."""
        labels = ""
        for label in self.labels:
            labels = labels + label + ","
        labels = labels[:-1]
        finallabel = "'" + labels + "'"
        finallabel = finallabel.replace("=", "\=")
        self._finallabels = finallabel
