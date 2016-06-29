# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Red Hat, Inc.
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

    :copyright: (c) 2016 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from . import __version__
import click

_VERBOSITY = 0


def print_version(ctx, param, value):
    """Print carbon version for the command line"""
    if not value or ctx.resilient_parsing:
        return
    click.echo('%s' % __version__)
    ctx.exit()


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
@click.option("--stopbefore",
              type=click.Choice(['config', 'install', 'test',
                                 'report', 'teardown']),
              help="Stop before the specified task is executed.")
@click.option("--stopafter",
              type=click.Choice(['provision', 'config', 'install', 'test',
                                 'report']),
              help="Stop after the specified task is executed.")
@click.option("--only",
              type=click.Choice(['provision', 'config', 'install', 'test',
                                 'report', 'teardown']),
              help="Stop after the specified task is executed.")
def run():
    """Run a scenario."""
    raise NotImplementedError


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
