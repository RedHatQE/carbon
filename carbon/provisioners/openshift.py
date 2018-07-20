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

from ..helpers import exec_local_cmd
from ..core import CarbonProvisioner, CarbonProvisionerError


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
    (with same config file).
    """
    __provisioner_name__ = "openshift"
    __provisioner_prefix__ = 'oc_'

    _app_choices = ['image', 'git', 'template', 'custom_template']

    def __init__(self, host):
        """Constructor.

        :param host: The host object.
        :type host: object
        """
        super(OpenshiftProvisioner, self).__init__()
        self.host = host
        self._data_folder = host.data_folder
        self.workspace = getattr(host, 'workspace')
        self._routes = list()
        self._labels = list()
        self._finallabels = list()
        self._app_name = ""
        self._env_opts = ""

    @property
    def labels(self):
        """Return the label name to be associated with an apps resources."""
        return self._labels

    @labels.setter
    def labels(self, value):
        """Set the application labels.

        :param value: The application labels.
        """
        raise AttributeError('Labels cannot be set! Only by descriptor file.')

    def create_labels(self):
        """Creates the labels list to be applied to an application.

        This method will build the list of labels in the form of key:values.
        Any key which contains spaces will be replaced with a underscore.
        """
        for label in self.host.oc_labels:
            for k, v in label.items():
                self._labels.append(
                    str(k.strip().replace(' ', '_')) + '=' + str(v)
                )

        labels = ""
        for label in self.labels:
            labels = labels + label + ","
        labels = labels[:-1]
        finallabel = "'" + labels + "'"
        self._finallabels = finallabel

    def authenticate(self):
        """Authenticate with OpenShift.

        This method will attempt to authenticate with OpenShift using either
        a API token or username/password.
        """
        # save provider credentials
        credentials = self.host.provider.credentials

        # setup base oc login command
        _cmd = 'oc login %s --insecure-skip-tls-verify=True' % \
               credentials['auth_url']

        # append to oc login command based on authentication type
        if 'token' in credentials:
            _cmd += ' --token=%s' % credentials['token']
        elif 'username' and 'password' in credentials:
            _cmd += ' --username=%s --password=%s' % \
                    (credentials['username'], credentials['password'])
        else:
            raise OpenshiftProvisionerError(
                'Authentication type not supplied (token|username/password)'
            )

        self.logger.info('Authenticating with OpenShift..')

        # authenticate with openshift
        results = exec_local_cmd(_cmd)
        if results[0] != 0:
            self.logger.error(results[2])
            raise OpenshiftProvisionerError(
                'Authentication failed! Verify that your credentials are set'
                ' properly')
        self.logger.info('Successfully authenticated with OpenShift!')

    def select_project(self):
        """Select project to create applications in.

        This method will switch to the project defined in the scenario
        descriptor file.
        """
        # setup oc project command
        _cmd = 'oc project %s' % self.host.provider.credentials['project']

        self.logger.info('Selecting OpenShift project..')

        # select openshift project
        results = exec_local_cmd(_cmd)
        if results[0] != 0:
            self.logger.error(results[2])
            raise OpenshiftProvisionerError(
                'Failed to select project! Verify that your project defined '
                'actually exists in OpenShift.')
        self.logger.info('Successfully selected OpenShift project!')

    def _create(self):
        """Create a new application in OpenShift.

        This method will create a application based on the application type
        declared for the host. If multiple application types are defined, it
        will raise an exception (since we cannot determine which one the user
        wanted to create).
        """
        self.logger.info('Create application from %s', self.__class__)

        # authenticate with openshift
        self.authenticate()

        # select project to use
        self.select_project()

        # create labels to apply to application
        self.create_labels()

        # create environment variables to apply to application
        self.create_env_vars()

        # determine if multiple application types are defined
        application = None
        count = 0
        for atype in self._app_choices:
            # create key name
            app = self.__provisioner_prefix__ + atype

            # does the host have this attribute?
            found = False
            if hasattr(self.host, app):
                found = True

            # is the attribute None?
            if found and not getattr(self.host, app):
                continue

            # increment counter
            count += 1

            if count > 1:
                raise OpenshiftProvisionerError(
                    'Multiple application types defined, unable to decide '
                    'which to create!'
                )

            # save application type
            application = atype

        # exit if no application type given
        if not application:
            raise OpenshiftProvisionerError(
                'No application type declared for resource. Unable to create!'
            )

        self.logger.info('Provisioning application in OpenShift..')

        # call method to create application based on application type
        getattr(self, 'app_by_%s' % application)()

        self.logger.info('Successfully provisioned application in OpenShift!')

    def _delete(self):
        """Delete a application in OpenShift.

        This method will delete a application based on the labels associated
        to it. This will ensure no stale application elements are left
        laying around.
        """
        self.logger.info('Deleting application from %s', self.__class__)

        # authenticate with openshift
        self.authenticate()

        # select project to use
        self.select_project()

        # create labels to use to delete application
        self.create_labels()

        # setup oc delete command
        _cmd = 'oc delete all -l app={appname}'. \
            format(appname=str(self.host.oc_name).replace("_", "-"))

        self.logger.info('Deleting application in OpenShift..')

        # delete application
        results = exec_local_cmd(_cmd)
        if results[0] != 0:
            self.logger.error(results[2])
            raise OpenshiftProvisionerError(
                'Failed to delete application.')
        self.logger.info('Successfully deleted application in OpenShift!')

    def app_by_image(self):
        """Create application by docker image.

        This method creates a application in OpenShift based on a image. It
        will create the application, wait for the pod to be ready and expose
        the routes. It runs the following oc client command:
            - oc new-app --docker-image=<image> -l app=<label>
        """
        image_call = "--docker-image={0}".format(self.host.oc_image)

        # call oc new-app
        self.create_application("image", image_call)

        # wait for all pods to be up
        self.wait_for_pods()

        # expose routes
        self.expose_route()

        # show results for the app
        self.show_results()

    def app_by_git(self):
        """Create application by git repository.

        This method creates a application in OpenShift based on a git. It
        will create the application, wait for the pod to be ready and expose
        the routes. It runs the following oc client command:
            - oc new-app <git_url> -l app=<label>
        """
        # call oc new-app
        self.create_application("git", self.host.oc_git)

        # wait for all pods to be up
        self.wait_for_pods()

        # expose routes
        self.expose_route()

        # show results for the app
        self.show_results()

    def app_by_custom_template(self):
        """Create application by custom template.

        This method creates a application in OpenShift based on a template.
        It will create the application, wait for the pod to be ready and
        expose the routes. It runs the following oc client command:
            - oc new-app --file=./template --env=[] -l app=<label>
        """
        self.app_by_template()

    def app_by_template(self):
        """Create application by default template.

        This method creates a application in OpenShift based on a template.
        It will create the application, wait for the pod to be ready and
        expose the routes. It runs the following oc client command:
            - oc new-app --template=<name> --env=[] -l app=<label>
        """
        if self.host.oc_template:
            _template = self.host.oc_template
        else:
            _template = self.host.oc_custom_template
        _template_file = None
        _template_filename = None

        filepath = os.path.join(self.host.workspace, _template)

        if os.path.isfile(filepath):
            _template_file = filepath
            _template_filename = os.path.basename(filepath)

        if _template_file:
            custom_template_file = os.path.join(self.workspace,
                                                _template_filename)
            custom_template_call = "--file={}".format(custom_template_file)

            # we will not use env vars for custom templates
            # as they can be set in the template itself
            self.create_application("custom_template", custom_template_call)

        else:
            self.create_application("template", _template)

        # wait for all pods to be up
        self.wait_for_pods()

        # show results for the app
        self.show_results()

    def create_application(self, oc_type, value):
        """Create applications in OpenShift using oc client new-app.

        This method will create applications in OpenShift based on the
        application type defined. Other class methods call this method. This
        is used as a generic method to call.

        :param oc_type: Application type to create
        :type oc_type: str
        :param value: Data required for creating applicaton type defined.
        :type value: str
        """
        # setup oc new-app command
        _cmd = 'oc new-app {value} -l {labels} --name={appname} {opts}'.\
            format(value=value,
                   labels=self._finallabels,
                   opts=self._env_opts,
                   appname=str(self.host.oc_name).replace("_", "-"))

        self.logger.debug('OpenShift Client comamnd: %s' % _cmd)

        self.logger.info('Creating application from %s..' % oc_type)

        # create application
        results = exec_local_cmd(_cmd)
        if results[0] != 0:
            self.logger.error(results[2])
            raise OpenshiftProvisionerError(
                'Error creating application from %s.' % oc_type)
        self.logger.info('Successfully created application from %s!' % oc_type)

    def create_env_vars(self):
        """Create the environment variables to be applied to the application.

        This method creates the environment variables to be passed to the
        application created.
        """
        self._env_opts = ""
        # get the env vars if set
        env_vars = getattr(self.host, 'oc_env_vars', None)
        if env_vars is not None:
            for env_key in env_vars:
                self._env_opts = self._env_opts + "-p " + env_key + "=" +\
                                 env_vars[env_key] + " "

    def wait_for_pods(self):
        """Wait for pods to be ready.

        This method will wait for pods to be ready. It will check if any builds
        are running as they need tobe complete before pods will become ready
        (up).
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

            # check build status, needs to be 'no resources found or complete'

            _cmd = 'oc get builds -l app={appname} -o yaml'. \
                format(appname=str(self.host.oc_name).replace("_", "-"))

