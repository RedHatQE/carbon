Beaker
------

Carbon framework supports Beaker as a provider to provision and teardown
nodes. This page will help you understand the required keys that are needed
within your scenario descriptor file to provision resources using Beaker.

Assets
++++++

Assets are any files that are needed by the Provider, the following Beaker
keys are assets: **keytab** and **bkr_ssh_key**. They must reside in the
assets directory.


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

Resources
+++++++++

To provision resources from Beaker, you will need to create a Beaker
resource section within your scenario descriptor file. Below is an example
resource section with the available Beaker provider keys.

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
        - filename of the kickstart template for installation
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

Examples
++++++++

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


.. code-block:: yaml

    ---
    name: Beaker example
    description: Get a machine from Beaker

    credentials:

      - name: beaker
        keytab:
        keytab_principal:

    provision:

      - name: Machine from Beaker
        provider: beaker
        credential: beaker
        role: bkr-machine
        # required keys - arch and variant
        bkr_arch: x86_64
        bkr_variant: Server

        # either distro or family needs to be set
        bkr_family: RedHatEnterpriseLinux7

        # the rest are optional values, it is good idea to have a whiteboard value set
        # also a really good idea to have your jobgroup set, if using a keytab
        bkr_whiteboard: VJP - Testing machine provisioning from Carbon
        bkr_jobgroup: ci-ops-pit

        # bkr_tag cannot be set in conjuction w/bkr_distro, should be set w/bkr_family
        bkr_tag: "RTT_ACCEPTED"
        bkr_host_requires_options: ["memory>=1000", "hostname=rowlf.dqe.lab.eng.bos.redhat.com"]
        bkr_distro_requires_options: ["method=nfs"]

        # Virt options
        bkr_virtual_machine: False
        bkr_virt_capable: True

        # possible values for priority: Low, Medium, Normal, High, Urgent"
        bkr_priority: Urgent
        bkr_retention_tag: 60days
        
        # inject ssh key into Beaker machine
        bkr_ssh_key: <my_private_ssh_key>
        bkr_username: <username of Beaker system>
        bkr_password: <password of Beaker user>

        # timeout for the beaker job, default if not set is 8hrs = 28800
        # can only set values between 1hr(3600) and 48hrs(172800)
        bkr_timeout: 172800

        # possible values for ignore panic: True, False
        bkr_ignore_panic: True
    
        # Filename of the kickstart file to execute
        bkr_kickstart: <kickstart filename>

        # Only taskparam value supported currently is RESERVETIME
        # Set as seconds - Reserve system for 2 days
        bkr_taskparam: RESERVETIME=172800

        # kick start meta data OPTIONS - list
        bkr_ksmeta: ["<key>=<value>"]

        # Host metadata
        metadata:
          user: root
          password: root
        # Example with ansible parameters defined
        ansible_params:
          # 'ansible_' will always be appended if not given
          user: root
          ssh_pass: root
          -- or --
          ansible_user: root
          ansible_ssh_pass: root
