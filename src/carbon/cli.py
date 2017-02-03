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
    carbon.cli

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import os

import click

from . import __version__
from .carbon import Carbon

_VERBOSITY = 0

_TASK_CHOICES = ['validate',
                 'check',
                 'provision',
                 'config',
                 'install',
                 'test',
                 'report',
                 'teardown']

_TASK_CLEANUP_CHOICES = ['always',
                         'never',
                         'pronto',
                         'on_success',
                         'on_failure']

_TASK_LOGLEVEL_CHOICES = ['debug',
                          'info',
                          'warning',
                          'error',
                          'critical']


def print_version(ctx, param, value):
    """Print carbon version for the command line"""
    if not value or ctx.resilient_parsing:
        return
    click.echo('%s' % __version__)
    ctx.exit()


def print_header():
    click.echo("-" * 50)
    click.echo("Carbon Framework v%s" % __version__)
    click.echo("Copyright (C) 2017 Red Hat, Inc.")
    click.echo("-" * 50)


@click.group()
@click.option("--version", is_flag=True, callback=print_version,
              expose_value=False, is_eager=True,
              help="Show version and exit.")
@click.option("-v", "--verbose", count=True,
              help="Add verbosity to the commands.")
def cli(verbose):
    """
    This is Carbon command line utility.
    """
    global _VERBOSITY
    if verbose:
        _VERBOSITY = verbose
        click.echo('\n--- Verbose mode ON (verbosity %s)---\n' % verbose)


@cli.command()
def create():
    """Create a scenario configuration."""
    raise NotImplementedError


@cli.command()
def validate():
    """Validate a scenario configuration."""
    raise NotImplementedError


@cli.command()
@click.option("--task",
              default=None,
              type=click.Choice(_TASK_CHOICES),
              help="Select a specific task to run. Default all tasks run.")
@click.option("-s", "--scenario",
              default=None,
              help="Scenario definition file to be executed.")
@click.option("-c", "--cleanup",
              type=click.Choice(_TASK_CLEANUP_CHOICES),
              default='always',
              help="taskrunner cleanup behaviour. Default: 'always'")
@click.option("--log-level",
              type=click.Choice(_TASK_LOGLEVEL_CHOICES),
              default='info',
              help="Select logging level. Default is 'INFO'")
@click.pass_context
def run(ctx, task, scenario, cleanup, log_level):
    """
    Run a carbon scenario, given the scenario YAML file configuration.
    """
    print_header()

    if os.path.isfile(scenario):
        scenario = os.path.abspath(scenario)
    else:
        click.echo('You have to provide a valid scenario file.')
        ctx.exit()

    # Create a new carbon compound
    cbn = Carbon(__name__)

    # Read configuration first from etc, then overwrite from CARBON_SETTINGS
    # environment variable and the look gor a carbon.cfg from within the
    # directory where this command is running from.
    cbn.config.from_pyfile('/etc/carbon/carbon.cfg', silent=True)
    cbn.config.from_envvar('CARBON_SETTINGS', silent=True)
    cbn.config.from_pyfile(os.path.join(os.getcwd(), 'carbon.cfg'), silent=True)

    # This is the easiest way to configure a full scenario.
    cbn.load_from_yaml(scenario)

    # The scenario will start the main pipeline and run through the ordered list
    # of pipelines. See :function:`~carbon.Carbon.run` for more details.
    cbn.run()


@cli.command('help')
@click.option("--task",
              type=click.Choice(['provision', 'config', 'install', 'test',
                                 'report', 'teardown']),
              help="Display helpful information about a task.")
def carbon_help():
    """
    Display helpful information about Carbon
    internals.
    """
    raise NotImplementedError
