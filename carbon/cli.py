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
import click
import os
import yaml

from . import __version__
from .carbon import Carbon
from .constants import TASKLIST, TASK_LOGLEVEL_CHOICES, LOGTYPE_CHOICES
from .helpers import template_render

_VERBOSITY = 0


def print_header():
    click.echo("-" * 50)
    click.echo("Carbon Framework v%s" % __version__)
    click.echo("Copyright (C) 2017 Red Hat, Inc.")
    click.echo("-" * 50)


@click.group()
@click.option("-v", "--verbose", count=True,
              help="Add verbosity to the commands.")
@click.version_option()
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
@click.option("-s", "--scenario",
              default=None,
              help="Scenario definition file to be executed.")
@click.option("-d", "--data-folder",
              default=None,
              help="Scenario workspace path.")
@click.option("--log-level",
              type=click.Choice(TASK_LOGLEVEL_CHOICES),
              default='info',
              help="Select logging level. Default is 'INFO'")
@click.pass_context
def validate(ctx, scenario, data_folder, log_level):
    """Validate a scenario configuration."""
    # Make sure the file exists and gets its absolute path
    if os.path.isfile(scenario):
        scenario = os.path.abspath(scenario)
    else:
        click.echo('You have to provide a valid scenario file.')
        ctx.exit()

    # apply templating before loading the data
    scenario_data = template_render(scenario, os.environ)

    # Create a new carbon compound
    cbn = Carbon(__name__, log_level=log_level, data_folder=data_folder)

    # This is the easiest way to configure a full scenario.
    cbn.load_from_yaml(scenario_data)

    # The scenario will start the main pipeline and run through the ordered list
    # of pipelines. See :function:`~carbon.Carbon.run` for more details.
    cbn.run(tasklist=["validate"])


@cli.command()
@click.option("-t", "--task",
              default=None,
              type=click.Choice(TASKLIST),
              multiple=True,
              help="Select a specific task to run. Default all tasks run.")
@click.option("-s", "--scenario",
              default=None,
              help="Scenario definition file to be executed.")
@click.option("-d", "--data-folder",
              default=None,
              help="Scenario workspace path.")
@click.option("-a", "--assets-path",
              default=None,
              help="Scenario workspace path.")
@click.option("--log-level",
              type=click.Choice(TASK_LOGLEVEL_CHOICES),
              default='info',
              help="Select logging level. Default is 'INFO'")
@click.pass_context
def run(ctx, task, scenario, log_level, data_folder, assets_path):
    """
    Run a carbon scenario, given the scenario YAML file configuration.
    """
    print_header()

    # Make sure the file exists and gets its absolute path
    if scenario is not None and os.path.isfile(scenario):
        scenario = os.path.abspath(scenario)
    else:
        click.echo('You have to provide a valid scenario file.')
        ctx.exit()

    # apply templating before loading the data
    scenario_data = template_render(scenario, os.environ)

    # Verify the updated data is valid
    try:
        yaml.safe_load(scenario_data)
    except yaml.YAMLError as ex:
        click.echo('Error:\n%s\n%s' % (ex.problem, ex.problem_mark))
        ctx.exit()

    # Ensure assets_path is set. If user does not set via client command
    # line it will set the same path where the scenario is
    if assets_path is None:
        assets_path = os.path.dirname(scenario)

    # Create a new carbon compound
    cbn = Carbon(
        __name__,
        log_level=log_level,
        data_folder=data_folder,
        assets_path=assets_path
    )

    # This is the easiest way to configure a full scenario.
    cbn.load_from_yaml(scenario_data)

    # Setup the list of tasks to run
    if not task:
        task = TASKLIST
    else:
        task = list(task)

    # The scenario will start the main pipeline and run through the task
    # pipelines declared. See :function:`~carbon.Carbon.run` for more details.
    cbn.run(tasklist=task)


@cli.command('help')
@click.option("--task",
              type=click.Choice(['create', 'config', 'install', 'test',
                                 'report', 'teardown']),
              help="Display helpful information about a task.")
def carbon_help():
    """
    Display helpful information about Carbon
    internals.
    """
    raise NotImplementedError
