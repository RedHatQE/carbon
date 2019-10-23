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

    *   - ca_cert
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
  ca_cert=<ca_cert_path>

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


Libvirt Credentials
-------------------

For Linchpin Libvirt, the following table is a list of required and optional keys for
your credential section in your carbon.cfg file.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - create_creds
        - This is to determine if carbon should create credentials for the scenario. If
          set to **True** carbon will create a client configuration file in the
          **~/.config/libvirt** directory with the username and password provided
          and export the **LIBVIRT_AUTH_FILE** variable.

          If set to **False** carbon will not create a configuration
          file. This is to accommodate users who already have some form of pre-existing
          credentials setup with the libvirt daemon. Refer `here <https://libvirt.org/auth.html>`_
          for the different Libvirt authentication options.
        - String
        - True

    *   - username
        - The username that has privileges with the Libvirt daemon.
        - String
        - False

    *   - password
        - The password of your user to be used with the Libvirt daemon.
        - String
        - False

.. code-block:: bash

  [credentials:libvirt-creds]
  create_creds=<True/False>
  username=<username>
  password=<password>

The following is an example of a resource in the scenario descriptor file
that references this credential:

.. literalinclude:: ../../.examples/provision/linchpin/libvirt_scenario_linchpin.yml
    :lines: 7-12


AWS Credentials
---------------

For Linchpin AWS, the following table is a list of required and optional keys for
your credential section in your carbon.cfg file.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - create_creds
        - This is to determine if carbon should create credentials for the scenario.
          If set to **True** carbon will create a boto credentials file with the
          access keys provided in  **~/.aws/credentials**  and export the **AWS_PROFILE**
          variable.

          If set to **False** carbon will not create a configuration file.
          This is to accommodate users who already have some form of pre-existing
          credentials setup for AWS. Refer
          `here <https://docs.ansible.com/ansible/latest/modules/ec2_module.html#notes>`_
          for the different AWS authentication options.
        - String
        - True

    *   - aws_access_key_id
        - access key id that should be used to authenticate with AWS. This is required
          if create_creds is enabled.
        - String
        - False

    *   - aws_secret_access_key
        - The secret for the access key id to authenticate with AWS. This is required
          if create_creds is enabled.
        - String
        - False

    *   - aws_security_token
        - The security token to use when authenticating with AWS. This is optional if the
          create_creds is enabled unless the credentials provided are temporary.
        - String
        - False

.. code-block:: bash

  [credentials:aws-creds]
  create_creds=<True/False>
  aws_access_key_id=<key>
  aws_secret_access_key=<secret>
  aws_security_token=<token>

The following is an example of a resource in the scenario descriptor file
that references this credential:

.. literalinclude:: ../../.examples/provision/linchpin/aws_scenario_linchpin.yml
    :lines: 8-13


Polarion Credentials
--------------------

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

Report Portal Credentials
-------------------------

For Report Portal, the following table is a list of required and optional keys for
your credential section in your carbon.cfg file.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - create_creds
        - This is to determine if carbon should use the credentials provided in the
          carbon.cfg file or use the ones that are given in the json config file
          user supplies in the report portal provider parameters
          If set to **True** carbon will make use the optional report portal credentials
          in this table to connect to the report portal instance

          If set to **False** carbon will assume these credentials are being provided by 
          users in the report portal config json file, which can be given as a report 
          portal provider parameter. For how to configure Report Portal json file refer
          `here <https://docs.engineering.redhat.com/pages/viewpage.action?pageId=81876674#CCITReportPortalUser's
          Guide[EADraft]-ConfigurationFileDescription>`_
        - String
        - True

    *   - rp_url
        - The URL to the report portal instance
        - String
        - False

    *   - api_token
        - api token from the  report portal instance for a user account
        - String
        - False

    *   - service_url
        - This param is to use the rp_preproc service for sending
          the launch to Report Portal. It takes the value of the URL to the RP
          PreProc REST API service OR **false** in case you do not want to use
          the rp_preproc service option
        - String
        - False

.. code-block:: bash

  [credentials:reportportal-creds]
  create_creds=<True/False>
  rp_url=<report_portal_url / False>
  api_token=<token>
  service_url=<service_url>

The following is an example of a resource in the scenario descriptor file
that references this credential:

.. literalinclude:: ../../../examples/docs-usage/report.yml
          :lines: 89-96


