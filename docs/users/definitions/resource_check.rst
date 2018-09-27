Resource Check
==============

Carbon's Resource Dependency Check Section is optional. It specifies a list of
external resource component names whose status will be checked before proceeding
to run the scenario. If all components are up the scenario will be executed.
If one or more components are down the scenario will exit with an error. It will
also indicate if a component name given is invalid.

The key "resource_check_endpoint" must be set in the carbon.cfg file to actually
perform check. If not set this section is ignored. The "resource_check_endpoint"
must be the URL of a "Cachet" status page endpoint. Component names must be valid
for that status page.

Examples
--------

Example 1
~~~~~~~~~

List format 1.

.. literalinclude:: ../../../examples/docs-usage/resource_check.yml
    :lines: 1-30

Example 2
~~~~~~~~~

List format 2.

.. literalinclude:: ../../../examples/docs-usage/resource_check.yml
    :lines: 32-51

Please look at this `template <https://gitlab.cee.redhat.com/PIT/carbon/examples/blob/master/e2e/template.yml>`_
for details on what a complete scenario descriptor should look like.

