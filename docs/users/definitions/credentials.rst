Credentials
===========

For each resource that needs to be provisioned or artifact that needs to be 
imported, credentials are required. These credentials will be set in the required 
`carbon.cfg file <../configuration.html#carbon-configuration>`_, and the credential 
name will be referenced in your scenario descriptor file in the provision section for each
resource or artifact that is defined.

Beaker Credentials
------------------

For Beaker, the following table is a list of required and optional keys for
your credential section in your carbon.cfg file.  You must set
either keytab and keytab_principal or username and password:

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - hub_url
        - The beaker server url.
        - String
        - True

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

    *   - ca_path
        - path to a trusted certificate file
        - String
        - False


Below is an example credentials section in the carbon.cfg file.  If the
credential was defined as below, it should be referenced in your carbon
scenario descriptor by the host as **credential: beaker-creds**:

.. code-block:: bash

  [credentials:beaker-creds]
  hub_url=<hub_url>
  keytab=<keytab>
  keytab_principal=<keytab_principal>
  username=<username>
  password=<password>
  ca_path=<ca_path>

The following is an example of a resource in the scenario descriptor file
that references this credential:

.. literalinclude:: ../../.examples/provision/beaker/scenario.yml


OpenStack Credentials
---------------------

For OpenStack, the following table is a list of required and optional keys for
your credential section in your carbon.cfg file.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

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

    *   - domain_name
        - The name of your OpenStack domain to authenticate with.
          When not set carbon will use the 'default' domain
        - String
        - False


.. code-block:: bash

  [credentials:openstack-creds]
  auth_url=<auth_url>
  tenant_name=<tenant_name>
  username=<username>
  password=<password>
  region=<region>
  domain_name=<domain_name>

The following is an example of a resource in the scenario descriptor file
that references this credential:


.. literalinclude:: ../../.examples/provision/openstack/scenario.yml


Polarion Credentials
---------------------

For Polarion, the following table is a list of required keys for
your credential section in your carbon.cfg file.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - polarion_url
        - The URL you use to log into Polarion. Do not append the xunit-queue
          to the end of it.
        - String
        - True

    *   - username
        - The username that has privileges to your Polarion project. It is 
          recommended to have an automation user created with admin privileges
        - String
        - True

    *   - password
        - The password of your user to the Polarion project.
        - String
        - True

.. code-block:: bash

  [credentials:polarion-creds]
  polarion_url=<polarion_url>
  username=<username>
  password=<password>

The following is an example of a resource in the scenario descriptor file
that references this credential:

.. literalinclude:: ../../../examples/docs-usage/report.yml
    :lines: 1-8

