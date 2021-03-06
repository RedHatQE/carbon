Provision
=========

Overview
--------

The input for provisioning will depend upon the type of resource you are
trying to provision. The current support for provisioning resources are:
:ref:`Beaker<beaker_provisioning>` and :ref:`OpenStack<openstack_provisioning>`.
The Beaker and OpenStack resources are provisioned with Carbon's native
provisioners but as of 1.2.0, these resources can also be provisioned using
the :ref:`Linchpin<linchpin_provisioning>` provisioner.

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
        - The name of the asset to provision.
        - String
        - True

    *   - role/groups
        - The names of the roles or groups for the asset. Used to
          assign host assets to groups when generating the Ansible
          inventory files.
        - List
        - False

    *   - provisioner
        - The name of the provisioner to use to provision assets.
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
          ansible communicates with the host asset.
        - Dict
        - False



Provisioner
+++++++++++

As of 1.6.0, this key is will be a requirement to specify. We will still be backwards compatible
for users who do not use this key in conjuction with the **provider** key. But at some point in
the future will be making this a hard requirement. So it is recommended to update all scenarios
to start explicitly using this key.

Provider
++++++++

As of 1.6.0, the provider key is no longer a requirement for all provisioners. Going forward this
key is only required for the **bkr-client** and **openstack-libcloud** provisioners.

Role/Groups
+++++++++++

Carbon roles are the equivalent of Ansible groups. As of 1.2.0, we've
changed the schema from role to groups to better reflect what the purpose of this
parameter is intended for. All scenario descriptor files written prior to 1.2.0
using role will still be honored but it is considered deprecated and it is recommended to
update all scenarios to use the new parameter.

As of 1.4.0 role/groups is not a requirement for all asset types. This should only be
specified for host assets like VMs or Baremetal Systems that have an ip and will be acted
on later on during Orchestrate or Execute. Assets like networks, storage, security key, etc.
do not and should not be assigned a role/groups to avoid polluting the Ansible inventory file
with empty groups.

You can associate a number of roles or groups to a host in a couple of different ways.
First is to define your roles in a comma separated string

.. literalinclude:: ../../../examples/docs-usage/provision.yml
    :lines: 1-5

You can also define your roles as a list.

.. literalinclude:: ../../../examples/docs-usage/provision.yml
    :lines: 7-13

Here we have defined a list of groups.

.. literalinclude:: ../../../examples/docs-usage/provision.yml
    :lines: 15-21

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
provisioning resource for Beaker using the **bkr-client** provisioner:

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
resource for OpenStack using the **openstack-libcloud** provisioner:

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

Provisioning Openstack Assets using carbon_openstack_client_plugin
------------------------------------------------------------------

Starting with version 1.8.0, Carbon is offering a new plugin **carbon_openstack_client_plugin**. to provision
openstack resources. This plugin utilizes the openstackclient to provision resources.

User can now install this plugin from Carbon

.. code-block:: bash

    $ pip install carbon[openstack-client-plugin]


In your scenario descriptor file specify the **provisioner** key in your provision section.

.. code-block:: yaml

    provisioner: openstack-client

For more information on how to install plugin and setup the scenario descriptor file for using this plugin,
please refer `here <https://gitlab.cee.redhat.com/ccit/carbon/plugins/carbon_openstack_client_plugin>`__


.. _linchpin_provisioning:

Provisioning Assets with Linchpin
----------------------------------

Starting in Carbon 1.6.0 you can fully provision all Linchpin supported providers
using the Linchpin plugin. The code has also been pulled out of Carbon and maintained
as a separate plugin.

First the plugin must be installed. Refer to the carbon `installation <install.html>`__ document on
how you can install the plugin as an extra package.

You can also refer to the
`plugin <https://gitlab.cee.redhat.com/ccit/carbon/plugins/carbon_linchpin_plugin/blob/develop/docs/user.md#installation>`__
documentation directly

In your scenario file specify the **provisioner** key in your provision section.

.. code-block:: yaml

    provisioner: linchpin-wrapper


Specify any of the
`keys <https://gitlab.cee.redhat.com/ccit/carbon/plugins/carbon_linchpin_plugin/blob/develop/docs/user.md#provisioning-assets-with-linchpin>`__
supported by the linchpin provisioner.


.. note::

   Users who were using the linchpin provisoiner and using the **provider**
   key, we will only be supported for OpenStack and Beaker Providers. It is highly
   recommended that users migrate to using the new set of linchpin provisioner keys.
   Refer to second example below.

.. note::

    Due to Linchpin's lack of transactional concurrency support in their database
    it is recommended to provision resources sequentially. Refer to the
    `task_concurrency <../configuration.html#carbon-configuration>`__
    setting in the carbon.cfg to switch the provision task execution
    to be sequential.

