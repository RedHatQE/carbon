Openstack
---------

Carbon framework supports OpenStack as a provider to provision and teardown
nodes. This page will help you understand the required keys that are needed
within your scenario descriptor file to provision resources in OpenStack.

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
        tenant_id: <tenant_id>
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

    *   - tenant_id
        - The ID of your OpenStack tenant.
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

Resources
+++++++++

To provision resources within OpenStack, you will need to create an OpenStack
resource section within your scenario descriptor file. Below is an example
resource section with all available OpenStack provider keys.

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
        - True

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

Examples
++++++++

.. code-block:: yaml

    ---
    name: OpenStack provider example
    description: Provision one resource in OpenStack

    credentials:
      - name: openstack
        auth_url: http://dashboard.centralci.eng.rdu2.redhat.com:5000/v2.0
        tenant_name: pit-jenkins
        tenant_id: bf4de4c330bb47d6937af31fd5c71a18
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
        os_floating_ip_pool: 10.8.172.0/22
        os_keypair: pit-jenkins

.. code-block:: yaml

    ---
    name: OpenStack provider example
    description: Provision two resources in OpenStack

    credentials:
      - name: openstack
        auth_url: http://dashboard.centralci.eng.rdu2.redhat.com:5000/v2.0
        tenant_name: pit-jenkins
        tenant_id: bf4de4c330bb47d6937af31fd5c71a18
        username: username
        password: password

    provision:
      - name: test_client1
        role: client
        provider: openstack
        credential: openstack
        os_image: Fedora-Cloud-Base-24-compose-latest
        os_flavor: m1.small
        os_networks: [pit-jenkins]
        os_floating_ip_pool: 10.8.172.0/22
        os_keypair: pit-jenkins

      - name: test_client2
        role: client
        provider: openstack
        credential: openstack
        os_image: Fedora-Cloud-Base-25-compose-latest
        os_flavor: m1.small
        os_networks: [pit-jenkins]
        os_floating_ip_pool: 10.8.172.0/22
        os_keypair: pit-jenkins
        # Example with metadata defined
        metadata:
          username: root
          password: root
        # Example with ansible parameters defined
        ansible_params:
          # 'ansible_' will always be appended if not given
          user: root
          ssh_pass: root
          -- or --
          ansible_user: root
          ansible_ssh_pass: root
