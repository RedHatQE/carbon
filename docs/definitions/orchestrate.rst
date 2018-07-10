Orchestrate
===========

The orchestrate section is for defining what configuration needs to be done
to the test systems.  At the moment, only ansible is supported.

Overview
--------

The following is an example of what the orchestration section looks like.

.. literalinclude:: ../../examples/template.yml
   :lines: 82-100

The following is a definition of the key/values required to define a
configuration action in the orchestrate section.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - name
        - The name of the playbook to execute.
        - String
        - True

    *   - orchestrator
        - The orchestrator that is being used (Default: ansible).
        - String
        - False

    *   - hosts
        - lists of hosts where the configuration will be applied.
        - list
        - True

    *   - vars
        - A dicitionary of key value variables and values to pass to the
          configuraiton script.
        - dictionary
        - False

Resources:
----------

For system configuration & product installs use roles from: `Oasis Roles`_

.. _Oasis Roles: https://github.com/oasis-roles

For some common configuration & test setup use playbooks from:
`Common PIT Playbooks`_

.. _Common PIT Playbooks: https://gitlab.cee.redhat.com/PIT/carbon-playbooks
