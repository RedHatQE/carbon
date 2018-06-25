Welcome to Carbon!
==================

What is Carbon?
---------------

Carbon is a framework developed in Python to perform interoperability testing
and multi-product scenario testing. Carbon handles coordinating the E2E
(end to end) task workflow to drive the scenario execution.

What does an E2E workflow consist of?
-------------------------------------

At a high level carbon executes the following tasks when processing a scenario.

   - Provision system resources
   - Perform system configuration
   - Install products
   - Configure products
   - Install test frameworks
   - Configure test frameworks
   - Execute tests
   - Report results
   - Destroy system resources

Carbon was developed with a model of "plug-in-play". Meaning you can easily
interface with various tools, endpoints, etc to perform one of the given
tasks.

.. note::

    Carbon can interface with an external tool to provision system resources
    for the scenario. It could also interface with an external tool to report
    results to the product owners.

.. toctree::
    :hidden:

    install
    architecture
    scenario_descriptor
    configuration
    examples
    output
    development
    changelog
    contact