Scenario Descriptor
===================

This page is intended to explain the input to carbon. The goal and focus behind
carbons input is to be simple and transparent. It uses common language to
describe the entire scenario (E2E). The input is written in YAML. The term
used to reference carbons input is a scenario descriptor file. You will hear
this throughout carbons documentation.

Every scenario descriptor is broken down into different mappings. Each mapping
relates to a particular component within carbon. You can learn about this at
the `architecture <architecture.html>`_ page. Below are sub pages which go
into further detail explaining the different mappings.

.. toctree::
    :maxdepth: 1

    definitions/credentials
    definitions/provision
    definitions/orchestrate
    definitions/execute
    definitions/report

When we put all of these mappings together, we have a complete scenario to
provide to carbon. Below is an example scenario descriptor:

.. note::

    This scenario descriptor may be subject to change.

.. literalinclude:: ../examples/template.yml