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
import stat
import uuid
import time
import socket
from xml.dom.minidom import parse, parseString

import paramiko

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


class BeakerProvisioner(CarbonProvisioner):
    """The main class for carbon Beaker provisioner.

    This provisioner will interact with the Beaker server using the
    beaker client (bkr) to submit jobs to get resources from Beaker.

    Clashing (potential loss of data) will occur when trying to perform
    multiple requests with different authentication in the same namespace
    (with same config file). In order to handle this, we need to isolate
    each session with different namespaces. This will be handled by each
    scenario, each resource will have its own dedicated container to perform the requests
    to the beaker server. This will isolate multiple scenarios runs and resources on the
    same server.

    Please see the diagram below for an example:

    ------------      ------------
    | Scenario | --> | Resources  |
    ------------     | - machine1 |
                     | - machine2 |
                      ------------
                            |      -----------       --------------------------------
                            | --> | Container | --> | $ bkr job-submit machine1.xml  |
                            |      -----------       --------------------------------
                            |
                            |      -----------       --------------------------------
                            | --> | Container | --> | $ bkr job-submit machine2.xml  |
                                   -----------       --------------------------------

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

    _bkr_xml = "bkrjob.xml"

    _bkr_image = "docker-registry.engineering.redhat.com/carbon/bkr-client"

    def __init__(self, host):
        super(BeakerProvisioner, self).__init__()
        self.host = host

        # Set Data Folder
        self._data_folder = host.data_folder()

        # Set beaker xml class
        self.bxml = BeakerXML()

        # Create controller objects
        self._docker = DockerController(
            cname=self.host.bkr_name + '_' + str(uuid.uuid4())[:4]
        )
        self._ansible = AnsibleController(
            inventory=get_ansible_inventory_script(self.docker.name.lower())
        )

        # Run container
        try:
            self.docker.run_container(self._bkr_image, entrypoint='bash')
        except DockerControllerException as ex:
            self.logger.warn(ex)
            raise BeakerProvisionerException("Issue bringing up the container")

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
            src_file_path = os.path.join(self._data_folder, "assets", self.host.provider.credentials["keytab"])
            dest_file_path = os.path.join('/etc/beaker', self.host.provider.credentials["keytab"])

            # ensure destination path exists
            dest_dir = os.path.dirname(dest_file_path)
            ensure_dir_args = 'path={0} recurse=yes state=directory'.format(dest_dir)
            results = self.ansible.run_module(
                dict(name='ensure keytab folder', hosts=self.docker.cname, gather_facts='no',
                     tasks=[dict(action=dict(module='file', args=ensure_dir_args))])
            )
            self.ansible.results_analyzer(results['status'])
            if results['status'] != 0:
                raise BeakerProvisionerException("Error when creating keytab folder within"
                                                 " the container")

            # copy the keytab
            cp_args = 'src={0} dest={1} mode=0755'.format(src_file_path, dest_file_path)
            results = self.ansible.run_module(
                dict(name='copy file', hosts=self.docker.cname, gather_facts='no',
                     tasks=[dict(action=dict(module='copy', args=cp_args))])
            )
            self.ansible.results_analyzer(results['status'])
            if results['status'] != 0:
                raise BeakerProvisionerException("Error when copying file to container")

            # Modify the config file with correct data
            summary = "update beaker config - authmethod"
            replace_line = 'AUTH_METHOD=\"krbv\"'
            cmd = 'path={0} regexp=^AUTH_METHOD line={1}'.format(bkr_config, replace_line)
            self.lineinfile_call(summary, replace_line, cmd)

            summary = "update beaker config: keytab filename"
            replace_line = 'KRB_KEYTAB=\"{0}\"'.format(dest_file_path)
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

        results = self.ansible.run_module(
            dict(name='bkr authenticate', hosts=self.docker.cname, gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args=_cmd))])
        )

        self.ansible.results_analyzer(results['status'])
        if results['status'] != 0:
            raise BeakerProvisionerException("Authentication was not successful")

    def lineinfile_call(self, summary, replace_line, lineinfilecmd):
        self.logger.debug(lineinfilecmd)

        results = self.ansible.run_module(
            dict(name=summary, hosts=self.docker.cname, gather_facts='no',
                 tasks=[dict(action=dict(module='lineinfile', args=lineinfilecmd))])
        )

        if results['status'] != 0:
            raise BeakerProvisionerException("Error when {0}".format(summary))

    def gen_bkr_xml(self):
        """ generate the Beaker xml file from the host input
        """
        self.logger.info("Generating bkr XML")

        bkr_xml_file = os.path.join(self._data_folder,
                                    self._bkr_xml)

        host_desc = self.host.profile()

        # Set attributes for Beaker
        for key in host_desc:
            if key is not 'bkr_name' and key.startswith('bkr_'):
                xml_key = key.split("bkr_", 1)[1]
                if host_desc[key]:
                    try:
                        setattr(self.bxml, xml_key, host_desc[key])
                    except Exception as ex:
                        raise BeakerProvisionerException(ex)

        # Generate Beaker workflow-simple command
        try:
            self.bxml.generateBKRXML(bkr_xml_file, savefile=True)
        except Exception as ex:
            raise BeakerProvisionerException(ex)

        # Format command for container
        _cmd = self.bxml.cmd.replace('=', "\=")
        self.logger.debug(_cmd)

        # copy the ks file to container if set
        if self.bxml.kickstart != "":
            src_file_path = os.path.join(self._data_folder, "assets", self.bxml.kickstart)
            dest_full_path_file = '/tmp'

            cp_args = 'src={0} dest={1} mode=0755'.format(src_file_path, dest_full_path_file)

            results = self.ansible.run_module(
                dict(name='copy file', hosts=self.docker.cname, gather_facts='no',
                     tasks=[dict(action=dict(module='copy', args=cp_args))])
            )

            self.ansible.results_analyzer(results['status'])
            if results['status'] != 0:
                raise BeakerProvisionerException("Error copying kickstart file to container")

        # Run command on container
        results = self.ansible.run_module(
            dict(name='bkr workflow-simple', hosts=self.docker.cname, gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args=_cmd))])
        )

        # Process results and get xml from stdout
        self.ansible.results_analyzer(results['status'])

        if results['status'] != 0:
            raise BeakerProvisionerException("Issue generating Beaker XML")

        else:
            if len(results["callback"].contacted) == 1:
                parsed_results = results["callback"].contacted[0]["results"]
            else:
                raise BeakerProvisionerException("Unexpected Error creating XML")

            output = parsed_results["stdout"]

        # Generate Complete XML
        try:
            self.bxml.generateXMLDOM(bkr_xml_file, output, savefile=True)
        except Exception as ex:
            raise BeakerProvisionerException("Issue generating Beaker XML")

    def submit_bkr_xml(self):
        """ submit the beaker xml and retrieve Beaker JOBID
        """
        self.logger.info("Submitting bkr job")
        # copy the xml to container
        src_file_path = os.path.join(self._data_folder, self._bkr_xml)
        dest_full_path_file = '/tmp'

        cp_args = 'src={0} dest={1} mode=0755'.format(src_file_path, dest_full_path_file)

        results = self.ansible.run_module(
            dict(name='copy file', hosts=self.docker.cname, gather_facts='no',
                 tasks=[dict(action=dict(module='copy', args=cp_args))])
        )

        self.ansible.results_analyzer(results['status'])
        if results['status'] != 0:
            raise BeakerProvisionerException("Error when copying bkr xml to container")

        bkr_xml_path = os.path.join(dest_full_path_file, self._bkr_xml)
        _cmd = "bkr job-submit --xml {0}".format(bkr_xml_path)

        results = self.ansible.run_module(
            dict(name='bkr job submit', hosts=self.docker.cname, gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args=_cmd))])
        )

        self.ansible.results_analyzer(results['status'])

        if results['status'] != 0:
            raise BeakerProvisionerException("Error submitting Beaker job")
        else:
            if len(results["callback"].contacted) == 1:
                parsed_results = results["callback"].contacted[0]["results"]
            else:
                raise BeakerProvisionerException("Unexpected Error submitting job")

            output = parsed_results["stdout"]
            if output.find("Submitted:") != "-1":
                mod_output = output[output.find("Submitted:"):]
                # set the result as ascii instead of unicode
                self.host.bkr_job_id = mod_output[mod_output.find(
                    "[") + 2:mod_output.find("]") - 1].encode('ascii', 'ignore')
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

            results = self.ansible.run_module(
                dict(name='bkr job status', hosts=self.docker.cname, gather_facts='no',
                     tasks=[dict(action=dict(module='shell', args=_cmd))])
            )

            self.ansible.results_analyzer(results['status'])

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
                    # get machine info
                    self.get_machine_info(bkr_xml_output)
                    return
                elif status == "fail":
                    raise BeakerProvisionerException("Machine provision failed: {}".format(self.host.bkr_job_id))
                else:
                    raise BeakerProvisionerException("Unknown status from Beaker job")
        # timeout reached for Beaker job
        self.logger.error("Timeout reached waiting for Beaker job to complete.")
        self.cancel_job()
        raise BeakerProvisionerException("Timeout reached for Beaker job")

    def create(self):
        """Get a machine from Beaker based on the definition from the scenario.
        Steps:
        1.  authenticate
        2.  generate a beaker xml from the host data
        3.  submit a beaker job
        4.  watch for the beaker job to be complete -> return success or failed
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

        # copy ssh key to the machine
        if self.host.bkr_ssh_key:
            self.copy_ssh_key()

        try:
            # Stop/remove container
            self.docker.stop_container()
            self.docker.remove_container()
        except DockerControllerException as ex:
            raise BeakerProvisionerException(ex)

    def cancel_job(self):
        """Cancel a Beaker job """
        self.logger.info('Tearing down machines from %s', self.__class__)
        _cmd = "bkr job-cancel {0}".format(self.host.bkr_job_id)

        results = self.ansible.run_module(
            dict(name='bkr job cancel', hosts=self.docker.cname, gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args=_cmd))])
        )

        self.ansible.results_analyzer(results['status'])

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
            self.docker.stop_container()
            self.docker.remove_container()
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

    def get_machine_info(self, xmldata):
        """
        Used to parse the Beaker results xml and return machine information
        setting hostname and ip address

        :param xmldata: xmldata of a beaker job status
        :return: dictionary of job and install task statuses
        :raises BeakerProvisionerException: if results cannot be analyzed successfully
        """
        try:
            dom = parseString(xmldata)
        except Exception as e:
            raise BeakerProvisionerException("Error Issue reading xml data {}".format(e))

        tasklist = dom.getElementsByTagName('task')
        for task in tasklist:
            cname = task.getAttribute('name')

            if cname == '/distribution/install':
                hostname = task.getElementsByTagName('system')[0].getAttribute("value")
                addr = socket.gethostbyname(hostname)
                self.host.bkr_hostname = hostname.encode('ascii', 'ignore')
                self.host.bkr_ip_address = addr

    def copy_ssh_key(self):

        self.logger.info("Send keys over to the Beaker Nodes: {0} "
                         "{1}".format(self.host.bkr_ip_address, self.host.bkr_hostname))

        # setup prior to injecting ssh keys
        private_key = os.path.join(self._data_folder, "assets", self.host.bkr_ssh_key)

        try:
            # set permission of the private key
            os.chmod(private_key, stat.S_IRUSR | stat.S_IWUSR)

        except OSError as ex:
            raise BeakerProvisionerException("Error setting permission of ssh key - %s" % ex.message)

        # generate public key from private
        public_key = os.path.join(self._data_folder, "assets", self.host.bkr_ssh_key + ".pub")
        rsa_key = paramiko.RSAKey(filename=private_key)
        with open(public_key, 'w') as f:
            f.write('%s %s' % (rsa_key.get_name(), rsa_key.get_base64()))

        # send the key to the beaker machine
        ssh_con = paramiko.SSHClient()
        ssh_con.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh_con.connect(hostname=self.host.bkr_ip_address,
                            username=self.host.bkr_username,
                            password=self.host.bkr_password)
            sftp = ssh_con.open_sftp()
            sftp.put(public_key, '/root/.ssh/authorized_keys')
        except paramiko.SSHException as ex:
            raise BeakerProvisionerException('Error connecting to beaker machine - %s' % ex.message)
        except IOError as ex:
            raise BeakerProvisionerException('Error sending public key - %s' % ex.message)
        finally:
            ssh_con.close()

        self.logger.info("Successfully Sent key: {0}, "
                         "{1}".format(self.host.bkr_ip_address,
                                      self.host.bkr_hostname))

    def analyze_results(self, resultsdict):
        """
        return success, fail, or warn based on the job and install task statuses

        :param resultsdict: dictionary of job and install task statuses
        :return: action str [wait, success, or fail]
        :raises BeakerProvisionerException: if results cannot be analyzed successfully
        """
        # when is the job complete
        if resultsdict["job_result"].strip().lower() == "new" and \
           resultsdict["job_status"].strip().lower() in \
           ["new", "waiting", "queued", "scheduled", "processed", "installing"]:
            return "wait"
        elif resultsdict["install_result"].strip().lower() == "new" and \
                resultsdict["install_status"].strip().lower() in \
                ["new", "waiting", "queued", "scheduled", "running", "processed"]:
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


