Using Localhost
===============

There may be a scenario where you want to run cmds or scripts on the
local system instead of the provisioned resources.  There are couple options
to be able to do this.

Explicit Localhost
------------------

The following is an example of a statically defined local machine:

.. _localhost_example:

Example
+++++++

.. literalinclude:: ../.examples/orchestrate/ansible/basic/scenario.yml
    :lines: 1-11

When explicitly defined, this host entry is written to the master inventory
file and the localhost will be accessible to ALL the Orchestrate and Execute tasks
in the scenario.

Implicit Localhost
------------------

If localhost or any other host name that is not explicitly defined in the Provision
section is used as a value to *hosts* in the Orchestrate or Execute sections, Carbon
will infer that the intended task is to be run on the localhost.

This will temporarily add a localhost entry, with the appropriate Ansible host group
variables, to the inventory which will be available to Ansible when running the task.
An example entry might look like the following example.

.. code-block:: bash

    [hosts:children]
    localhost

    [localhost]
    127.0.0.1

    [localhost:vars]
    ansible_connection=local
    ansible_python_interpreter="{{ansible_playbook_python}}"


Once the Orchestrate or Execute task finishes the localhost entry will be removed. It is only
available to the single task it was specified for.

Example
+++++++

Here an Orchestrate and an Execute task refer to a couple hosts, *carbon_controller* and *localhost*,
respectively, that are not defined in the provision section.

.. code-block:: yaml

    ---
    provision:
      - name: ci_test_client_b
        groups:
        - client
        - vnc
        ip_address: 192.168.100.51
        ansible_params:
           ansible_private_ssh_key: keys/test_key

    orchestrate:
      - name: test_setup_playbook.yml
        description: "running a test setup playbook on localhost"
        orchestrator: ansible
        hosts: carbon_controller

    execute:
      - name: test execution
        description: "execute some test script locally"
        hosts: localhost
        executor: runner
        ignore_rc: False
        shell:
          - chdir: /home/user/tests
            command: python test_sample.py --output-results suite_results.xml
            ignore_rc: True
        artifacts:
          - /home/user/tests/suite_results.xml