#             self.logger.debug(_cmd)
            # check the build status

            results = exec_local_cmd(_cmd)
            if results[0] != 0:
                error_msg = results[2]
                if "No resources" in error_msg:
                    buildcheck = False
                    pass
                else:
                    self.logger.error(results[2])
                    raise OpenshiftProvisionerError("Unable to get the builds")
            mydict = yaml.load(results[1])

            # no builds yet
            if not mydict["items"]:
                pass
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

            _cmd = 'oc get pods -l app={appname} -o yaml'. \
                format(appname=str(self.host.oc_name).replace("_", "-"))

#             self.logger.debug(_cmd)

            results = exec_local_cmd(_cmd)
            if results[0] != 0:
                error_msg = results[2]
                if "No resources" in error_msg:
                    self.logger.info("Pod not created yet")
                    errcheck += 1
                    time.sleep(10)
                    wait -= 10
                    continue
                else:
                    raise OpenshiftProvisionerError(
                        "Unexpected output when checking for created pods: "
                        "{}".format(error_msg))

            mydict = yaml.load(results[1])

            # no pods displayed
            if not mydict["items"]:
                podcheck = False

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

            # complete if all conditions passed and no Exceptions thrown
            self.logger.info("Build Complete and all pods are up")
            return
        # timeout reached
        raise OpenshiftProvisionerError("Timeout reached waiting for builds"
                                        "to complete and pods to come up")

    def expose_route(self):
        """Expose application routes for external access.

        This method will expose application routes for external access to the
        application. It runs the following oc client command:
            - oc get svc -l (extract application name)
            - oc expose svc <name>
        """
        _cmd = 'oc get svc -l app={appname} -o yaml'. \
            format(appname=str(self.host.oc_name).replace("_", "-"))

        results = exec_local_cmd(_cmd)
        if results[0] != 0:
            self.logger.error(results[2])
            raise OpenshiftProvisionerError(
                'Unable to get application name')

        parsed_results = results[1]
        mydict = yaml.load(parsed_results)
        try:
            app_name = mydict["items"][0]["metadata"]["name"]
        except KeyError:
            # this may be the case where there is no svc for the application
            self.logger.warn("unable to get application name " + parsed_results)

        if app_name:
            _cmd = 'oc expose svc {0}'.format(self._app_name)

            results = exec_local_cmd(_cmd)
            if results[0] != 0:
                self.logger.warning("Unable to expose routes")
                self.logger.warning(results[2])
            self.logger.info('Successfully exposed routes')

    def show_results(self):
        """Show the results from a pod creation.

        This method will return the data (application name & routes if they
        are defined). It runs the following commands:
            - oc get pod -l (extract application name from a pod)
            - oc get route -l (extract all routes that are defined for a pod)
        """
        # TODO: Function should set these values in temporary yaml of the input
        # TODO: (cont). will wait for implementation to update before adding
        # app name should already be set
        self.logger.debug("return app name: {}".format(self._app_name))

        _cmd = 'oc get route -l app={appname} -o yaml'.\
            format(appname=str(self.host.oc_name).replace("_", "-"))

        results = exec_local_cmd(_cmd)
        if results[0] != 0:
            self.logger.error(results[2])
            raise OpenshiftProvisionerError(
                'Failed getting routes')

        parsed_results = results[1]
        mydict = yaml.load(parsed_results)

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
