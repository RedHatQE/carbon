Provision
=========

Overview
--------

The input for provisioning will depend upon the type of resource you are
trying to provision. The current support for provisioning resources are:
:ref:`Beaker<beaker_provisioning>` and :ref:`OpenStack<openstack_provisioning>`.

Provision Resource
++++++++++++++++++

Each resource defined within a provision section can have the following
common keys, and the table below will describe whether the keys are
required or optional:

.. code-block:: yaml

    ---
    provision:
      - name: <name>
        role: <role>
        provisioner: <provisioner>
        metadata: <dict_key_values>
        ansible_params: <dict_key_values>
        provider: <dict_key_values>

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - name
        - The name of the node to boot.
        - String
        - True

    *   - role
        - The names of the roles for the node.
        - List
        - True

    *   - provisioner
        - The name of the provisioner to use to boot nodes.
        - String
        - False

    *   - metadata
        - Data that the resource may need access to after provisioning is
          finished. This data is passed through and is not modified by carbon
          framework.
        - Dict
        - False

    *   - ansible_params
        - Ansible parameters to be used within a inventory file to control how
          ansible communicates with the host.
        - Dict
        - False

    *   - provider
        - Dictionary of the specific provider key/values.
        - Dict
        - True


Role
++++

You can associate a number of roles to a host in a couple of different ways.
First is to define your roles in a comma separated string

.. literalinclude:: ../../../examples/docs-usage/provision.yml
    :lines: 1-4

You can also define your roles as a list.

.. literalinclude:: ../../../examples/docs-usage/provision.yml
    :lines: 7-11

.. _beaker_provisioning:

Provisioning Systems from Beaker
--------------------------------

Credentials
+++++++++++

To authenticate with Beaker, you will need to have your Beaker credentials
in your carbon.cfg file, see `Beaker Credentials
<credentials.html#beaker-credentials>`_ for more details.

Beaker Resource
+++++++++++++++

The following shows all the possible keys for defining a
provisioning resource for Beaker:

.. code-block:: yaml

    ---
    provision:
      - name: <name>
        role: <role>
        provisioner: <provisioner>
        provider:
          name: beaker
          credential: <credential>
          arch: <arch>
          variant: <variant>
          family: <family>
          distro: <os_distro>
          whiteboard: <whiteboard>
          jobgroup: <group_id>
          tag: <tag>
          host_requires_options: [<list of host options>]
          key_values: [<list of key/value pairs defining the host>]      
          distro_requires_options: [<list of distro options>]
          virtual_machine: <True or False>
          virt_capable: <True or False>
          priority: <priority of the job>
          retention_tag: <retention tag>
          timeout: <timeout val for Beaker job>
          kernel_options: [<list of kernel options>]
          kernel_post_options: [<list of kernel post options>]
          kickstart: < Filename of kickstart file>
          ignore_panic: <True or False>
          taskparam: [<list of task parameter settings>]
          ksmeta: [<list of kick start meta OPTIONS>]
        metadata: <dict_key_values>
        ansible_params: <dict_key_values>


