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
    carbon.constants

    A module containing all constants used throughout the carbon code base.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.

"""
import os
import re
import tempfile

CARBON_ROOT = os.path.join("/".join(os.path.dirname(__file__).split('/')[0:-2]))
SCENARIO_SCHEMA = os.path.join(os.path.dirname(__file__), "files", "schema.yml")
SCHEMA_EXT = os.path.join(os.path.dirname(__file__), 'files/extensions.py')
DATA_FOLDER = tempfile.gettempdir()

TASKLIST = [
    "validate",
    "provision",
    "orchestrate",
    "execute",
    "report",
    "cleanup"
]

NOTIFYSTATES = [
    'on_start',
    'on_complete',
    'on_demand'
]

TASK_LOGLEVEL_CHOICES = [
    "debug",
    "info"
]

PROVISIONERS = {
    "beaker": ["beaker-client", "linchpin-wrapper"],
    "openstack": ["openstack-libcloud", "linchpin-wrapper"],
    "aws": "linchpin-wrapper",
    "libvirt": "linchpin-wrapper",
    "asset": "asset-provisioner"
}

HOST_UPDATE_FIELDS = ["app_name", "routes", "ip_address", "hostname"]

RESULTS_FILE = "results.yml"

# Rule for Carbon hosts naming convention
RULE_HOST_NAMING = re.compile('[\\W]+')

# Default orchestrator
ORCHESTRATOR = 'ansible'

# Default executor
EXECUTOR = 'runner'

# Default task concurrency settings
DEFAULT_TASK_CONCURRENCY = dict(VALIDATE='True',
                                PROVISION='True',
                                ORCHESTRATE='False',
                                EXECUTE='False',
                                REPORT='True',
                                CLEANUP='False')

# Default config
DEFAULT_CONFIG = {
    'ANSIBLE_LOG_REMOVE': True,
    'DATA_FOLDER': DATA_FOLDER,
    'LOG_LEVEL': 'info',
    'RESOURCE_CHECK_ENDPOINT': '',
    'INVENTORY_FOLDER': '',
    'RESULTS_FOLDER': os.path.join(DATA_FOLDER, '.results'),
    'TASK_CONCURRENCY': DEFAULT_TASK_CONCURRENCY,
    'TOGGLES': [],
    'CREDENTIALS': [],
    'SETUP_LOGGER': [],
    'NOTIFICATIONS': []
}

# Default config sections
DEFAULT_CONFIG_SECTIONS = ['defaults', 'credentials', 'orchestrator', 'feature_toggles', 'importer',
                           'task_concurrency', 'setup_logger', 'executor', 'provisioner']

# options on how credentials can be set
SET_CREDENTIALS_OPTIONS = ['config', 'scenario']

# Default importer
IMPORTER = 'artifact-importer'

# Default feature toggle for provisioner plugins
DEFAULT_FEATURE_TOGGLE_HOST_PLUGIN = dict(name='host', plugin_implementation='True')

# Default logging config for carbon
# Need this because ansible 2.9 setups a logging basicConfig which 'hijacks' the carbon loggers
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': ''
        },
        'debug': {
            'format': ''
        },
    },
    'filters': {
        'exception': {
            '()': 'carbon.core.LoggerMixin.ExceptionFilter',
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'formatter': 'default',
            'filename': '',
            'encoding': 'utf-8',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'filters': ['exception']
        }
    },
    'loggers': {
        'blaster': {'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': False},
        'lp_console': {'handlers': ['console', 'file'],
                       'level': 'INFO',
                       'propagate': False},
    }
}
