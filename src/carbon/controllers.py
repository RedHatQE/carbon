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
    carbon.controllers

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from collections import namedtuple

from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory import Inventory
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible.vars import VariableManager
from docker import DockerClient
from docker.errors import APIError, ContainerError, NotFound, ImageNotFound

from .core import CarbonController, CarbonException


class CarbonCallback(CallbackBase):
    """Carbon's custom Ansible callback class. It handles storing all task
    results (as they finish) into one object to be used later for further
    parsing.
    """

    def __init__(self):
        """Constructor."""
        super(CarbonCallback, self).__init__()
        self.contacted = []
        self.unreachable = False

    def v2_runner_on_ok(self, result):
        """Store ok results."""
        CallbackBase.v2_runner_on_ok(self, result)
        self.contacted.append(
            {
                'host': result._host.get_name(),
                'success': True,
                'results': result._result
            }
        )

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """Store failed results."""
        CallbackBase.v2_runner_on_failed(
            self, result, ignore_errors=ignore_errors)
        self.contacted.append(
            {
                'host': result._host.get_name(),
                'success': False,
                'results': result._result
            }
        )

    def v2_runner_on_unreachable(self, result):
        """Store unreachable results."""
        CallbackBase.v2_runner_on_unreachable(self, result)
        self.unreachable = True


class AnsibleController(CarbonController):
    """Ansible controller class.

    This is carbons Ansible controller class to drive remote machine
    configuration and management.
    """

    def __init__(self, inventory=None):
        """Constructor.

        When the Ansible worker class is instantiated, it will perform the
        following tasks:

        * Initialize required Ansible objects.

        :param inventory: The inventory host file.
        """
        super(AnsibleController, self).__init__()
        self.variable_manager = VariableManager()
        self.loader = DataLoader()
        self.callback = CarbonCallback()
        self.ansible_inventory = inventory
        self.inventory = None

        # Module options
        self.module_options = namedtuple(
            'Options', ['connection',
                        'module_path',
                        'forks',
                        'become',
                        'become_method',
                        'become_user',
                        'check',
                        'remote_user',
                        'private_key_file']
        )

        # Playbook options
        self.playbook_options = namedtuple(
            'Options', ['connection',
                        'module_path',
                        'forks',
                        'become',
                        'become_method',
                        'become_user',
                        'check',
                        'listtags',
                        'listtasks',
                        'listhosts',
                        'syntax',
                        'remote_user',
                        'private_key_file']
        )

    def set_inventory(self):
        """Instantiate the inventory class with the inventory file in-use."""
        self.inventory = Inventory(
            loader=self.loader,
            variable_manager=self.variable_manager,
            host_list=self.ansible_inventory
        )
        self.variable_manager.set_inventory(self.inventory)

    def run_module(self, play_source, remote_user="root", become=False,
                   become_method="sudo", become_user="root",
                   private_key_file=None):
        """Run an Ansible module.

        Example play source:
        dict(
            name="Ansible Play",
            hosts=192.168.1.1,
            gather_facts='no',
            tasks=[
                dict(action=dict(module='ping'), register='shell_out')
            ]
        )

        :param play_source: Play to be run.
        :param remote_user: Connect as this user.
        :param become: Whether to run as sudoer.
        :param become_method: Method to use for become.
        :param become_user: User to become.
        :param private_key_file: SSH private key for authentication.
        :return: A dict of Ansible return code and callback object
        """
        # Instantiate callback class
        self.callback = CarbonCallback()

        # Set inventory file
        self.set_inventory()

        # Define ansible options
        options = self.module_options(
            connection='smart',
            module_path='',
            forks=100,
            become=become,
            become_method=become_method,
            become_user=become_user,
            check=False,
            remote_user=remote_user,
            private_key_file=private_key_file
        )

        # Load the play
        play = Play().load(
            play_source,
            variable_manager=self.variable_manager,
            loader=self.loader
        )

        # Run the tasks
        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=options,
                passwords={},
                stdout_callback=self.callback
            )
            result = tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()

        return dict(status=result, callback=self.callback)

    def run_playbook(self, playbook, extra_vars=None, become=False,
                     become_method="sudo", become_user="root",
                     remote_user="root", private_key_file=None):
        """Run an Ansible playbook.

        :param playbook: Playbook to call
        :param extra_vars: Additional variables for playbook
        :param become: Whether to run as sudoer
        :param become_method: Method to use for become
        :param become_user: User to become to run playbook call
        :param remote_user: Connect as this user
        :param private_key_file: SSH private key for authentication
        :return: A dict of Ansible return code and callback object
        """
        # Instantiate callback class
        self.callback = CarbonCallback()

        # Set inventory file
        self.set_inventory()

        # Define ansible options
        options = self.playbook_options(
            connection='smart',
            module_path='',
            forks=100,
            become=become,
            become_method=become_method,
            become_user=become_user,
            check=False,
            listtags=False,
            listtasks=False,
            listhosts=False,
            syntax=False,
            remote_user=remote_user,
            private_key_file=private_key_file
        )

        # Set additional variables for use by playbook
        if extra_vars is not None:
            self.variable_manager.extra_vars = extra_vars

        # Instantiate playbook executor object
        runner = PlaybookExecutor(
            playbooks=[playbook],
            inventory=self.inventory,
            variable_manager=self.variable_manager,
            loader=self.loader,
            options=options,
            passwords={}
        )

        # Set stdout_callback to use custom callback class
        runner._tqm._stdout_callback = self.callback

        # Run playbook
        result = runner.run()

        return dict(status=result, callback=self.callback)

    def results_analyzer(self, status):
        """Results analyzer.

        This is a simple method that performs results analzying. It is good to
        use when you need to log the standard error/output based on the
        return code from ansible call.

        :param status: Status code of ansible call
        """
        for item in self.callback.contacted:
            _stderr = item['results']['stderr']
            _stdout = item['results']['stdout']
            if status != 0:
                if _stderr:
                    self.logger.info('Standard error:')
                    self.logger.error(item['results']['stderr'])
            if _stdout:
                self.logger.info('Standard output:')
                self.logger.info(item['results']['stdout'])