Credentials
+++++++++++
Since Linchpin support multiple providers, each provider supports different types of parameters.
Linchpin also comes with it's own ability to pass in credentials. To be flexible, we support the
following options

 - You can define the credentials in the *carbon.cfg* and reference
   them using the Carbon *credential* key. In most cases, Carbon will export the provider
   specific credential environmental variables supported by Linchpin/Ansible.

 - You can use the Linchpin *credentials* option and create the credentials file per
   Linchpin provider specification.

 - You can specify no *credential* or *credentials* key and export the specific provider
   credential environmental variables supported by Linchpin/Ansible yourself.

For more information refer to the plugins
`credential <https://gitlab.cee.redhat.com/ccit/carbon/plugins/carbon_linchpin_plugin/blob/develop/docs/user.md#provisioning-assets-with-linchpin>`__
document section.

Examples
++++++++

Below we will just touch on a couple examples. You can see the rest of the
`examples <https://gitlab.cee.redhat.com/ccit/carbon/plugins/carbon_linchpin_plugin/blob/develop/docs/user.md#credentials>`__
in the plugin documentation.

Example 1
~~~~~~~~~

This example uses a PinFile that has already been developed with specific targets in the pinfile.

.. code-block:: yaml

    ---
    provision:
    - name: db2_dummy
      provisioner: linchpin-wrapper
      pinfile:
        path: openstack-simple/PinFile
        targets:
          - openstack-stage
          - openstack-dev


Example 2
~~~~~~~~~

This example uses the more traditional way of provisioning with Carbon. It's recommended that users
still using the **provider** key with the Linchpin provisioner should switch over to this style.

.. code-block:: yaml

    ---
    provision:
    - name: db2_dummy
      provisioner: linchpin-wrapper
      credential: osp-creds
      groups:
        - example
      resource_group_type: openstack
      resource_definitions:
        - name: {{ instance | default('database') }}
          role: os_server
          flavor: {{ flavor | default('m1.small') }}
          image:  rhel-7.5-server-x86_64-released
          count: 1
          keypair: {{ keypair | default('db2-test') }}
          networks:
            - {{ networks | default('provider_net_ipv6_only') }}
      ansible_params:
        ansible_user: cloud-user
        ansible_ssh_private_key_file: keys/{{ OS_KEYPAIR }}


Using Linchpin Count
++++++++++++++++++++

Carbon supports Linchpin's count feature to create multiple resources in a single
Asset block. Refer to the example.

Example
~~~~~~~
To create 2 resources in openstack **count: 2** is added.
It's important to note that when multiple
resources are generated Carbon will save them as two distinct assets.
Assets created using count will be suffixed with a digit starting at 0 up
to the number of resources.

This example will provision 2 resources *openstack-node_0* and *openstack-node_1*

By default count value is 1.

.. code-block:: yaml
   
    provision:
    - name: openstack-node
      role: node
      provisioner: linchpin-wrapper
      resource_group_type: openstack
      resource_definitions:
         - name: openstack
           credential: openstack-creds
           image: rhel-7.5-server-x86_64-released
           flavor: m1.small
           networks:
            - '{{ network }}'
           count: 2

the output of results.yml

.. code-block:: yaml

    provision:
    - name: openstack-node_0
      role: node
      provisioner: linchpin-wrapper
      resource_group_type: openstack
      resource_definitions:
         - name: openstack
           credential: openstack-creds
           image: rhel-7.5-server-x86_64-released
           flavor: m1.small
           networks:
            - '{{ network }}'
           count: 2

    - name: openstack-node_1
      role: node
      provisioner: linchpin-wrapper
      resource_group_type: openstack
      resource_definitions:
         - name: openstack
           credential: openstack-creds
           image: rhel-7.5-server-x86_64-released
           flavor: m1.small
           networks:
            - '{{ network }}'
           count: 2

Generating Ansible Inventory
++++++++++++++++++++++++++++

Both Carbon and Linchpin have the capability to generate inventory files post
provisioning. For those that want Carbon to continue to generate the Inventory
file and use the Linchpin provisioner as just a pure provisioner can do so
by specifying the following keys

 - roles/group
 - ansible_params

Refer to Example 2 above in the examples section.

For those that want to use Linchpin to generate the inventory file. You must do the following

 - Specify the **layout** key and either provide a dictionary of a Linchpin layout or provide
   a path to a layout file in your workspace.

 - Do NOT specify **roles/group** and **ansible_params** keys

Refer to examples 6 and 8 in the Linchpin plugin documents to see the two variations.

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
local system instead of the provisioned resources.  Refer to the
`localhost <../localhost.html>`_ page for more details.

