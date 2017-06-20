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
import time

from xml.dom.minidom import parseString

from ..controllers import AnsibleController
from ..controllers import DockerController, DockerControllerException
from ..core import CarbonProvisioner, CarbonProvisionerException
from ..helpers import get_ansible_inventory_script


class BeakerProvisionerException(CarbonProvisionerException):
    """ Base class for Beaker provisioner exceptions."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        self.message = message
        super(BeakerProvisionerException, self).__init__(message)


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

    _assets = ["keytab"]
    _bkr_xml = "bkrjob.xml"

    _bkr_image = "docker-registry.engineering.redhat.com/carbon/bkr-client"

    def __init__(self, host):
        super(BeakerProvisioner, self).__init__()
        self.host = host
        self._data_folder = host.data_folder()

        # Set name for container
        self._name = self.host.bkr_name + '_' + str(uuid.uuid4())[:4]

        # Set ansible inventory file
        self.ansible_inventory = get_ansible_inventory_script('docker')

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
        bkr_config = "/etc/beaker/client.conf"
        # Case 1: user has username and password set
        if ["username", "password"] <= self.host.provider.credentials.keys() \
                and self.host.provider.credentials["username"] and \
                self.host.provider.credentials["password"]:
            self.logger.info("Authentication w/ username/pass")

            # Modify the config file with correct data
            summary = "update beaker config - username"
            username = self.host.provider.credentials["username"]
            replace_line = 'USERNAME=\"{0}\"'.format(username)
            cmd = 'path={0} regexp=^#USERNAME line={1}'.format(bkr_config, replace_line)
            self.lineinfile_call(summary, replace_line, cmd)

            summary = "update beaker config - password"
            password = self.host.provider.credentials["password"]
            replace_line = 'PASSWORD=\"{0}\"'.format(password)
            cmd = 'path={0} regexp=^#PASSWORD line={1}'.format(bkr_config, replace_line)
            self.lineinfile_call(summary, replace_line, cmd)

        # Case 2: user has a keytab and principal set
        elif ["keytab", "keytab_principal"] <= self.host.provider.credentials.keys() \
                and self.host.provider.credentials["keytab"] and \
                self.host.provider.credentials["keytab_principal"]:
            self.logger.info("Authentication w/ keytab/keytab_principal")

            # copy the keytab file to container
            src_file_path = os.path.join(self._data_folder, self.host.provider.credentials["keytab"])
            dest_full_path_file = '/etc/beaker'

            cp_args = 'src={0} dest={1} mode=0755'.format(src_file_path, dest_full_path_file)

            results = self.run_module(
                dict(name='copy file', hosts=self.name, gather_facts='no',
                     tasks=[dict(action=dict(module='copy', args=cp_args))])
            )

            if results['status'] != 0:
                raise BeakerProvisionerException("Error when copying file to container")

            # Modify the config file with correct data
            summary = "update beaker config - authmethod"
            replace_line = 'AUTH_METHOD=\"krbv\"'
            cmd = 'path={0} regexp=^AUTH_METHOD line={1}'.format(bkr_config, replace_line)
            self.lineinfile_call(summary, replace_line, cmd)

            summary = "update beaker config: keytab filename"
            keytab_path = os.path.join(dest_full_path_file, self.host.provider.credentials["keytab"])
            replace_line = 'KRB_KEYTAB=\"{0}\"'.format(keytab_path)
            cmd = 'path={0} regexp=^#KRB_KEYTAB line={1}'.format(bkr_config, replace_line)
            self.lineinfile_call(summary, replace_line, cmd)

            summary = "update beaker config: keytab principal"
            replace_line = 'KRB_PRINCIPAL=\"{0}\"'.format(self.host.provider.credentials["keytab_principal"])
            cmd = 'path={0} regexp=^#KRB_PRINCIPAL line={1}'.format(bkr_config, replace_line)
            self.lineinfile_call(summary, replace_line, cmd)

        # Case 3: invalid authentication vals
        else:
            raise BeakerProvisionerException("Unable to Authenticate, please set"
                                             " username/password or keytab/keytab_principal.")

        # verify that the authentication worked
        _cmd = "bkr whoami"

        results = self.run_module(
            dict(name='bkr authenticate', hosts=self.name, gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args=_cmd))])
        )

        self.results_analyzer(results['status'])
        if results['status'] != 0:
            raise BeakerProvisionerException("Authentication was not successful")

    def lineinfile_call(self, summary, replace_line, lineinfilecmd):
        self.logger.debug(lineinfilecmd)

        results = self.run_module(
            dict(name=summary, hosts=self.name, gather_facts='no',
                 tasks=[dict(action=dict(module='lineinfile', args=lineinfilecmd))])
        )

        if results['status'] != 0:
            raise BeakerProvisionerException("Error when {0}".format(summary))

    def gen_bkr_xml(self):
        """ generate the Beaker xml from the host input
        """
        pass

    def submit_bkr_xml(self):
        """ submit the beaker xml and retrieve Beaker JOBID
        """
        self.logger.info("Submitting bkr job")
        # copy the xml to container
        src_file_path = os.path.join(self._data_folder, self._bkr_xml)
        dest_full_path_file = '/tmp'

        cp_args = 'src={0} dest={1} mode=0755'.format(src_file_path, dest_full_path_file)

        results = self.run_module(
            dict(name='copy file', hosts=self.name, gather_facts='no',
                 tasks=[dict(action=dict(module='copy', args=cp_args))])
        )

        self.results_analyzer(results['status'])
        if results['status'] != 0:
            raise BeakerProvisionerException("Error when copying bkr xml to container")

        bkr_xml_path = os.path.join(dest_full_path_file, self._bkr_xml)
        _cmd = "bkr job-submit --xml {0}".format(bkr_xml_path)

        results = self.run_module(
            dict(name='bkr job submit', hosts=self.name, gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args=_cmd))])
        )

        self.results_analyzer(results['status'])

        if results['status'] != 0:
            raise BeakerProvisionerException("Error submitting Beaker job")
        else:
            if len(results["callback"].contacted) == 1:
                parsed_results = results["callback"].contacted[0]["results"]
            else:
                raise BeakerProvisionerException("Unexpected Error submitting job")

            output = parsed_results["stdout"]
            if output.find("Submitted:") != "-1":
                # set the result as ascii instead of unicode
                self.host.bkr_job_id = output[output.find("[") + 2:output.find("]") - 1].encode('ascii', 'ignore')
                self.logger.info("just submitted: {}".format(self.host.bkr_job_id))
            else:
                raise BeakerProvisionerException("Unexpected Error submitting job")

    def wait_for_bkr_job(self):
        """ wait for the Beaker job to be complete and return if the provisioning was
        successful or not, do we let user set a timeout, if timeout is reached, cancel the job,
        or always wait indefinitely for the machine to come up.
        """
        # default max wait time of 8 hrs
        wait = getattr(self.host, 'bkr_timeout', None)
        if wait is None:
            wait = 28800

        # check Beaker status every 60 seconds
        total_attempts = wait / 60

        attempt = 0
        while wait > 0:
            attempt += 1
            self.logger.info("Waiting for machine to be ready, attempt {0} of"
                             " {1}".format(attempt, total_attempts))

            _cmd = "bkr job-results {0}".format(self.host.bkr_job_id)

            results = self.run_module(
                dict(name='bkr job status', hosts=self.name, gather_facts='no',
                     tasks=[dict(action=dict(module='shell', args=_cmd))])
            )

            self.results_analyzer(results['status'])

            if results['status'] != 0:
                raise BeakerProvisionerException("Unable to check status of the beaker job")
            else:
                if len(results["callback"].contacted) == 1:
                    parsed_results = results["callback"].contacted[0]["results"]
                else:
                    raise BeakerProvisionerException("Unexpected Error submitting job")

                bkr_xml_output = parsed_results["stdout"]
                bkr_job_status_dict = self.get_job_status(bkr_xml_output)
                self.logger.debug("Beaker job status: {}".format(bkr_job_status_dict))
                status = self.analyze_results(bkr_job_status_dict)

                if status == "wait":
                    wait -= 60
                    time.sleep(60)
                    continue
                elif status == "success":
                    self.logger.info("Machine is successfully provisioned from Beaker")
                    return
                elif status == "fail":
                    raise BeakerProvisionerException("Machine provision failed: {}".format(self.host.bkr_job_id))
                else:
                    raise BeakerProvisionerException("Unknown status from Beaker job")
        # timeout reached for Beaker job
        self.logger.error("Timeout reached waiting for Beaker job to complete.")
        self.cancel_job()
        raise BeakerProvisionerException("Timeout reached for Beaker job")

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

        try:
            # Stop/remove container
            self.stop_container(self.name)
            self.remove_container(self.name)
        except DockerControllerException as ex:
            raise BeakerProvisionerException(ex)

    def cancel_job(self):
        """Cancel a Beaker job """
        self.logger.info('Tearing down machines from %s', self.__class__)
        _cmd = "bkr job-cancel {0}".format(self.host.bkr_job_id)

        results = self.run_module(
            dict(name='bkr job cancel', hosts=self.name, gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args=_cmd))])
        )

        self.results_analyzer(results['status'])

        if results['status'] != 0:
            raise BeakerProvisionerException("Error cancelling Beaker job")
        else:
            if len(results["callback"].contacted) == 1:
                parsed_results = results["callback"].contacted[0]["results"]
            else:
                raise BeakerProvisionerException("Unexpected Error submitting job")

            output = parsed_results["stdout"]
            if "Cancelled" in output:
                self.logger.info("Successfully cancelled: {}".format(self.host.bkr_job_id))
            else:
                raise BeakerProvisionerException("Unexpected Error cancelling job")

    def delete(self):
        """ Return the bkr machine back to the pool"""
        self.logger.info('Tearing down machines from %s', self.__class__)

        # Authenticate to beaker
        self.authenticate()

        # cancel the job
        self.cancel_job()

        try:
            # Stop/remove container
            self.stop_container(self.name)
            self.remove_container(self.name)
        except DockerControllerException as ex:
            raise BeakerProvisionerException(ex)

    def get_job_status(self, xmldata):
        """
        Used to parse the Beaker results xml

        :param xmldata: xmldata of a beaker job status
        :return: dictionary of job and install task statuses
        :raises BeakerProvisionerException: if results cannot be analyzed successfully
        """

        mydict = {}
        try:
            dom = parseString(xmldata)
        except Exception as e:
            raise BeakerProvisionerException("Error Issue reading xml data {}".format(e))

        # check job status
        joblist = dom.getElementsByTagName('job')
        # verify it is a length of 1 else exception
        if len(joblist) != 1:
            raise BeakerProvisionerException("Unable to parse job results from "
                                             "{}".format(self.host.bkr_job_id))
        mydict["job_result"] = joblist[0].getAttribute("result")
        mydict["job_status"] = joblist[0].getAttribute("status")

        tasklist = dom.getElementsByTagName('task')
        for task in tasklist:
            cname = task.getAttribute('name')
#             id = task.getAttribute('id')

            if cname == '/distribution/install':
                mydict["install_result"] = task.getAttribute('result')
                mydict["install_status"] = task.getAttribute('status')

        if "install_status" in mydict and mydict["install_status"]:
            return mydict
        else:
            raise BeakerProvisionerException("Couldn't find install task status")

    def analyze_results(self, resultsdict):
        """
        return success, fail, or warn based on the job and install task statuses

        :param resultsdict: dictionary of job and install task statuses
        :return: action str [wait, success, or fail]
        :raises BeakerProvisionerException: if results cannot be analyzed successfully
        """
        # when is the job complete
        if resultsdict["job_result"].strip().lower() == "new" and \
           resultsdict["job_status"].strip().lower() in ["new", "waiting", "queued", "scheduled"]:
            return "wait"
        elif resultsdict["install_result"].strip().lower() == "new" and \
                resultsdict["install_status"].strip().lower() in ["new", "waiting", "queued", "scheduled", "running"]:
            return "wait"
        elif resultsdict["job_result"].strip().lower() == "pass" and \
            resultsdict["job_status"].strip().lower() == "running" and \
            resultsdict["install_result"].strip().lower() == "pass" and \
                resultsdict["install_status"].strip().lower() == "completed":
            return "success"
        elif resultsdict["job_result"].strip().lower() == "new" and \
            resultsdict["job_status"].strip().lower() == "running" and \
            resultsdict["install_result"].strip().lower() == "new" and \
                resultsdict["install_status"].strip().lower() == "completed":
            return "success"
        elif resultsdict["job_result"].strip().lower() == "warn":
            return "fail"
        elif resultsdict["job_result"].strip().lower() == "fail":
            return "fail"
        else:
            raise BeakerProvisionerException("Unexpected Job status {}".format(resultsdict))
