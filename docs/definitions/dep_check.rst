Dependency Check
================

Carbon's Dependency Check Section is optional. It specifies a list of
external components whose status will be checked before proceeding to
run the scenario. If all components are up the scenario will be executed.
If one or more components are down the scenario will exit with an error.

The key "dep_check_endpoint" must be set in the carbon.cfg file to actually
perform check. If not set this section is ignored. The "dep_check_endpoint"
must be a "Cachet" status page that supports specific components. See
components listed below.

Dependency Check Section (with all available components):

.. literalinclude:: ../../examples/docs-usage/dep_check.yml
    :lines: 1-12

Examples
--------

Example 1
~~~~~~~~~

List format 1.

.. literalinclude:: ../../examples/docs-usage/dep_check.yml
    :lines: 14-20

Example 2
~~~~~~~~~

List format 2.

.. literalinclude:: ../../examples/docs-usage/dep_check.yml
    :lines: 22-23

Example 3
~~~~~~~~~

Gerrit component and endpoint url in list format 1.

.. literalinclude:: ../../examples/docs-usage/dep_check.yml
    :lines: 25-29

Example 4
~~~~~~~~~

Gerrit component and endpoint url in list format 2.

.. literalinclude:: ../../examples/docs-usage/dep_check.yml
    :lines: 31-32