class BeakerXML():
    """ Class to generate Beaker XML file from input host yaml"""
    _op_list = ['!=', '<=', '>=', '=', '<', '>']

    def __init__(self):
        """Intialization of BeakerXML"""
        self._jobgroup = ""
        self._key_values = ""
        self._xmldom = ""
        self._arch = ""
        self._family = ""
        self._random = True
        self._component = ""
        self._cmd = ""
        self._runid = ""
        self._osvariant = ""
        self._product = ""
        self._retention_tag = ""
        self._whiteboard = ""
        self._packages = "None"
        self._tasks = "None"
        self._method = "nfs"
        self._reservetime = "86400"
        self._reservetime_always = ""
        self._host_requires_options = []
        self._distro_requires_options = []
        self._tasklist = []
        self._paramlist = []
        self._hrname = []
        self._hrvalue = []
        self._taskparam = []
        self._hrop = []
        self._drname = []
        self._drvalue = []
        self._drop = []
        self._repolist = []
        self._tag = ""
        self._priority = "Normal"  # Low, Medium, Normal, High, or Urgent
        self._distro = ""
        self._kernel_options = ""
        self._kernel_options_post = ""
        self._kickstart = ""
        self._ksmeta = ""
        self._removetask = False
        self._kdumpon = False
        self._ndumpon = False
        self._cclist = []
        self._virtmachine = False
        self._virtcapable = False
        self._ignore_panic = False

    def generateBKRXML(self, x, savefile=False):

        xmlfile = x

        # How will we generate the XML dom
        # Step 1: take all the values and pass it to bkr workflow simple to create a xml for us.
        file = open(xmlfile, 'w+')
        file.write("<?xml version='1.0' ?>\n")
        file.close()

        # Set virtual machine if configured
        if(self.virtual_machine):
            self.sethostrequires('hypervisor', '!=', "")

        # Set virtual capable if configured
        if(self.virt_capable):
            self.sethostrequires('system_type', '=', "Machine")
            self.setdistrorequires('distro_virt', '=', "")

        # Set User supplied host requires
        if (self.host_requires_options):
            for hro in self.host_requires_options:
                for hro_op in self._op_list:
                    if hro_op in hro:
                        hr_values = hro.split(hro_op)
                        self.sethostrequires(hr_values[0], hro_op, hr_values[1])
                        break

        # Set User supplied host requires
        if (self.distro_requires_options):
            for dro in self.distro_requires_options:
                for dro_op in self._op_list:
                    if dro_op in dro:
                        dr_values = dro.split(dro_op)
                        self.setdistrorequires(dr_values[0], dro_op, dr_values[1])
                        break

        # Set User supplied taskparam Only valid option currently is reservetime
        if (self.taskparam):
            for taskparam in self.taskparam:
                for tp_op in self._op_list:
                    if tp_op in taskparam:
                        tp_values = taskparam.split(tp_op)
                        tp_key = str(tp_values[0]).lower()
                        if tp_key == 'reservetime':
                            self.reservetime = tp_values[1]
                            break
                        else:
                            self.logger.warning(
                                "taskparam setting of %s not currently supported. Ingnoring" %
                                tp_key)
                            break

        # Set arch
        self.cmd += "bkr workflow-simple --arch " + self.arch

        # Set random if hostname not configured
        # if(self.bkr_random and not("hostname" in self.hrname)):
        #     self.cmd += " --random"

        # Generate Whiteboard Value if not specified
        if (self.whiteboard == ""):
            self.whiteboard = "Carbon:"
            if self.runid != "":
                self.whiteboard += " RunID:" + self.runid
            if self.component != "":
                self.whiteboard += " Component:" + self.component
            if self.distro != "":
                self.whiteboard += " " + self.distro
            else:
                self.whiteboard += " " + self.family + "," + self.tag
            self.whiteboard += " " + self.arch

        # Set family if configured and no distro specified
        if self.family != "" and self.distro == "":
            self.cmd += " --family " + self.family

        # Set variant if configured
        if self.variant != "":
            self.cmd += " --variant " + self.variant

        # Set retention tag
        if self.retention_tag != "":
            self.cmd += " --retention_tag " + self.retention_tag

        # Set whiteboard and method
        self.cmd += " --whiteboard '" + self.whiteboard + "'"
        self.cmd += " --method " + self.method

        # Set repos
        for repo in self.repolist:
            self.cmd += " --repo " + repo

        # Set email recipients
        for email in self.cclist:
            self.cmd += " --cc " + email

        # Set kernel options
        if(self.kernel_options != ""):
            self.cmd += " --kernel_options '" + " ".join(self.kernel_options) + "'"

        # Set post kernel options
        if(self.kernel_post_options != ""):
            self.cmd += " --kernel_options_post '" + " ".join(self.kernel_post_options) + "'"

        # Set kickstart file
        if (self.kickstart != ""):
            self.cmd += " --kickstart '" + "/tmp/" + self.kickstart + "'"

        # Set kick start meta options
        if (self.ksmeta != ""):
            self.cmd += " --ks-meta '" + " ".join(self.ksmeta) + "'"

        # Set product
        if(self.product != ""):
            self.cmd += " --product '" + self.product + "'"

        # Set debug and dryrun
        self.cmd += " --debug --dryrun"

        # Removal of --prettyxml option because it creates too many line breaks.
        # self.cmd += " --prettyxml"

        # Set packages to install
        if(self.packages != "None"):
            packagelist = self.packages.split(",")
            for package in packagelist:
                self.cmd += " --install " + package

        # Set tasks
        if(self.tasks != "None"):
            tasklist = self.tasks.split(",")
            for task in tasklist:
                self.cmd += " --task " + task
        else:
            # workaround for no tasks, add one task and delete it later
            self.cmd += " --task " + "/distribution/reservesys"
            self.removetask = True

        # Set tag if distro empty else distro
        if self.tag:
            self.cmd += " --tag " + self.tag

        if self.distro:
            self.cmd += " --distro " + self.distro

        # Set kdumo on
        if(self.kdump):
            self.cmd += " --kdump"

        # Set ndump on
        if(self.ndump):
            self.cmd += " --ndump"

        # Set ignore panic
        if(self.ignore_panic):
            self.cmd += " --ignore-panic"

        # Set job group
        if(self.jobgroup != ""):
            self.cmd += " --job-group " + self.jobgroup

        # Set priority
        self.cmd += " --priority " + self.priority

        # Set a key value hostrequires field
        for kv in self.key_values:
            self.cmd += " --keyvalue '" + kv + "'"

    def generateXMLDOM(self, x, xmldata, savefile=False):

        xmlfile = x

        file = open(xmlfile, 'w+')
        for xmlline in xmldata:
            file.write(xmlline)
        file.close()

        # parse the xml that was create and put it into a dom, so it can be modified
        dom1 = parse(xmlfile)
        # print dom1.toprettyxml()

        # Done with the xmlfile so it can be deleted
        if not savefile:
            os.remove(xmlfile)

        # If there were no tasks added delete the one placeholder task, which
        # was added because one task must be passed to simple workflow
        if(self.removetask):
            recipe_parent = dom1.getElementsByTagName('recipe')[0]
            tasklength = dom1.getElementsByTagName('task').length
            delete_index = tasklength - 1
            delete_element = dom1.getElementsByTagName('task')[delete_index]
            # print tasklength
            # print delete_index
            # print delete_element
            recipe_parent.removeChild(delete_element)

        # Step 2: Take the xml generated by beaker-workflow and put it into a DOM
        # Create host requires  elementi
        if len(dom1.getElementsByTagName('and')) > 1:
            hre_parent = dom1.getElementsByTagName('and')[1]
        else:
            temp_parent = dom1.getElementsByTagName('hostRequires')[0]
            # print temp_parent
            temp_parent.appendChild(dom1.createElement('and'))
            # print dom1.toprettyxml()
            hre_parent = dom1.getElementsByTagName('and')[1]

        dre_parent = dom1.getElementsByTagName('and')[0]

        # should check for an empty host requires first
        if self.hrname:
            for index, value in enumerate(self.hrname):
                # parse the value hostrequires key, first is op the rest is the value
                # print str(self.hrname[index])
                # print str(self.hrop[index])
                # print str(self.hrvalue[index])
                # Add all host requires here
                hre = dom1.createElement(str(self.hrname[index]))
                hre.attributes['op'] = str(self.hrop[index])
                hre.attributes['value'] = str(self.hrvalue[index])

                hre_parent.appendChild(hre)

        # should check for an empty distro requires first
        if self.drname:
            for index, value in enumerate(self.drname):
                # parse the value hostrequires key, first is op the rest is the value
                # Add all distro requires here
                dre = dom1.createElement(str(self.drname[index]))
                dre.attributes['op'] = str(self.drop[index])
                dre.attributes['value'] = str(self.drvalue[index])

                dre_parent.appendChild(dre)

        for index, val in enumerate(self.tasklist):
            paramlist = self.paramlist[index]

            te = dom1.createElement('task')
            te.attributes['name'] = val
            te.attributes['role'] = "STANDALONE"

            tpe = dom1.createElement('params')

            te_parent = dom1.getElementsByTagName("recipe")[0]

            # Add the task to the xml
            te_parent.appendChild(te)
            te.appendChild(tpe)

            keyindex = 0
            for key in paramlist:
                tpce = dom1.createElement('param')
                tpce.attributes['name'] = key

                tpce.attributes['value'] = paramlist[key]
                keyindex = keyindex + 1
                tpe.appendChild(tpce)

        if self.reservetime_always != "":
            te = dom1.createElement('task')
            te.attributes['name'] = "/distribution/reservesys"
            te.attributes['role'] = "STANDALONE"

            tpe = dom1.createElement('params')

            tpce = dom1.createElement('param')
            tpce.attributes['name'] = "RESERVETIME"
            tpce.attributes['value'] = str(self.reservetime_always)

            te_parent = dom1.getElementsByTagName("recipe")[0]

            # Add reservetime to the xml
            te_parent.appendChild(te)
            te.appendChild(tpe)
            tpe.appendChild(tpce)
        else:
            # Reserve if it fails
            te = dom1.createElement('task')
            te.attributes['name'] = "/distribution/reservesys"
            te.attributes['role'] = "STANDALONE"

            tpe = dom1.createElement('params')

            tpce = dom1.createElement('param')
            # tpce.attributes['name'] = "RESERVE_IF_FAIL"
            # tpce.attributes['value'] = "true"

            tpce2 = dom1.createElement('param')
            tpce2.attributes['name'] = "RESERVETIME"
            tpce2.attributes['value'] = str(self.reservetime)

            te_parent = dom1.getElementsByTagName("recipe")[0]

            # Add reservetime to the xml
            te_parent.appendChild(te)
            te.appendChild(tpe)
            tpe.appendChild(tpce)
            tpe.appendChild(tpce2)

        # set the completed DOM and return 0 for a successfull creation of the Beaker XML
        self.xmldom = dom1

        # Output updated file
        file = open(xmlfile, "wb")
        self.xmldom.writexml(file)
        file.close()

    @property
    def kernel_post_options(self):
        """Return the kernel post options."""
        return self._kernel_options_post

    @kernel_post_options.setter
    def kernel_post_options(self, options):
        """Set the the kernel post options.
        :param options: post kernel options"""
        self._kernel_options_post = options

    @property
    def kernel_options(self):
        """Return the beaker options."""
        return self._kernel_options

    @kernel_options.setter
    def kernel_options(self, options):
        """Set the beaker options.
        :param options: beakeroptions"""
        self._kernel_options = options

    @property
    def kickstart(self):
        """Return the kickstart file."""
        return self._kickstart

    @kickstart.setter
    def kickstart(self, ksfile):
        """Set kick start file.
        :param ksfile: kickstart file"""
        self._kickstart = ksfile

    @property
    def ksmeta(self):
        """Return the kick start meta data."""
        return self._ksmeta

    @ksmeta.setter
    def ksmeta(self, meta):
        """Set kick start meta data.
        :param meta: meta data"""
        self._ksmeta = meta

    @property
    def arch(self):
        """Return the arch."""
        return self._arch

    @arch.setter
    def arch(self, arch):
        """Set arch for resource.
        :param arch: Arch of resource"""
        self._arch = arch

    @property
    def family(self):
        """Return the family of resource."""
        return self._family

    @family.setter
    def family(self, family):
        """Set family of resource.
        :param family: Family of resource"""
        self._family = family

    @property
    def ignore_panic(self):
        """Return the ignore_panic setting."""
        return self._ignore_panic

    @ignore_panic.setter
    def ignore_panic(self, ipbool):
        """Set ignore panic.
        :param ipbool: ignore panic setting (bool)"""
        self._ignore_panic = ipbool

    @property
    def kdump(self):
        """Return the k dump on setting."""
        return self._kdumpon

    @kdump.setter
    def kdump(self, kbool):
        """Set k dump on.
        :param kbool: k dump on setting (bool)"""
        self._kdumpon = kbool

    @property
    def ndump(self):
        """Return the n dump on setting."""
        return self._ndumpon

    @ndump.setter
    def ndump(self, nbool):
        """Set n dump on.
        :param nbool: n dump on setting (bool)"""
        self._ndumpon = nbool

    @property
    def retention_tag(self):
        """Return the retention tag."""
        return self._retention_tag

    @retention_tag.setter
    def retention_tag(self, rtag):
        """Set retention tag.
        :param rtag: Retention tag"""
        self._retention_tag = rtag

    @property
    def tag(self):
        """Return the tag."""
        return self._tag

    @tag.setter
    def tag(self, tag):
        """Set tag.
        :param tag: Tag to set"""
        self._tag = tag

    @property
    def jobgroup(self):
        """Return the jobs group."""
        return self._jobgroup

    @jobgroup.setter
    def jobgroup(self, group):
        """Set the jobs group.
        :param group: Group to use for job"""
        self._jobgroup = group

    @property
    def component(self):
        """Return the component."""
        return self._component

    @component.setter
    def component(self, component):
        """Set component.
        :param component: Component"""
        self._component = component

    @property
    def distro(self):
        """Return the distro."""
        return self._distro

    @distro.setter
    def distro(self, distro):
        """Set the distro for resource.
        :param distro: Distro to set"""
        self._distro = distro

    @property
    def product(self):
        """Return the product."""
        return self._product

    @product.setter
    def product(self, product):
        """Set the product.
        :param product: Product to set"""
        self._product = product

    @property
    def method(self):
        """Return the method."""
        return self._method

    @method.setter
    def method(self, method):
        """ Set the method.
        :param method: Method to set"""
        self._method = method

    @property
    def priority(self):
        """Return the priority."""
        return self._priority

    @priority.setter
    def priority(self, priority):
        """Set priority.
        :param priority: Priority to set."""
        self._priority = priority

    @property
    def xmldom(self):
        """Return the xmldom."""
        return self._xmldom

    @xmldom.setter
    def xmldom(self, xmldom):
        """Set xmldom for class.
        :param xmldom"""
        self._xmldom = xmldom

    def get_xmldom_pretty(self):
        """Return the xmldom in pretty print format."""
        return self.xmldom.toprettyxml()

    @property
    def whiteboard(self):
        """Return the white board."""
        return self._whiteboard

    @whiteboard.setter
    def whiteboard(self, whiteboard):
        """Set whiteboard value.
        :param whiteboard: Value to set"""
        self._whiteboard = whiteboard

    @property
    def packages(self):
        """Return the packages."""
        return self._packages

    @packages.setter
    def packages(self, packages):
        """Set packages to install for job.
        :param packages: List of packages to install"""
        self._packages = packages

    @property
    def runid(self):
        """Return the runid of job ."""
        return self._runid

    @runid.setter
    def runid(self, runid):
        """Set runid.
        :param runid: runid of job"""
        self._runid = runid

    @property
    def tasks(self):
        """Return the tasks."""
        return self._tasks

    @tasks.setter
    def tasks(self, tasks):
        """Set tasks of job.
        :param tasks: List of tasks"""
        self._tasks = tasks

    @property
    def paramlist(self):
        """Return the parameter list to be used by tasks."""
        return self._paramlist

    @paramlist.setter
    def paramlist(self, paramdict):
        """Set parameter list.
        :param paramdict: Paramerters to be used by tasklist (dict)."""
        raise AttributeError('You cannot set paramlist directly. '
                             'Use settaskparam().')

    @property
    def key_values(self):
        """Return the key values."""
        return self._key_values

    @key_values.setter
    def key_values(self, key_values):
        """Set key values for job.
        :param key_values: Key values to set for job"""
        self._key_values = key_values

    @property
    def taskparam(self):
        """Return the taskparam list. Its a list of task parameters
           that will be applied to all tasks"""
        return self._taskparam

    @taskparam.setter
    def taskparam(self, taskparam):
        """Set List of taskparam.
        :param taskparam: List of task parameter that will be applied to all tasks"""
        self._taskparam = taskparam

    @property
    def tasklist(self):
        """Return the task list."""
        return self._tasklist

    @tasklist.setter
    def tasklist(self, task):
        """Set List of tasks for job.
        :param task: List of tasks"""
        raise AttributeError('You cannot set tasklist directly. '
                             'Use settaskparam().')

    @property
    def host_requires_options(self):
        """Return the host requires options."""
        return self._host_requires_options

    @host_requires_options.setter
    def host_requires_options(self, hr_values):
        """Set host requires opttions.
        :param hr_values: List of host requires options"""
        self._host_requires_options = hr_values

    @property
    def distro_requires_options(self):
        """Return the distro requires options."""
        return self._distro_requires_options

    @distro_requires_options.setter
    def distro_requires_options(self, dr_values):
        """Set distro requires options.
        :param dr_values: List of distro requires options"""
        self._distro_requires_options = dr_values

    @property
    def cclist(self):
        """Return the cc list."""
        return self._cclist

    @cclist.setter
    def cclist(self, email):
        """Set cc list for job.
        :param email: List of emails to cc"""
        self._cclist.append(email)

    @property
    def hrname(self):
        """Return the host requires names."""
        return self._hrname

    @hrname.setter
    def hrname(self, hr_name):
        """Raises an exception when trying to set the host requires name
        directly. Must use sethostrequires.
        :param value: The host requires name.
        """
        raise AttributeError('You cannot set Hostrequires name directly. '
                             'Use sethostrequires().')

    @property
    def hrop(self):
        """Return the host requires operations"""
        return self._hrop

    @hrop.setter
    def hrop(self, hr_op):
        """Raises an exception when trying to set the host requires op
        directly. Must use sethostrequires.
        :param value: The host requires operation.
        """
        raise AttributeError('You cannot set Hostrequires operation directly. '
                             'Use sethostrequires().')

    @property
    def hrvalue(self):
        """Return the host requires values"""
        return self._hrvalue

    @hrvalue.setter
    def hrvalue(self, hr_value):
        """Raises an exception when trying to set the host requires value
        directly. Must use sethostrequires.
        :param value: The host requires value.
        """
        raise AttributeError('You cannot set Hostrequires value directly. '
                             'Use sethostrequires().')

    @property
    def drname(self):
        """Return distro requires names"""
        return self._drname

    @drname.setter
    def drname(self, dr_name):
        """Raises an exception when trying to set the Distro requires name
        directly. Must use setdistrorequires.
        :param value: The disto requires name.
        """
        raise AttributeError('You cannot set Distrorequires name directly. '
                             'Use setdistrorequires().')

    @property
    def drop(self):
        """Return distro requires operations"""
        return self._drop

    @drop.setter
    def drop(self, dr_op):
        """Raises an exception when trying to set the distro requires op
        directly. Must use setdistrorequires.
        :param value: The distro requires operation.
        """
        raise AttributeError('You cannot set Distrorequires operation directly. '
                             'Use setdistrorequires().')

    @property
    def drvalue(self):
        """Return distro requires values"""
        return self._drvalue

    @drvalue.setter
    def drvalue(self, dr_value):
        """Raises an exception when trying to set the distro requires value
        directly. Must use setdistrorequires.
        :param value: The distro requires value.
        """
        raise AttributeError('You cannot set Distroequires value directly. '
                             'Use setdistrorequires().')

    @property
    def repolist(self):
        """Return the repos list."""
        return self._repolist

    @repolist.setter
    def repolist(self, repo):
        """Set the repos for the resource.
        :param repo: repo to add to list"""
        self._repolist.append(repo)

    @property
    def cmd(self):
        """Return the bkr cmd to create xml."""
        return self._cmd

    @cmd.setter
    def cmd(self, cmd):
        """Set bkr cmd to run to create xml.
        :param cmd: bkr xml creation cmd"""
        self._cmd = cmd

    @property
    def bkr_random(self):
        """Return the random setting of job."""
        return self._random

    @bkr_random.setter
    def bkr_random(self, rbool):
        """Set random setting of job.
        :param rbool: random setting (bool)"""
        self._random = rbool

    @property
    def virtual_machine(self):
        """Return the virtual machine setting."""
        return self._virtmachine

    @virtual_machine.setter
    def virtual_machine(self, vbool):
        """Set virtual machine setting.
        :param vbool: virtual machine setting (bool)"""
        self._virtmachine = vbool

    @property
    def virt_capable(self):
        """Return the virt capable setting."""
        return self._virtcapable

    @virt_capable.setter
    def virt_capable(self, vbool):
        """Set virt capable.
        :param vbool: virtual capable setting (bool)"""
        self._virtcapable = vbool

    @property
    def variant(self):
        """Return the variant."""
        return self._osvariant

    @variant.setter
    def variant(self, osvariant):
        """Set variant of resource.
        :param osvariant: variant of resource"""
        self._osvariant = osvariant

    @property
    def reservetime(self):
        """Return the reserve time."""
        return self._reservetime

    @reservetime.setter
    def reservetime(self, reservetime):
        """Set reserve time.
        :param reservetime: time to reserve resource for (seconds)"""
        self._reservetime = reservetime

    @property
    def reservetime_always(self):
        """Return the reserve time always setting."""
        return self._reservetime_always

    @reservetime_always.setter
    def reservetime_always(self, reservetime_always):
        """Set reserve time always.
        :param reservetime_always: time setting"""
        self._reservetime_always = reservetime_always

    def isRandom(self):
        """Returns if random"""
        return self._random

    def isVirtEnable(self):
        """Returns if virtual machine"""
        return self._virtmachine

    def isVirtCapable(self):
        """Returns if virtual capable"""
        return self._virtcapable

    def getXMLtext(self):
        """Returns pretty print format of xml"""
        return self.xmldom.toprettyxml()

    def sethostrequires(self, hr_name, hr_op, hr_value):
        """Set host requires parameters.
        :param hr_name: Host requires name
        :param hr_op: Host requires operation
        :param hr_value: Host requires value"""
        if hr_name not in self._hrname:
            self._hrname.append(hr_name)
            self._hrop.append(hr_op)
            self._hrvalue.append(hr_value)
        else:
            updateindex = self._hrname.index(hr_name)
            self._hrop[updateindex] = hr_op
            self._hrvalue[updateindex] = hr_value

    def setdistrorequires(self, dr_name, dr_op, dr_value):
        """Set the distro requires parameters.
        :param dr_name: Distro requires name
        :param dr_op: Distro requires operation
        :param dr_value: Distro requires value"""
        if dr_name not in self._drname:
            self._drname.append(dr_name)
            self._drop.append(dr_op)
            self._drvalue.append(dr_value)
        else:
            updateindex = self._drname.index(dr_name)
            self._drop[updateindex] = dr_op
            self._drvalue[updateindex] = dr_value

    def settaskparam(self, task, paramdict):
        self.tasklist.append(task)
        self.paramlist.append(paramdict)

    def set(self, param, value):
        """Set parameters value.
        :param param: Parameter to set
        :value value: Value of parameter
        :returns: 0 on success 1 if failed"""
        if param == "variant":
            self.variant(value)
        elif param == "priority":
            self.priority(value)
        elif param == "family":
            self.family(value)
        elif param == "retentiontag":
            self.retentiontag(value)
        elif param == "whiteboard":
            self.whiteboard(value)
        elif param == "packages":
            self.packages(value)
        elif param == "tasks":
            self.tasks(value)
        elif param == "tag":
            self.tag(value)
        elif param == "distro":
            self.distro(value)
        elif param == "arch":
            self.arch(value)
        elif param == "reservetime":
            self.reservetime(value)
        elif param == "method":
            self.method(value)
        elif param == "component":
            self.component(value)
        elif param == "product":
            self.product(value)
        elif param == "kernel_options":
            self.kernel_options(value)
        elif param == "kernel_post_options":
            self.kernel_post_options(value)
        elif param == "cclist":
            self.cclist(value)
        else:
            return(1)
        return(0)
