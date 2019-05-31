Including Scenarios
===================

Overview
--------
The *Include* section is introduced to provide a way to include common steps of
provisioning, orchestration, execute or reports under one common scenario file.
This reduces the redundancy of putting the same set of steps in every scenario file.

The included scenario file when run, will generate its own results.yml file with its
name as a prefix. e.g. common_scenario_results.yml where common_scenario is the name of the
included scenario file. This file will be stored in the same location as the result.yml file.
This allows users to run the common.yml once and its result can be included in other 
scenario files saving time on test executions. Also see `Carbon Output <../output.html>`_

For example:

If you want to run many tests where you need the same provisioned resources,
you can make use of the *include* section in your scenario file. Seperate out your 
provisioning and orchestration steps in a seperate scenario file , e.g  common_scenario.yml.
Put this file in your main scenario.yml file under the *include* section. When you run carbon 
with the scenario.yml, two results file will be generated. One for scenario.yml 
(results.yml) and one for common_scenario.yml (common_scenario_results.yml). You can now add
the common_scenario_results.yml under the *include* section of other scenarios which need
already provisioned resources. This will  eliminate the repetition of the provisioning and
orchestration steps in every scenario file.

.. note::

        For any given task the included scenario is looked for and executed first followed by the main
        scenario. For example, for Orchestrate task, if you have orchestrate section in both the included 
        scenario and the main scenario, then the orchestrate tasks in included scenario will be performed
        first followed by the orchestrate tasks in the main scenario.

Example 1
+++++++++
.. literalinclude:: ../../../examples/docs-usage/include.yml
       :lines: 1-21

Example 2
+++++++++
.. literalinclude:: ../../../examples/docs-usage/include.yml
          :lines: 22-38

The provision.yml and orchstrate.yml could look like below

.. literalinclude:: ../../../examples/docs-usage/provision.yml
       :lines: 1-5

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
       :lines: 1-6

