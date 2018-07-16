Orchestrate
===========

Carbon's orchestrate section declares the configuration to be be performed in
order to test the systems properly.

First lets go over the basic structure that defines a configuration task.

.. literalinclude:: ../../examples/docs-usage/orchestrate.yml
    :lines: 1-6

The above code snippet is the minimal structure that is required to create a
orchestrate task within carbon. This task is translated into a carbon action
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
        - The name of the action you want carbon to execute
        - String
        - Yes
        - n/a

    *   - description
        - A description of what the resource is trying to accomplish
        - String
        - No
        - n/a

    *   - orchestrator
        - The orchestrator to use to execute the action (name) you defined
          above
        - String
        - No (best practice to define this!)
        - ansible

    *   - hosts
        - The list of hosts where carbon will execute the action against
        - List
        - Yes
        - n/a

**Hosts**

You can associate hosts to a given orchestrate task a couple of different ways.
First is to define your hosts in a comma separated string.

.. literalinclude:: ../../examples/docs-usage/orchestrate.yml
    :lines: 8-11

You can also define your hosts as a list.

.. literalinclude:: ../../examples/docs-usage/orchestrate.yml
    :lines: 13-18

It can become tedious if a orchestrate task needs to be performed on all hosts
within the scenario and you have many hosts declared. Carbon provides you with
the ability to say all hosts. This eliminates the need to define every host per
multiple tasks. It can be either in string or list format.

.. literalinclude:: ../../examples/docs-usage/orchestrate.yml
    :lines: 20-23

.. literalinclude:: ../../examples/docs-usage/orchestrate.yml
    :lines: 25-29

-----

Since carbons development model is plug and play. This means different
orchestrator's could be used to execute configuration tasks declared. For the
remainder of this page, please go to your preferred orchestrator below. To
learn more on how you can setup your orchestrate task structures.

Ansible
-------

Ansible is carbons default orchestrator. As we mentioned above each task has
a given name (action). This name is the ansible playbook name (excluding the
file extension). Carbon has the ability to find the playbook. In addition to
the required orchestrate base keys, there are more you can define based on your
selected orchestrator. Lets dive into them..

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required
        - Default

    *   - ansible_options
        - Additional options to provide to the ansible orchestrator regarding
          the task (playbook) to be executed
        - Dictionary
        - No
        - n/a

    *   - ansible_galaxy_options
        - Additional options to provide to the ansible orchestrator regarding
          ansible roles
        - Dictionary
        - No
        - n/a

The table above describes additional key:values you can set within your
orchestrate task. Each of those keys can accept additional key:values. Lets
dive into a couple different examples..

Example 1
~~~~~~~~~

You have a playbook which needs to run against x number of hosts and does not
require any additional extra variables.

.. literalinclude:: ../../examples/docs-usage/orchestrate.yml
    :lines: 31-38

Example 2
~~~~~~~~~

You have a playbook which needs to run against x number of hosts and requires
additional extra variables.

.. literalinclude:: ../../examples/docs-usage/orchestrate.yml
    :lines: 40-53

Example 3
~~~~~~~~~

You have a playbook which needs to run against x number of hosts and requires
an ansible role to be downloaded.

.. literalinclude:: ../../examples/docs-usage/orchestrate.yml
    :lines: 55-64

Content of roles.yml:

.. code-block:: yaml

    ---
    - src: oasis-roles.rhsm

As you can see we defined the role_file key. This defines the ansible role
requirements filename. Carbon will consume that file and download all the
roles defined within.

An alternative to using the role file is you can directly define them using
the roles key.

.. literalinclude:: ../../examples/docs-usage/orchestrate.yml
    :lines: 66-76

It is possible to define both role_file and roles. Carbon will install the
roles first from the role file and then the roles defined. It is up to the
scenario to ensure no problems may occur if both are defined.

.. note::

    If your scenario directory has roles already defined, you do not need to
    define them. This is only if you want carbon to download roles from sites
    such as ansible galaxy, external web servers, etc.

Example 4
~~~~~~~~~

You have a playbook which needs to run against x number of hosts, requires
ansible roles to be downloaded and requires additional extra variables.

.. literalinclude:: ../../examples/docs-usage/orchestrate.yml
    :lines: 78-93

.. attention::

    Every scenario processed by carbon should define an ansible configuration
    file. This provides the scenario with the flexibility to easily control
    portions of ansible.

    If you are using the ability to download roles by carbon, you need to set
    the roles path within your ansible.cfg. If this is not set, problems will
    occur and carbon will fail. Due to being unable to locate the roles within
    the playbook its executing.

    Here is an example ansible.cfg setting the roles_path to a relative path
    within the scenario directory.

    .. code-block:: bash

        [defaults]
        host_key_checking = False
        retry_files_enabled = False
        roles_path = ./assets/ansible/roles

----

Resources
~~~~~~~~~

For system configuration & product installs use roles from: `Oasis Roles`_

.. _Oasis Roles: https://github.com/oasis-roles

For some common configuration & test setup use playbooks from:
`Common PIT Playbooks`_

.. _Common PIT Playbooks: https://gitlab.cee.redhat.com/PIT/carbon-playbooks
