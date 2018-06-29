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
        auth_url: <Beaker server url>
        keytab: <your keytab file, must be in your assets directory>
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

    *   - auth_url
        - The beaker server url.
        - String
        - False

    *   - keytab
        - name of the keytab file, which must be placed in the assets directory.
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
        provider: openstack
        provisioner: <provisioner>
        credential: <credential>
        metadata: <dict_key_values>
        ansible_params: <dict_key_values>
        bkr_arch: <arch>
        bkr_variant: <variant>
        bkr_family: <family>
        bkr_distro: <os_distro>
        bkr_whiteboard: <whiteboard>
        bkr_jobgroup: <group_id>
        bkr_tag: <tag>
        bkr_host_requires_options: [<list of host options>]
        bkr_distro_requires_options: [<list of distro options>]
        bkr_virtual_machine: <True or False>
        bkr_virt_capable: <True or False>
        bkr_priority: <priority of the job>
        bkr_retention_tag: <retention tag>
        bkr_timeout: <timeout val for Beaker job>
        bkr_kernel_options: [<list of kernel options>]
        bkr_kernel_post_options: [<list of kernel post options>]
        bkr_kickstart: < Filename of kickstart file>
        bkr_ignore_panic: <True or False>
        bkr_taskparam: [<list of task parameter settings>]
        bkr_ksmeta: [<list of kick start meta OPTIONS>]

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

    *   - bkr_arch
        - The arch of the node.
        - String
        - True

    *   - bkr_variant
        - The OS variant of the node.
        - String
        - True

    *   - bkr_family
        - The OS family of the node. (family or distro needs to be set)
        - String
        - False

    *   - bkr_distro
        - The specific OS distribution. (family or distro needs to be set)
        - String
        - False

    *   - bkr_whiteboard
        - The name to set for the Beaker whiteboard to help identify your job.
        - String
        - False

    *   - bkr_jobgroup
        - The name of the beaker group to set, of who can see the machines and used for machine searching.
        - String
        - False

    *   - bkr_tag
        - The name of a tag to get the correct OS (i.e. RTT-ACCEPTED).
        - String
        - False

    *   - bkr_host_requires_options
        - List of host options with the format:["<key><operand><value>"].
        - List
        - False

    *   - bkr_distro_requires_options
        - List of OS options with the format:["<key><operand><value>"].
        - List
        - False

    *   - bkr_kernel_options
        - List of bkr kernel options during install with the format:["<key><operand><value>"]
        - List
        - False

    *   - bkr_kernel_options_post
        - List of bkr kernel options after install with the format:["<key><operand><value>"]
        - List
        - False

    *   - bkr_virtual_machine
        - Look for a node that is a virtural machine.
        - Boolean
        - False

    *   - bkr_virt_capable
        - Look for a machine that is virt capable.
        - Boolean
        - False

    *   - bkr_priority
        - Set the priority of the Beaker job.
        - String
        - False

    *   - bkr_retention_tag
        - Set the tag value of how long to keep the job results.
        - String
        - False

    *   - bkr_ssh_key
        - Name of the ssh key to inject to the test system, file must be
          placed in assets directory.
        - String
        - False

    *   - bkr_username
        - username of the bkr machine, required if using bkr_ssh_key.
        - String
        - False

    *   - bkr_password
        - password of the bkr machine, required if using bkr_ssh_key.
        - String
        - False

    *   - bkr_timeout
        - Set a value of how long to wait for the Beaker job in seconds.(Default is 8hrs = 28800)
        - Boolean
        - False

    *   - bkr_kickstart
        - Name of the kickstart template for installation, the file must be
          placed in assets directory.
        - String
        - False

    *   - bkr_ignore_panic
        - Do not abort job if panic message appears on serial console
        - Boolean
        - False

    *   - bkr_taskparam
        - parameter settings of form NAME=VALUE that will be set for every task in job
        - List
        - False

    *   - bkr_ksmeta
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
        provider: beaker
        credential: beaker
        role: bkr-machine
        bkr_arch: x86_64
        bkr_variant: Server
        bkr_whiteboard: Testing machine provisioning from Carbon
        bkr_distro: RHEL-7.4-20170621.0


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
        provider: openstack
        provisioner: <provisioner>
        credential: <credential>
        metadata: <dict_key_values>
        ansible_params: <dict_key_values>
        os_image: <image>
        os_flavor: <flavor>
        os_networks: <networks>
        os_floating_ip_pool: <floating_ip_pool>
        os_keypair: <keypair>

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

    *   - os_image
        - The name or ID of the image to boot.
        - String
        - True

    *   - os_flavor
        - The name or ID of the flavor to boot.
        - String
        - True

    *   - os_networks
        - The name of the internal network to attach node too.
        - List
        - True

    *   - os_floating_ip_pool
        - The name of the external network to attach node too.
        - String
        - False

    *   - os_keypair
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
        provider: openstack
        credential: openstack
        os_image: Fedora-Cloud-Base-25-compose-latest
        os_flavor: m1.small
        os_networks: [pit-jenkins]
        os_floating_ip_pool: 10.8.240.0
        os_keypair: pit-jenkins

