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
    carbon.provisioners.beaker

    Carbon's own Beaker provisioner. This module handles everything from
    authentication to creating/deleting resources in Beaker.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import os
import uuid

from ..controllers import AnsibleController
from ..controllers import DockerController, DockerControllerException
from ..core import CarbonProvisioner, CarbonException
from ..helpers import get_ansible_inventory_script


class BeakerProvisionerException(CarbonException):
    """ Base class for Beaker provisioner exceptions."""


class BeakerProvisioner(CarbonProvisioner, AnsibleController,
                        DockerController):
    """The main class for carbon Beaker provisioner.

    This provisioner will interact with the Beaker server using the
    beaker client (bkr) to submit jobs to get resources from Beaker.

    Clashing (potential loss of data) will occur when trying to perform
    multiple requests with different authentication in the same namespace
    (with same config file). In order to handle this, we need to isolate
    each session with different namespaces. This will be handled by each
    scenario will have its own dedicated container to perform all the requests
    to the beaker server. This will isolate multiple scenarios runs on the
    same server.

    Please see the diagram below for an example:

    ------------      ------------
    | Scenario | --> | Container |
    ------------      ------------
         |                  |     -------------------------------
    ------------            | --> | $ bkr job-submit machine1.xml  |
    | - machine1 |          |     -------------------------------
    | - machine2 |          |
    ------------            |     -------------------------------
                            | --> | $ bkr job-submit machine2.xml  |
                                  -------------------------------

    This provisioner assumes that on the server, docker is installed and
    running.

    Docker has their own Python SDK that could be used to run the bkr commands
    inside a container. From trying out the SDK, there is a big limitation
    around getting the return code (status code) from the command run inside
    the container. They only return a string and it would be challenging to
    parse that since each bkr command may log different results. We will be
    able to take advtange of using Ansible to run commands into a running
    container. This way we can get both the stdout/stderr plus the return
    code to determine pass or fail.
    """
    __provisioner_name__ = "beaker"
    __provisioner_prefix__ = 'bkr_'

    _assets = ["bkr_arch"]

    _bkr_image = "docker-registry.engineering.redhat.com/carbon/bkr-client"

    def __init__(self, host):
        super(BeakerProvisioner, self).__init__()
        self.host = host
        self._data_folder = host.data_folder()

        # Set name for container
        self._name = self.host.bkr_name + '_' + str(uuid.uuid4())[:4]

        # Set ansible inventory file
        self.ansible_inventory = get_ansible_inventory_script('docker')
        # Set file permissions: pip install . does not give right permissions
        # to allow ansible to execute the script under site-packages.
        os.chmod(self.ansible_inventory, 0o775)

        # Run container
        try:
            self.run_container(self.name, self._bkr_image, entrypoint='bash')
        except DockerControllerException as ex:
            self.logger.warn(ex)
            raise BeakerProvisionerException("Issue bringing up the container")

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

    def authenticate(self):
        """Authenticate to Beaker server, support
        1. username/password
        2. keytab (file and kerberos principal)
        """
        pass
#         _cmd = "bkr whoami"
#
#         results = self.run_module(
#             dict(name='bkr authenticate', hosts=self.name, gather_facts='no',
#                  tasks=[dict(action=dict(module='shell', args=_cmd))])
#         )
#
#         self.results_analyzer(results['status'])

    def gen_bkr_xml(self):
        """ generate the Beaker xml from the host input
        """
        pass

    def submit_bkr_xml(self):
        """ submit the beaker xml and retrieve Beaker JOBID
        """
        pass

    def wait_for_bkr_job(self):
        """ wait for the Beaker job to be complete and return if the provisioning was
        successful or not, do we let user set a timeout, if timeout is reached, cancel the job,
        or always wait indefinitely for the machine to come up.
        """
        pass

    def get_bkr_logs(self):
        """ Retrieve the logs for the Beaker provisioning
        """
        pass

    def create(self):
        """Get a machine from Beaker based on the definition from the scenario.
        Steps:
        1.  authenticate
        2.  generate a beaker xml from the host data
        3.  submit a beaker job
        4.  watch for the beaker job to be complete -> return success or failed
        5.  get logs for the beaker job
        """
        self.logger.info('Provisioning machines from %s', self.__class__)

        # Authenticate to beaker
        self.authenticate()

        # generate the Beaker xml
        self.gen_bkr_xml()

        # submit the Beaker job and get the Beaker Job ID
        self.submit_bkr_xml()

        # wait for the bkr job to be complete and return pass or failed
        self.wait_for_bkr_job()

        # get the logs of the Beaker provisioning
        self.get_bkr_logs()

    def delete(self):
        """ Return the bkr machine back to the pool"""
        self.logger.info('Tearing down machines from %s', self.__class__)
        raise NotImplementedError
