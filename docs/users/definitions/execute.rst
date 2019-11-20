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

The following is the basic structure that defines an execution task, using a
command for execution:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 1-18

The following is the basic structure that defines an execution task, using a
user defined script for execution:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 20-37

The following is the basic structure that defines an exectuion task, using a
user defined playbook for execution:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 40-57


The above code snippet is the minimal structure that is required to create a
execute task within carbon. This task is translated into a carbon execute
object which is part of the carbon compound. You can learn more about this at
the `architecture <../../developers/architecture.html>`_ page.

Please see the table below to understand the key/values defined.

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

    *   - valid_rc
        - valid return codes of the execution (success)
        - list of integers
        - No
        - n/a

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

    *   - artifact_locations
        - A dictionary of data collected during artifacts or a dictionary of additional log files to be
          considered by Carbon after execution
          It is a dictionary of dir path as key and files in the dir as values.
        - dict
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
defining the hosts `here <orchestrate.html#hosts>`_. For more localhost
usage refer to the`localhost <../localhost.html>`_ page.

Ansible
-------

The default executor '*runner*' uses ansible to perform the requested actions.
This means users can set ansible options to be used by the runner executor.
In this case, the options should mostly be used for defining the user that is
performing the execution. Please see the following example for more details:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 59-65

Return Code for Test Execution
------------------------------

Carbon will fail out if there is a non-zero return code.  However, for many
unit testing frameworks there is a non-zero return code if there are test failures.
For this case, carbon has two options to handle these situations:

 #.  ignore the return code for the test execution
 #.  give list of valid return codes that will not flag failure

Option 1 to handle non-zero return codes is called **ignore_rc**, this option 
can be used at the top level key of execute or can also be used for each
specific call.  The following shows an example, where it is defined in both
areas.  The top level is set to False, which is the default, then it is used
only for the 2nd pytest execution call, where there are failures:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 68-88

Options 2 to handle non-zero return codes is called **valid_rc**, this option
can also be used at the top level key of execute or can be used for each
specific call. If **ignore_rc** is set it takes precedence. The following shows
an example, where it is defined in both areas. The top level is set to one value
and the call overides it:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 197-217


Using Shell Parameter for Test Execution
----------------------------------------

When building your shell commands it is important to take into consideration
that there are multiple layers the command is being passed through before
being executed. The two main things to pay attention to are
YAML syntax/escaping and Shell escaping.

When writing the command in the scenario descriptor file it needs to be written in
a way that both Carbon and Ansible can parse the YAML properly. From a Carbon perspective
it is when the the scenario descriptor is first loaded. From an Ansible perspective
its when we pass it the playbook we create, cbn_execute_shell.yml, through to the
ansible-playbook CLI.

Then there could be further escapes required to preserve the test command so it can be
interpreted by the shell properly. From a Carbon perspective that is when we
pass the test command to the ansible-playbook CLI on the local shell using the
-e "xcmd='<test_command>'" parameter. From the Ansible perspective its when
the shell module executes the actual test command using the shell on the designated system.

Let's go into a couple examples

.. code-block:: yaml

   shell:
     - command: glusto --pytest='-v tests/test_sample.py --junitxml=/tmp/SampleTest.xml'
                --log /tmp/glusto_sample.log

On the surface the above command will pass YAML syntax parsing but will fail when actually
executing the command on the shell. That is because the command is not preserved properly on
the shell when it comes to the *--pytest* optioned being passed in. In order to get
this to work you could escape this in one of two ways so that the *--pytest* optioned is
preserved.

.. code-block:: yaml

   shell:
     - command: glusto --pytest=\\\"-v tests/test_sample.py --junitxml=/tmp/SampleTest.xml\\\"
                --log /tmp/glusto_sample.log


   shell:
     - command: glusto \\\"--pytest=-v tests/test_sample.py --junitxml=/tmp/SampleTest.xml\\\"
                --log /tmp/glusto_sample.log


Here is a more complex example

