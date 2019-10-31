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

    *   - provider
        - Dictionary of the specific provider key/values.
        - Dict
        - True


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


.. _linchpin_provisioning:

Provisioning Systems with Linchpin
----------------------------------

The Beaker, OpenStack, Libvirt, and AWS resources can also be deployed using the
Linchpin provisioner. To use the linchpin provisioner you must supply
the **provisioner** key in your provision section.

.. code-block:: yaml

    provisioner: linchpin-wrapper


.. note::

    When provisioning resources of different types, from the same Provider,
    that have some inter-dependency with each other it is recommended to use the
    `task_concurrency <../configuration.html#carbon-configuration>`__
    setting in the carbon.cfg to switch the provision task execution
    to be sequential.

.. note::

    You may notice that name in the provider parameters is different than
    name used in Linchpin pinfiles. For carbon, name is the name of the provider,
    i.e. libvirt, so carbon knows which provider to use and how to build the
    resource definitions. When building the resource defintion for Linchpin, Carbon
    will take the name of the defined carbon resource in the provision
    section and use that as the name parameter for the resource defintion.

Using Linchpin Count
++++++++++++++++++++

Carbon supports Linchpin's count feature to create multiple resources using
Beaker, Openstack, Libvirt and AWS providers. For this *count* key has to be added 
to the provider section in the scenario descriptor file.

Example
~~~~~~~
To create 2 resources in openstack **count: 2** is added to the provider 
section. 
Resources created using count will be suffixed with a digit starting at 0
upto the number of resources. This example will provision 2 resources
*openstack-node_0* and *openstack-node_1*
By default count value is 1.

.. code-block:: yaml
   
    provision:
    - name: openstack-node
      role: node
      provisioner: linchpin-wrapper
      provider: 
        name: openstack
        credential: openstack-creds
        image: rhel-7.5-server-x86_64-released
        flavor: m1.small
        networks:
         - '{{ network }}'
        count: 2

To enable the use of count feature while using linchpin set the feature toggle to
true in the carbon.cfg file

.. code-block:: yaml

   [feature_toggles:host]
   plugin_implementation=True


Beaker Resource
+++++++++++++++

The Beaker Provider has been augmented to include all the Linchpin roles and
parameters. For a full list of Linchpin Beaker parameters
please refer to
the `Linchpin Beaker Provider <https://linchpin.readthedocs.io/en/latest/beaker.html>`_.

Credentials
~~~~~~~~~~~

Nothing has changed with the authentication mechanism used by Carbon when using
Linchpin. Please refer to the previous Beaker section for the specific credential.

Common Beaker Parameters
~~~~~~~~~~~~~~~~~~~~~~~~

There is commonality between some of the bkr-client provisioner parameters and the
Linchpin parameters. If a bkr-client parameter is used with Linchpin, it will be translated
to the appropriate key name and value type supported by Linchpin. The table below highlights
some of the common parameters shared by both provisioners.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Carbon Key
        - Carbon Type
        - Linchpin Key
        - Linchpin Type

    *   - name
        - String
        - name
        - String

    *   - arch
        - String
        - arch
        - String

    *   - variant
        - String
        - variant
        - String

    *   - family
        - String
        - family
        - String

    *   - distro
        - String
        - distro
        - String

    *   - whiteboard
        - String
        - whiteboard
        - String

    *   - jobgroup
        - String
        - job_group
        - String

    *   - tag
        - String
        - tags
        - List

    *   - host_requires_options
        - List
        - hostrequires
        - List

    *   - key_values
        - List
        - keyvalues
        - List

    *   - kernel_options
        - List
        - kernel_options
        - String

    *   - kernel_post_options
        - List
        - kernel_options_post
        - String

    *   - kickstart
        - String
        - kickstart
        - String

    *   - taskparam
        - List
        - taskparam
        - List

    *   - ksmeta
        - List
        - ks_meta
        - List



SSH Keys
~~~~~~~~

It is important to note the **ssh_key** parameter with the bkr-client
provisioner was a string containing the private key path. From this key file
a public key was generated and injected it into the Beaker host.

Linchpin Beaker offers a couple different methods for public key injection. It's been
decided to keep the single **ssh_key** parameter and transparently map them
to the appropriate Linchpin parameters. The key file still needs to be in the
Scenario workspace.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Key Type Provided
        - Linchpin Key Mapped To

    *   - ssh_key
        - List of public ssh keys
        - ssh_key

    *   - ssh_key
        - List of private ssh key files
        - ssh_keys_path and ssh_key_file

    *   - ssh_key
        - List of public ssh key files
        - ssh_keys_path and ssh_key_file