class DockerControllerException(CarbonException):
    """Base class for docker controller exceptions."""
    pass


class DockerController(CarbonController):
    """Docker controller class.

    The docker controller interfaces with the docker service. It handles
    actions with containers.
    """

    def __init__(self):
        """Constructor.

        Instantiates docker client class.
        """
        super(DockerController, self).__init__()
        self.client = DockerClient()

    def run_container(self, name, image, command=None, entrypoint=None,
                      volumes=None):
        """Run a command in new container.

        :param name: Name for the container.
        :param image: Image to create container.
        :param command: Command to run inside the container.
        :param entrypoint: Override the default entrypoint.
        :param volumes: Volumes (dict form) to mount inside container. You
            can declare multiple volumes.
            {'/home/user': {'bind': '/tmp', 'mode': 'rw'}, ..}
        :return: A dict of the return code and ansible callback object.
        """
        status = self.get_container_status(name)
        if status == 'running':
            raise DockerControllerException(
                'Container %s is %s! Re-use container.' % (name, status))
        elif status == 'exited':
            self.logger.warn('Container %s is %s! Remove container before '
                             'starting a new one.', name, status)
            self.remove_container(name)

        try:
            self.client.containers.run(
                image,
                name=name,
                detach=True,
                tty=True,
                entrypoint=entrypoint,
                command=command,
                volumes=volumes
            )
        except (APIError, ContainerError, ImageNotFound) as ex:
            raise DockerControllerException(ex)
        self.logger.info('Successfully started container: %s', name)

    def remove_container(self, name):
        """Remove a container.

        :param name: Name for the container.
        """
        container = self.get_container(name)

        try:
            container.remove()
        except APIError as ex:
            raise DockerControllerException(ex)
        self.logger.info('Container %s successfully removed.', name)

    def start_container(self, name):
        """Start a stopped container.

        :param name: Name of the container.
        """
        status = self.get_container_status(name)
        if status != 'exited':
            self.logger.warn('Container %s is not stopped (status=%s).', name,
                             status)
            return

        container = self.get_container(name)

        try:
            container.start()
        except APIError as ex:
            raise DockerControllerException(ex)
        self.logger.info('Container %s successfully started.', name)

    def stop_container(self, name):
        """Stop a running container.

        :param name: Name for the container.
        """
        status = self.get_container_status(name)
        if status != 'running':
            self.logger.warn('Container %s is not running (status=%s).', name,
                             status)
            return

        container = self.get_container(name)

        try:
            container.stop()
        except APIError as ex:
            raise DockerControllerException(ex)
        self.logger.info('Container: %s successfully stopped.', name)

    def pull_image(self, name, tag='latest'):
        """Pull an image from a registry.

        :param name: Name of the image.
        :param tag: Name of the tag for the image.
        """
        try:
            self.client.images.pull(name, tag=tag)
        except APIError as ex:
            raise DockerControllerException(ex)
        self.logger.info('Successfully pulled image %s:%s.', name, tag)

    def remove_image(self, name, tag='latest'):
        """Remove an image.

        :param name: Name of the image.
        :param tag: Tag for the image.
        """
        _image = '%s:%s' % (name, tag)

        try:
            self.client.images.remove(image=_image)
        except APIError as ex:
            raise DockerControllerException(ex)
        self.logger.info('Successfully removed image %s.', _image)

    def get_container_status(self, name):
        """Get the status for the name of the container given.

        :param name: Name of the container.
        :return: Status of the container.
        """
        try:
            container = self.client.containers.get(name)
            status = str(container.status)
        except (APIError, NotFound):
            status = None
        return status

    def get_container(self, name):
        """Check to see if the container name given is already running.

        :param name: Name of the container.
        :return: A boolean, true = alive, false = not alive.
        """
        try:
            container = self.client.containers.get(name)
        except (APIError, NotFound):
            raise DockerControllerException('Container %s not found.' % name)
        return container

    def get_image(self, name):
        """Check to see if the image name given already exists.

        The image name can be given with or without a tag:
            - fedora or fedora:25

        :param name: Name of the image.
        :return: A boolean, true = exists, false = not exist.
        """
        found = True
        try:
            self.client.images.get(name)
        except (APIError, ImageNotFound):
            found = False
        return found
