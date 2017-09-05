Openshift
---------

Carbon framework supports OpenShift as a provider to provision and teardown
applications. This page will help you understand the required keys that are
needed within your scenario descriptor file to provision applications in
OpenShift.

Credentials
+++++++++++

To authenticate with OpenShift, you will need to create an OpenShift
credentials section within your scenario descriptor file.

If using your username and token, which is the preferred method, you can
either get it from the Openshift UI or using oc command line tool:

Using the Openshift UI:
~~~~~~~~~~~~~~~~~~~~~~~

In the top right of the OpenShift interface, select the ? -> Command Line
Tools.  From there, you see textboxes, after the first uneditable textbox
(which discusses a session token), click the clipboard button to copy the
token to your clipboard.

Using the oc command line tool:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    $ oc whoami --show-token

Below is an example credentials section with all available OpenShift credential keys.

.. code-block:: yaml

    ---
    credentials:
      - name: openshift
        auth_url: <auth_url>
        project: <project>
        token: <token>
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
        - The name of the OpenShift credentials section.
        - String
        - True

    *   - auth_url
        - The authentication URL of your OpenShift instance.
        - String
        - True

    *   - project
        - The name of the project to create applications within. This project
          should already exists in your OpenShift instance.
        - String
        - True

    *   - token
        - The token to be used for authentication.
        - String
        - False

    *   - username
        - The username to be used for authentication. Requires password key.
        - String
        - False

    *   - password
        - The password to be used for authentication. Requires username key.
        - String
        - False

Resources
+++++++++

To provision resources (applications) within OpenShift, you will need to
create an OpenShift resource section within your scenario descriptor file.
Below is an example resource section with all available OpenShift provider
keys.

.. code-block:: yaml

    ---
    provision
      - name: <name>
        role: <role>
        provider: openshift
        provisioner: <provisioner>
        credential: <credential>
        metadata: <dict_key_values>
        oc_image: <image>
        oc_git: <git>
        oc_template: <template>
        oc_custom_template: <custom_template>
        oc_env_vars: <env_vars>
        oc_labels: <labels>
        oc_build_timeout: <timeout>

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - name
        - The name of the application to boot.
        - String
        - True

    *   - role
        - The name of the role for the application.
        - String
        - True

    *   - provider
        - The name of the provider. (openshift)
        - String
        - True

    *   - provisioner
        - The name of the provisioner to use to boot applications.
        - String
        - False

    *   - credential
        - The name of the credentials to use to boot application. This is the
          one defined in the credentials section of the scenario descriptor.
        - String
        - True

    *   - oc_image
        - The name of the image to boot the application based on.
        - String
        - False

    *   - oc_git
        - The git URL to boot the application based on.
        - String
        - False

    *   - oc_template
        - The template name to boot the application based on.
        - String
        - False

    *   - oc_custom_template
        - Name of the custom template file that defines your application,
          which must be placed in assets directory.
        - String
        - False

    *   - oc_env_vars
        - Environment variables to inject into application when booted.
        - Dictionary
        - False

    *   - oc_labels
        - Labels to be associated with the booted application.
        - List of dictionaries
        - True

    *   - oc_build_timeout
        - The duration to wait for an application to finish building and pods
          to be up and running, default value is set to 1800, which is 30
          minutes.
        - Integer
        - False

    *   - metadata
        - Data that the resource may need access to after provisioning is
          finished. This data is passed through and is not modified by carbon
          framework.
        - Dict
        - False

Examples
++++++++

.. code-block:: yaml

    ---
    name: Openshift image example
    description: Provision application in Openshift based on a image

    credentials:
      - name: openshift
        auth_url: https://osemaster.sbu.lab.eng.bos.redhat.com:8443
        project: myproject
        token: token

    provision:
      - name: Application by image
        provider: openshift
        credential: openshift
        role: application_image
        oc_image: rywillia/example
        oc_env_vars:
          var1: var1
          var2: var2
        oc_labels:
          - label1: label1
          - label2: image_app

.. code-block:: yaml

    ---
    name: Openshift git example
    description: Provision application in Openshift based on a git

    credentials:
      - name: openshift
        auth_url: https://osemaster.sbu.lab.eng.bos.redhat.com:8443
        project: myproject
        token: token

    provision:
      - name: Application by git
        provider: openshift
        provisioner: openshift
        credential: openshift
        oc_build_timeout: 3600
        role: application_git
        oc_git: https://github.com/openshift/django-ex
        oc_env_vars:
          var1: var1
          var2: var2
        oc_labels:
          - label1: label1
          - label2: git_app

.. code-block:: yaml

    ---
    name: Openshift default template example
    description: Provision applications in Openshift based on a default template

    credentials:
      - name: openshift
        auth_url: https://osemaster.sbu.lab.eng.bos.redhat.com:8443
        project: myproject
        token: token

    provision:
      - name: Application by pre-defined template
        provider: openshift
        credential: openshift
        role: application_template
        oc_template: jws30-tomcat7-basic-s2i
        oc_env_vars:
          JWS_ADMIN_USERNAME: jwsadmin
          JWS_ADMIN_PASSWORD: jwsadmin
          APPLICATION_NAME: tomcat-app
        oc_labels:
          - label1: label1
          - label2: predefinedtemplate_app

.. code-block:: yaml

    ---
    name: Openshift custom template example
    description: Provision applications in Openshift based on a custom template

    credentials:
      - name: openshift
        auth_url: https://osemaster.sbu.lab.eng.bos.redhat.com:8443
        project: myproject
        token: token

    provision:
      - name: Application by custom template
        provider: openshift
        provisioner: openshift
        credential: openshift
        role: application_custom_template
        oc_custom_template: mytemplate.yaml
        oc_env_vars:
          var1: var1
          var2: var2
        oc_labels:
          - another_label: customtemplate_app