Example
~~~~~~~

.. literalinclude:: ../../.examples/provision/linchpin/beaker_scenario_linchpin.yml


OpenStack Resource
++++++++++++++++++

The OpenStack Provider has been augmented to include all the Linchpin
OpenStack os_server resource type and topology parameters except
**cacert**, and **cert**. For a full list of Linchpin OpenStack
os_server parameters please refer to the
`Linchpin OpenStack Provider <https://linchpin.readthedocs.io/en/latest/openstack.html>`_.

Credentials
~~~~~~~~~~~

Nothing has changed with the authentication mechanism used by Carbon when using
Linchpin. Please refer to the previous OpenStack section for the specific credential.

Common OpenStack Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~

There is commonality between some of the openstack-libcloud provisioner parameters and the
Linchpin parameters. If a openstack-libcloud parameter is used with Linchpin, it will be translated
to the appropriate key name and value type supported by Linchpin. The table below
highlights some of the common parameters shared by both provisioners

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Carbon Key
        - Carbon Type
        - Linchpin Key
        - Linchpin Type

    *   - name
        - String
        - name
        - String

    *   - image
        - String
        - image
        - String

    *   - flavor
        - String
        - flavor
        - String

    *   - networks
        - List
        - networks
        - List

    *   - floating_ip_pool
        - String
        - fip_pool
        - String

    *   - keypair
        - String
        - keypair
        - String


Example
~~~~~~~

.. literalinclude:: ../../.examples/provision/linchpin/openstack_scenario_linchpin.yml


Libvirt Resource
++++++++++++++++

A Libvirt Provider has been added that supports all the resource types and
their respective parameters, except **count**.

Libvirt Parameters
~~~~~~~~~~~~~~~~~~
The most important provider parameter is **role**. This defines the resource type being
provisioned to Linchpin. Carbon will know which provider parameters that need to be
validated and how to put together the pinfile for Linchpin based on this parameter.
For a full list of Linchpin Libvirt parameters please refer to the
`Linchpin Libvirt Provider <https://linchpin.readthedocs.io/en/latest/libvirt.html>`_.

The Libvirt provider also has some configuration evars that affect how Linchpin
provisions Libvirt resources.

    * The `image management keys <https://linchpin.readthedocs.io/en/latest/libvirt.html#copying-images>`_
      can be directly specified in the providers dictionary in the scenario descriptor file.

    * The **default_ssh_key_path** defaults to *~/.ssh* and is used by Linchpin
      to find the ssh keys to be used or created when provisioning resources.
      Carbon overrides this key to point to the Scenario workspace *keys* directory.


Libvirt Credentials
~~~~~~~~~~~~~~~~~~~

To authenticate with Libvirt, you will need to have a Libvirt credentials
in your carbon.cfg file, see `Libvirt Credentials
<credentials.html#libvirt-credentials>`_ for more details.


Example
~~~~~~~

.. literalinclude:: ../../.examples/provision/linchpin/libvirt_scenario_linchpin.yml


AWS Resource
++++++++++++

An AWS Provider has been added that supports all the resource types and
their respective parameters, except **count**.

AWS Parameters
~~~~~~~~~~~~~~
The most important provider parameter is **role**. This defines the resource type being
provisioned to Linchpin. Carbon will know which provider parameters that need to be
validated and how to put together the pinfile for Linchpin based on this parameter.
For a full list of Linchpin AWS parameters please refer to the
`Linchpin AWS Provider <https://linchpin.readthedocs.io/en/latest/aws.html>`_.

The AWS provider also has some configuration evars and parameters that affect how Linchpin
provisions AWS resources.

    * The **default_ssh_key_path** evar defaults to *~/.ssh* and is used by Linchpin
      to find the ssh keys to be used or created when provisioning resources.
      Carbon overrides this key to point to the Scenario workspace *keys* directory.

    * Certain parameters will require a path to some type of file like **policy_file**
      or **template_path**. These will need to be stored in the Scenario workspace
      and specified as a relative file path.



AWS Credentials
~~~~~~~~~~~~~~~

To authenticate with AWS, you will need to have an AWS credentials
in your carbon.cfg file, see `AWS Credentials
<credentials.html#aws-credentials>`_ for more details.


Example
~~~~~~~

.. literalinclude:: ../../.examples/provision/linchpin/aws_scenario_linchpin.yml

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

