Carbon
======

Carbon is a project which provides a easy to use framework for creating
product interoperability scenarios to support interoperability testing.

What drives carbon is the scenario descriptor file (YAML formatted). Carbon
loads the descriptor and builds a list of pipelines to be executed. Each
pipeline contains tasks related to the resources. A resource can be a
scenario, a host, an action or a report. Each resource will contain many
tasks that the framework will collect in the descriptor file.

i.e. If an action has a task of type ValidateTask, carbon will collect it and
add it to the validate pipeline.

When you run your scenario descriptor via carbon, carbon will execute the
following:

1. Validate your scenario attributes (all resources)
2. Provision the machines defined (hosts)
3. Configure all machines accordingly (actions)
4. Install packages for each host (actions)
5. Run your tests (execute)
6. Report the results (reports)

To find out more about carbon please visit the sphinx documentation.
