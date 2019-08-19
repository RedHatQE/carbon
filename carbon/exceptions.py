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
    carbon.exceptions

    Module containing all custom exceptions used by carbon.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""


class CarbonError(Exception):
    """Carbon's base Exception class"""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(CarbonError, self).__init__(message)
        self.message = message


class CarbonTaskError(CarbonError):
    """Carbon's task base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(CarbonTaskError, self).__init__(message)


class CarbonResourceError(CarbonError):
    """Carbon's resource base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(CarbonResourceError, self).__init__(message)


class CarbonProvisionerError(CarbonError):
    """Carbon's provisioner base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(CarbonProvisionerError, self).__init__(message)


class CarbonProviderError(CarbonError):
    """Carbon's provider base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(CarbonProviderError, self).__init__(message)


class CarbonOrchestratorError(CarbonError):
    """Carbon's orchestrator base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(CarbonOrchestratorError, self).__init__(message)


class HelpersError(Exception):
    """Base class for carbon helpers exceptions."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(HelpersError, self).__init__(message)


class LoggerMixinError(CarbonError):
    """Carbon's logger mixin base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(LoggerMixinError, self).__init__(message)


class CarbonActionError(CarbonResourceError):
    """Action's base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(CarbonActionError, self).__init__(message)


class CarbonExecuteError(CarbonResourceError):
    """Execute's base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(CarbonExecuteError, self).__init__(message)


class CarbonHostError(CarbonResourceError):
    """Asset's base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(CarbonHostError, self).__init__(message)


class CarbonReportError(CarbonResourceError):
    """Report base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(CarbonReportError, self).__init__(message)


class ScenarioError(CarbonResourceError):
    """Scenario's base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(ScenarioError, self).__init__(message)


class BeakerProvisionerError(CarbonProvisionerError):
    """Base class for Beaker provisioner exceptions."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(BeakerProvisionerError, self).__init__(message)


class OpenshiftProvisionerError(CarbonProvisionerError):
    """Base class for openshift provisioner exceptions."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(OpenshiftProvisionerError, self).__init__(message)


class OpenstackProviderError(CarbonProviderError):
    """Base class for openstack provider exceptions."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(OpenstackProviderError, self).__init__(message)


class ArchiveArtifactsError(CarbonError):
    """Base class for when you always want to archive artifacts (pass|fail)."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(ArchiveArtifactsError, self).__init__(message)


class CarbonImporterError(CarbonError):
    """Base class for the artifact importer execeptions."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(CarbonImporterError, self).__init__(message)


class PolarionImporterError(CarbonImporterError):
    """Base class for the Polarion importer execeptions."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(PolarionImporterError, self).__init__(message)
