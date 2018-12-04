Credentials
===========

For each resource that needs to be provisioned, credentials are required.
These credentials will be set in the required `carbon.cfg file
<../configuration.html#carbon-configuration>`_, and the credential name will be
referenced in your scenario descriptor file in the provision section for each
resource that is defined.

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
