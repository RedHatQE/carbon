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
    tests.test_pipeline_class

    Unit tests for testing carbons pipeline builder class.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import pytest
from carbon.exceptions import CarbonError
from carbon.tasks import CleanupTask, ExecuteTask, ProvisionTask, \
    OrchestrateTask, ReportTask, ValidateTask
from carbon.utils.pipeline import PipelineBuilder


@pytest.fixture(scope='class')
def pipe_builder():
    return PipelineBuilder(name='validate')


@pytest.fixture(scope='class')
def invalid_pipe_builder():
    return PipelineBuilder(name='null')


class TestPipelineBuilder(object):
    @staticmethod
    def test_constructor(pipe_builder):
        assert isinstance(pipe_builder, PipelineBuilder)

    @staticmethod
    def test_name_property(pipe_builder):
        assert pipe_builder.name == 'validate'

    @staticmethod
    def test_verify_task_is_valid(pipe_builder):
        assert pipe_builder.is_task_valid()

    @staticmethod
    def test_verify_task_is_invalid(invalid_pipe_builder):
        assert not invalid_pipe_builder.is_task_valid()

    @staticmethod
    def test_valid_task_class_lookup(pipe_builder):
        cls = pipe_builder.task_cls_lookup()
        assert getattr(cls, '__task_name__') == pipe_builder.name

    @staticmethod
    def test_invalid_task_class_lookup(invalid_pipe_builder):
        with pytest.raises(CarbonError) as ex:
            invalid_pipe_builder.task_cls_lookup()
        assert 'Unable to lookup task %s class.' % invalid_pipe_builder.name \
               in ex.value.args

    @staticmethod
    def test_build_validate_task_pipeline(scenario):
        builder = PipelineBuilder(name='validate')
        pipeline = builder.build(scenario)
        assert getattr(pipeline, 'name') == 'validate'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert getattr(pipeline, 'type') is ValidateTask

    @staticmethod
    def test_build_provision_task_pipeline(scenario):
        builder = PipelineBuilder(name='provision')
        pipeline = builder.build(scenario)
        assert getattr(pipeline, 'name') == 'provision'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert getattr(pipeline, 'type') is ProvisionTask

    @staticmethod
    def test_build_orchestrate_task_pipeline(scenario):
        builder = PipelineBuilder(name='orchestrate')
        pipeline = builder.build(scenario)
        assert getattr(pipeline, 'name') == 'orchestrate'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert getattr(pipeline, 'type') is OrchestrateTask

    @staticmethod
    def test_build_execute_task_pipeline(scenario):
        builder = PipelineBuilder(name='execute')
        pipeline = builder.build(scenario)
        assert getattr(pipeline, 'name') == 'execute'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert getattr(pipeline, 'type') is ExecuteTask

    @staticmethod
    def test_build_report_task_pipeline(scenario):
        builder = PipelineBuilder(name='report')
        pipeline = builder.build(scenario)
        assert getattr(pipeline, 'name') == 'report'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert getattr(pipeline, 'type') is ReportTask

    @staticmethod
    def test_build_cleanup_task_pipeline(scenario):
        builder = PipelineBuilder(name='cleanup')
        pipeline = builder.build(scenario)
        assert getattr(pipeline, 'name') == 'cleanup'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert getattr(pipeline, 'type') is CleanupTask

    @staticmethod
    def test_multiple_scenario_pipeline_01(master_child_scenario):
        builder = PipelineBuilder(name='provision')
        pipeline = builder.build(master_child_scenario)
        tasks = getattr(pipeline, 'tasks')
        assert len(tasks) == 2

    @staticmethod
    def test_multiple_scenario_pipeline_02(master_child_scenario):
        builder = PipelineBuilder(name='execute')
        pipeline = builder.build(master_child_scenario)
        tasks = getattr(pipeline, 'tasks')
        assert len(tasks) == 2