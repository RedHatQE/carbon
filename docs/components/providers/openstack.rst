Openstack
---------

Carbon framework supports OpenStack as a provider to provision and teardown
nodes. This page will help you understand the required keys that are needed
within your scenario descriptor file to provision resources in OpenStack.

Credentials
+++++++++++

To authenticate with OpenStack, you will need to create a OpenStack
credentials section within your scenario descriptor file. Below is an example
of defining credentials for an OpenStack tenant.

.. code-block:: yaml
    :linenos:

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
        - The name of the openstack credentials section to reference to
          resources to be provisioned.
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

To provision resources within OpenStack, you will need to create a OpenStack
resource section within your scenario descriptor file. Below is an example
of a resource to provision in OpenStack.

.. code-block:: yaml
    :linenos:

    ---
    provision:
      - name: <name>
        role: <role>
        provider: openstack
        credential: <credential>
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
        - Name of the provider (openstack)
        - String
        - True

    *   - provisioner
        - Name of the provisioner to use to boot node.
        - String
        - False

    *   - credential
        - Name of the credentials to used defined in the scenario descriptor.
        - String
        - True

    *   - os_image
        - Name or ID of the image to boot.
        - String
        - True

    *   - os_flavor
        - Name or ID of the flavor to boot.
        - String
        - True

    *   - os_networks
        - Name of the internal network to attach node too.
        - List
        - True

    *   - os_floating_ip_pool
        - Name of the external network to attach node too.
        - String
        - True

    *   - os_keypair
        - Name of the keypair to associate node with.
        - String
        - True

Examples
++++++++

.. code-block:: yaml
    :linenos:

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
    :linenos:

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