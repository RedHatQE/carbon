Provision
=========

Overview
--------

The input for provisioning will depend upon the type of resource you are
trying to provision. The current support for provisioning resources are: :ref:`Beaker<beaker_provisioning>` and :ref:`OpenStack<openstack_provisioning>`.


.. _beaker_provisioning:

Provisioning Systems from Beaker
--------------------------------

Credentials
+++++++++++

To authenticate with Beaker, you will need to create a Beaker
credentials section within your scenario descriptor file. Below is an example
credentials section with all available Beaker credential keys.  You must set
either keytab and keytab_principal or username and password.

.. code-block:: yaml

    ---
    credentials:
      - name: beaker
        hub_url: <Beaker server url>
        keytab: <your keytab file, must be in your scenario workspace dir>
        keytab_principal: <The principal value for your keytab>
        username: <username>
        password: <password>

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - name
        - The name of the Beaker credentials section.
        - String
        - True

    *   - hub_url
        - The beaker server url.
        - String
        - False

    *   - keytab
        - name of the keytab file, which must be placed in the scenario
          workspace directory.
        - String
        - False

    *   - keytab_principal
        - The principal value of the keytab.
        - String
        - False

    *   - username
        - Beaker username.
        - String
        - False

    *   - password
        - Beaker username's password.
        - String
        - False

Provision Resource
++++++++++++++++++

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
        - The name to identify the node.
        - String
        - True

    *   - role
        - The name of the role for the node.
        - String
        - True

    *   - provider
        - The name of the provider. (beaker)
        - String
        - True

    *   - provisioner
        - The name of the provisioner to use to boot nodes.
        - String
        - False

    *   - credential
        - The name of the credentials to use to boot node. This is the one
          defined in the credentials section of the scenario descriptor.
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

Example
+++++++

.. code-block:: yaml

    ---
    name: Beaker example
    description: Get a specific RHEL7 distro

    credentials:

      - name: beaker
        keytab:
        keytab_principal:

    provision:

      - name: Machine from Beaker
        role: bkr-machine
        provider:
          name: beaker
          credential: beaker
          arch: x86_64
          variant: Server
          whiteboard: Testing machine provisioning from Carbon
          distro: RHEL-7.4-20170621.0


.. _openstack_provisioning:

Provisioning Systems from OpenStack
-----------------------------------

Credentials
+++++++++++

To authenticate with OpenStack, you will need to create an OpenStack
credentials section within your scenario descriptor file. Below is an example
credentials section with all available OpenStack credential keys.

.. code-block:: yaml

    ---
    credentials:
      - name: openstack
        auth_url: <auth_url>
        tenant_name: <tenant_name>
        username: <username>
        password: <password>
        region: <region>

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - name
        - The name of the OpenStack credentials section.
        - String
        - True

    *   - auth_url
        - The authentication URL of your OpenStack tenant. (identity)
        - String
        - True

    *   - tenant_name
        - The name of your OpenStack tenant.
        - String
        - True

    *   - username
        - The username of your OpenStack tenant.
        - String
        - True

    *   - password
        - The password of your OpenStack tenant.
        - String
        - True

    *   - region
        - The region of your OpenStack tenant to authenticate with.
        - String
        - False

Provision Resource
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
          credential: beaker
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
        - The name of the node to boot.
        - String
        - True

    *   - role
        - The name of the role for the node.
        - String
        - True

    *   - provider
        - The name of the provider. (openstack)
        - String
        - True

    *   - provisioner
        - The name of the provisioner to use to boot nodes.
        - String
        - False

    *   - credential
        - The name of the credentials to use to boot node. This is the one
          defined in the credentials section of the scenario descriptor.
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

Example
+++++++

.. code-block:: yaml

    ---
    name: OpenStack provider example
    description: Provision one resource in OpenStack

    credentials:
      - name: openstack
        auth_url: https://ci-rhos.centralci.eng.rdu2.redhat.com:13000/v2.0
        tenant_name: pit-jenkins
        username: username
        password: password

    provision:
      - name: test_client
        role: client
        provider:
          name: openstack
          credential: openstack
          image: Fedora-Cloud-Base-25-compose-latest
          flavor: m1.small
          networks: [pit-jenkins]
          floating_ip_pool: 10.8.240.0
          keypair: pit-jenkins

