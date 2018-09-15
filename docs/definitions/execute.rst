Execute
=======

Overview
--------

Carbon's execute section declares the test execution of the scenario.  In
most cases there would be three major steps performed during execution:

- cloning the tests
- executing the tests
- gathering the test results, logs, and other important information for the
  test execution.

The execution is further broken down into 3 different types:

- execution using a command
- execution using a user defined script
- execution using a user defined playbook

The folowing is the basic structure that defines an execution task, using a
command for execution:

.. literalinclude:: ../../examples/docs-usage/execute.yml
    :lines: 1-18

The following is the basic structure that defines an execution task, using a
user defined script for execution:

.. literalinclude:: ../../examples/docs-usage/execute.yml
    :lines: 20-37

The following is the basic structure that defines an exectuion task, using a
user defined playbook for execution:

.. literalinclude:: ../../examples/docs-usage/execute.yml
    :lines: 40-57


The above code snippet is the minimal structure that is required to create a
execute task within carbon. This task is translated into a carbon execute
object which is part of the carbon compound. You can learn more about this at
the `architecture <../architecture.html>`_ page. Please see the table below to
understand the key/values defined.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required
        - Default

    *   - name
        - Name assigned to the execution task
        - String
        - Yes
        - n/a

    *   - description
        - Description of the execution task
        - String
        - No
        - n/a

    *   - executor
        - Name of the executor to be used
        - String
        - No
        - runner

    *   - hosts
        - the machine(s) that execute will run on
        - String
        - Yes
        - n/a

    *   - ignore_rc
        - ignore the return code of the execution
        - Boolean
        - No
        - False

    *   - git
        - git information for the tests in execution
        - list of dictionaries
        - No
        - n/a

    *   - shell
        - list of shell commands to execute the tests.
        - list of dictionaries
        - (Not required; however, one of the following must be defined:
          shell, script or playbook)
        - False

    *   - script
        - list of scripts to execute to run the tests.
        - list of dictionaries
        - (Not required; however, one of the following must be defined:
          shell, script or playbook)
        - False

    *   - playbook
        - list of playbooks that execute the tests.
        - list of dictionaries
        - (Not required; however, one of the following must be defined:
          shell, script or playbook)
        - False

    *   - artifacts
        - list of all the data to collect after execution.
          If a directory is listed, all data in that folder
          will be gathered.  A single file can also be listed.
        - list
        - No
        - n/a

    *   - ansible_options
        - git information for the tests in execution
        - dictionary of ansible options
        - No
        - n/a

Hosts
-----

Carbon provides many ways to define your host.  This has already been
described in the orchestration section, please view information about
defining the hosts `here <orchestrate.html#hosts>`_.

Ansible
-------

Since using the default executor, which is called runner, uses ansible to
perform the actions, the user can set ansible_options.  In this case, the
options should mostly be used for defining the user that is performing the
execution, the following is an example:

.. literalinclude:: ../../examples/docs-usage/execute.yml
    :lines: 59-65

Return Code for Test Execution
------------------------------

Carbon will fail out if there is a non-zero return code.  However, for many
unit testing frameworks there is a non-zero return code if there are failures.
For this case, carbon has an option to ignore the return code for the test
execution.

The option that can be used for this case is called **ignore_rc**, this option
can be used at the top level key of execute or can also be used for each
specific call.  The following shows an example, where it is defined in both
areas.  The top level is set to False, which is the default, then it is used
only for the 2nd pytest execution call, where there are failures:

.. literalinclude:: ../../examples/docs-usage/execute.yml
    :lines: 68-88

Data Substitution Required for Test Execution
---------------------------------------------

In some cases, you may need to substitute data for the execution.  Carbon
allows you to substitute the information from the dynamically created hosts.

Let's first take a look at some example data of key/values a user may use
for provisioning a host:

.. literalinclude:: ../../examples/docs-usage/execute.yml
    :lines: 110-125

After the machines are provsioned, we have more information in the host object,
and this can be seen by the results.yml file after a provision is successful.
Some basic information that is added is the machine's actual name and ip
address.  The following is what the data looks like after provisioning:

.. literalinclude:: ../../examples/docs-usage/execute.yml
    :lines: 128-155

Looking at the data presented above, there is a lot of information about the
host, that may be useful for test execution.  You can also see the key
**metadata**, this key can be used to set any data the user wishes to when
running carbon.

The following is an example, where the user plans to use the ip address in an
execution command.  From the data above, you can see the user is accessing the
data from **test_client_a**, **ip_address**, and the first list item ([0]) in
the **ip_address** list.

.. literalinclude:: ../../examples/docs-usage/execute.yml
    :lines: 90-107


Artifacts of the Test Execution
-------------------------------

After an execution is complete, it is common to get results of the test
execution, logs related to the execution, and other logs or files generated
by a specific product during the execution.  These will all be gathered by
carbon and placed in an artifacts directory of your data directory.

For the data gathering, if you specify a folder, carbon will gather all the
data under that folder, if you specify a file, it will gather that single
file.

The following is a simple example of the data gathering (defining artifacts):

.. literalinclude:: ../../examples/docs-usage/execute.yml
    :lines: 158-165

Going through the basics of artifacts, the user can archive individual files,
as shown by the following example:

.. literalinclude:: ../../examples/docs-usage/execute.yml
    :lines: 168-172

The user can also artifact files using wildcards as shown in the following
example:

.. literalinclude:: ../../examples/docs-usage/execute.yml
    :lines: 174-177

The user can also archive a directory using either of the following two
examples:

.. literalinclude:: ../../examples/docs-usage/execute.yml
    :lines: 179-182

.. literalinclude:: ../../examples/docs-usage/execute.yml
    :lines: 184-187

Finally, the user can archive a directory using a wildcard using either
of the following two examples:

.. literalinclude:: ../../examples/docs-usage/execute.yml
   :lines: 189-192

.. literalinclude:: ../../examples/docs-usage/execute.yml
   :lines: 194-197

Common Examples
---------------

Please review the following for detailed end to end examples for common
execution use cases:

* `Pytest Example <../examples.html#pytest>`_
* `JUnit Example <../examples.html#junit>`_
* `Restraint Example <../examples.html#restraint>`_
