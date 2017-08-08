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
    carbon.signals

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from flask.signals import Namespace


_signals = Namespace()

#
# Resources signals
#
host_created = _signals.signal('host-created')
action_created = _signals.signal('action-create')
execute_created = _signals.signal('execute-create')
scenario_created = _signals.signal('scenario-created')

#
# Provisioners signals
#
provision_create_started = _signals.signal('provision-create-started')
provision_create_finished = _signals.signal('provision-create-finished')
provision_delete_started = _signals.signal('provision-delete-started')
provision_delete_finished = _signals.signal('provision-delete-finished')

prov_linchpin_initiated = _signals.signal('prov-linchpin-initialized')
prov_ciosp_initiated = _signals.signal('prov-ciosp-initialized')

#
# Openstack provisioner signals
#
prov_openstack_initiated = _signals.signal('prov-openstack-initialized')
prov_openstack_bootnode_started = _signals.signal('prov-openstack-bootnode-started')
prov_openstack_bootnode_finished = _signals.signal('prov-openstack-bootnode-finished')
prov_openstack_overlimit = _signals.signal('prov-openstack-overlimit')

#
# Beaker provisioner signals
#
prov_beaker_initiated = _signals.signal('prov-beaker-initialized')
prov_beaker_xml_submit_started = _signals.signal('prov-beaker-xml-submit-started')
prov_beaker_xml_submit_finished = _signals.signal('prov-beaker-xml-submit-finished')
prov_beaker_wait_job_started = _signals.signal('prov-beaker-wait-started')
prov_beaker_wait_job_finished = _signals.signal('prov-beaker-wait-finished')

#
# Openshift provisioner signals
#
prov_openshift_initiated = _signals.signal('prov-openshift-initialized')
prov_openshift_newapp_started = _signals.signal('prov-openshift-newapp-started')
prov_openshift_newapp_finished = _signals.signal('prov-openshift-newapp-finished')
prov_openshift_app_updated = _signals.signal('prov-openshift-app-updated')

#
# Tasks signals
#
task_validation_started = _signals.signal('task-validation-started')
task_validation_finished = _signals.signal('task-validation-finished')
task_provision_started = _signals.signal('task-provision-started')
task_provision_finished = _signals.signal('task-provision-finished')
task_orchestrate_started = _signals.signal('task-orchestrate-started')
task_orchestrate_finished = _signals.signal('task-orchestrate-finished')
task_report_started = _signals.signal('task-report-started')
task_report_finished = _signals.signal('task-report-finished')
task_cleanup_started = _signals.signal('task-cleanup-started')
task_cleanup_finished = _signals.signal('task-cleanup-finished')
task_execute_started = _signals.signal('task-execute-started')
task_execute_finished = _signals.signal('task-execute-finished')