.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - name
        - The name to identify the provider (beaker).
        - String
        - True

    *   - credential
        - The name of the credentials to use to boot node. This is the one
          defined in the credentials section of the carbon config file.
        - String
        - True

    *   - arch
        - The arch of the node.
        - String
        - True

    *   - variant
        - The OS variant of the node.
        - String
        - True

    *   - family
        - The OS family of the node. (family or distro needs to be set)
        - String
        - False

    *   - distro
        - The specific OS distribution. (family or distro needs to be set)
        - String
        - False

    *   - whiteboard
        - The name to set for the Beaker whiteboard to help identify your job.
        - String
        - False

    *   - jobgroup
        - The name of the beaker group to set, of who can see the machines and used for machine searching.
        - String
        - False

    *   - tag
        - The name of a tag to get the correct OS (i.e. RTT-ACCEPTED).
        - String
        - False

    *   - host_requires_options
        - List of host options with the format:["<key><operand><value>"].
        - List
        - False

    *   - key_values
        - List of key/value pairs defining the host, with the format:["<key><operand><value>"].
        - List
        - False

    *   - distro_requires_options
        - List of OS options with the format:["<key><operand><value>"].
        - List
        - False

    *   - kernel_options
        - List of Beaker kernel options during install with the format:["<key><operand><value>"]
        - List
        - False

    *   - kernel_options_post
        - List of Beaker kernel options after install with the format:["<key><operand><value>"]
        - List
        - False

    *   - virtual_machine
        - Look for a node that is a virtural machine.
        - Boolean
        - False

    *   - virt_capable
        - Look for a machine that is virt capable.
        - Boolean
        - False

    *   - priority
        - Set the priority of the Beaker job.
        - String
        - False

    *   - retention_tag
        - Set the tag value of how long to keep the job results.
        - String
        - False

    *   - ssh_key
        - Name of the ssh key to inject to the test system, file must be
          placed in your scenario workspace directory.
        - String
        - False

    *   - username
        - username of the Beaker machine, required if using **ssh_key**.
        - String
        - False

    *   - password
        - password of the Beaker machine, required if using **ssh_key**.
        - String
        - False

    *   - timeout
        - Set a value of how long to wait for the Beaker job in seconds.(Default is 8hrs = 28800)
        - Boolean
        - False

    *   - kickstart
        - Name of the kickstart template for installation, the file must be
          placed in your scenario workspace directory.
        - String
        - False

    *   - ignore_panic
        - Do not abort job if panic message appears on serial console
        - Boolean
        - False

    *   - taskparam
        - parameter settings of form NAME=VALUE that will be set for every task in job
        - List
        - False

    *   - ksmeta
        - kickstart metadata OPTIONS for when generating kickstart
        - List
        - False

Example
+++++++

.. literalinclude:: ../../.examples/provision/beaker/scenario.yml


.. _openstack_provisioning:

Provisioning Systems from OpenStack
-----------------------------------

Credentials
+++++++++++

To authenticate with OpenStack, you will need to have your OpenStack
credentials in your carbon.cfg file, see `OpenStack Credentials
<credentials.html#openstack-credentials>`_ for more details.

OpenStack Resource
++++++++++++++++++

The following shows all the possible keys for defining a provisioning
resource for OpenStack:

.. code-block:: yaml

    ---
    provision:
      - name: <name>
        role: <role>
        provisioner: <provisioner>
        metadata: <dict_key_values>
        ansible_params: <dict_key_values>
        provider:
          credential: openstack-creds
          name: openstack
          image: <image>
          flavor: <flavor>
          networks: <networks>
          floating_ip_pool: <floating_ip_pool>
          keypair: <keypair>

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - name
        - The name of the provider (openstack).
        - String
        - True

    *   - credential
        - The name of the credentials to use to boot node. This is the one
          defined in the credentials section of the carbon config file.
        - String
        - True

    *   - image
        - The name or ID of the image to boot.
        - String
        - True

    *   - flavor
        - The name or ID of the flavor to boot.
        - String
        - True

    *   - networks
        - The name of the internal network to attach node too.
        - List
        - True

    *   - floating_ip_pool
        - The name of the external network to attach node too.
        - String
        - False

    *   - keypair
        - The name of the keypair to associate the node with.
        - String
        - True


Example
+++++++

.. literalinclude:: ../../.examples/provision/openstack/scenario.yml

Defining Static Machines
------------------------

There may be scenarios where you already have machines provisioned and would
like carbon to use these static machines.  This option is supported in carbon.
The main key that needs to be stated is the **ip_address**.

The following is an example of a statically defined machine:

Example
+++++++

.. literalinclude:: ../../.examples/provision/static/scenario.yml

There may also be a scenario where you want to run cmds or scripts on the
local system instead of the provisioned resources.  In that case, you should
define a static localhost system.

The following is an example of a statically defined local machine:

.. _localhost_example:

Example
+++++++

.. literalinclude:: ../../.examples/orchestrate/ansible/basic/scenario.yml
    :lines: 1-11

