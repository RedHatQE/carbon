Examples
========

This page is intended to provide you with detailed examples on how you can use
carbon to perform various actions. Some of the actions below may redirect you
to a git repository where further detail is given.

----

Test Setup & Execution
----------------------

This section provides you with detailed examples on how carbon can perform
test setup and execution using common test frameworks. Below you will find
sub-sections with examples for installation and execution using commonly used
test frameworks. Each framework has an associated repository containing all
necessary files to call carbon to demonstrate test setup and execution. Each
of the examples demonstrates how carbon consumes the external
automated scripts (i.e, ansible roles/playbooks, bash scripts, etc) to install
the test frameworks, and how carbon executes example tests and gets the
artifacts of the execution.

.. note::

    These frameworks below are just examples on how you can use carbon to run
    existing automation you may have to install/setup/execute using common
    test frameworks. Since carbons primary purpose is to conduct "orchestrate"
    the E2E flow of a multi-product scenario, it has the flexibility to consume
    any sort of automation to run against your scenarios test machines defined.
    This allows you to focus on building the automation to setup test
    frameworks and then just tell carbon how you wish to run it.

Junit
~~~~~

Please reference the example `junit repository`_ for all details on how you
can execute this example with carbon to run a junit example.

Pytest
~~~~~~

Please reference the example `pytest repository`_ for all details on how you
can execute this example with carbon to run a pytest example.

Restraint
~~~~~~~~~

Please reference the example `restraint repository`_ for all details on how you
can execute this example with carbon to run a restraint example.

----

.. _junit repository: https://gitlab.cee.redhat.com/PIT/carbon/junit-install-example
.. _pytest repository: https://gitlab.cee.redhat.com/PIT/carbon/pytest-install-example
.. _restraint repository: https://gitlab.cee.redhat.com/PIT/carbon/restraint-install-example