.. code-block:: yaml

    shell:
        - command: if [ `echo \$PRE_GA | tr [:upper:] [:lower:]` == 'true' ];
                   then sed -i 's/pre_ga:.*/pre_ga: true/' ansible/test_playbook.yml; fi

By default this will fail to be parsed by YAML as improper syntax. The rule of thumb is
if your unquoted YAML string has any of the following special characters :-{}[]!#|>&%@
the best practice is to quote the string. You have the option to either use single quote
or double quotes. There are pros and cons to which quoting method to use. There are online
resources that go further into this topic.

Once the string is quoted, you now need to make sure the command is preserved properly
on the shell. Below are a couple of examples of how you could achieve this using either
a single quoted or double quoted YAML string

.. code-block:: yaml

    shell:
        - command: 'if [ \`echo \$PRE_GA | tr [:upper:] [:lower:]\` == ''true'' ];
                   then sed -i \"s/pre_ga:.*/pre_ga: true/\" ansible/test_playbook.yml; fi'


    shell:
        - command: "if [ \\`echo \\$PRE_GA | tr [:upper:] [:lower:]\\` == \\'true\\' ];
                   then sed \\'s/pre_ga:.*/pre_ga: true/\\' ansible/test_playbook.yml; fi"

.. note::
     It is NOT recommended to output verbose logging to standard output for long running tests as there could be
     issues with carbon parsing the output

Using Playbook Parameter for Test Execution
-------------------------------------------

Using the playbook parameter to execute tests works like how playbooks
are executed in the Orchestration phase. The only thing not supported is the
ability to download roles using the *ansible_galaxy_option*. The following
is an example of how run test playbooks.

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 218-232


.. note::
    Unlike the shell or script parameter the test playbook executes locally
    from where carbon is running. Which means the test playbook must be in
    the workspace.


Data Substitution Required for Test Execution
---------------------------------------------

In some cases, you may need to substitute data for the execution.  Carbon
allows you to substitute the information from the dynamically created hosts.

Let's first take a look at some example data of key/values a user may use
for provisioning a host:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 110-126

After the machines are provsioned, we have more information in the host object,
and this can be seen by the results.yml file after a provision is successful.
Some basic information that is added is the machine's actual name and ip
address.  The following is what the data looks like after provisioning:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 129-153

Looking at the data presented above, there is a lot of information about the
host, that may be useful for test execution.  You can also see the key
**metadata**, this key can be used to set any data the user wishes to when
running carbon.

The following is an example, where the user plans to use the ip address in an
execution command.  From the data above, you can see the user is accessing the
data from **test_client_a** -> **ip_address**.

.. literalinclude:: ../../../examples/docs-usage/execute.yml
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

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 156-163

Going through the basics of artifacts, the user can archive individual files,
as shown by the following example:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 166-170

The user can also artifact files using wildcards as shown in the following
example:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 172-175

The user can also archive a directory using either of the following two
examples:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 177-180

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 182-185

Finally, the user can archive a directory using a wildcard using either
of the following two examples:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
   :lines: 187-190

.. literalinclude:: ../../../examples/docs-usage/execute.yml
   :lines: 192-195

Artifact Locations
~~~~~~~~~~~~~~~~~~
The **artifact_locations** key is used to keep track of the artifacts that were collected using artifacts.
It's a dictionary where the path of the directory is the key and the files within the directory are values.
With release 1.4.0, the key is being made available to users to define locations for artifacts that
may not have been collected as part of artifacts but they want to be tracked for later use in Report.
The only caveat is the artifacts defined under artifact_locations must be placed in the
carbon_data_folder/.results directory. Refer to the `Report page <report.html>`_

In the below example, the ~payload_dir is the name of the directory , results
is a sub directory and artifacts/test1.log  is a file in another sub directory

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 235-255

Common Examples
---------------

Please review the following for detailed end to end examples for common
execution use cases:

* `Pytest Example <../examples.html#pytest>`_
* `JUnit Example <../examples.html#junit>`_
* `Restraint Example <../examples.html#restraint>`_
