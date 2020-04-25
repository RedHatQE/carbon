Carbon Quickstart
-----------------

Welcome to the carbon quick start guide! This guide will help get you started
with using carbon. This guide is broken down into two sections:

#. Carbon Usage
#. Getting Started Examples

Carbon usage will provide you with an overview of how you can call carbon.
It can be called from either a command line or invoked within a Python
module. The getting started examples section will show you working examples
for each carbon task. Each example is stored within a git repository for you
to clone and try in your local environment.

.. note::

    At this point, you should already have carbon installed and configured.
    If not, please view the `install <install.html>`_ guide and the
    `configuration <configuration.html>`_ guide.

----

Carbon Usage
~~~~~~~~~~~~

Once carbon is installed, you can run the carbon command to view its options:

.. code-block:: bash

    # OUTPUT MAY VARY BETWEEN RELEASES

    $ carbon
    Usage: carbon [OPTIONS] COMMAND [ARGS]...

      Carbon - Interoperability Testing Framework

    Options:
      -v, --verbose  Add verbosity to the commands.
      --version      Show the version and exit.
      --help         Show this message and exit.

    Commands:
      notify    Trigger notifications for a scenario configuration on demand.
      run       Run a scenario configuration.
      validate  Validate a scenario configuration.

Run
+++

The run command will run your scenario descriptor executing all tasks you
select. Below are the available run command options.

.. code-block:: bash

    # OUTPUT MAY VARY BETWEEN RELEASES

    $ carbon run --help
    Usage: carbon run [OPTIONS]

      Run a scenario configuration.

    Options:
      -t, --task [validate|provision|orchestrate|execute|report|cleanup]
                                      Select task to run. (default=all)
      -s, --scenario                  Scenario definition file to be executed.
      -d, --data-folder               Directory for saving carbon runtime files.
      -w, --workspace                 Scenario workspace.
      --log-level [debug|info]        Select logging level. (default=info)
      --vars-data                     Pass in variable data to template the
                                      scenario. Can be a file or raw json.
      -l, --labels                    Use only the resources associated with
                                      labels for running the tasks. labels and
                                      skip_labels are mutually exclusive
      -sl, --skip-labels              Skip the resources associated with
                                      skip_labels for running the tasks. labels
                                      and skip_labels are mutually exclusive
      -sn, --skip-notify              Skip triggering the specific notification
                                      defined for the scenario.
      -nn, --no-notify                Disable sending any notifications defined for
                                      the scenario.
      --help                          Show this message and exit.


.. note::
   
   If 'Include' section is present in the scenario file, carbon will aggregate and execute
   the selected tasks from both, main/parent and the included scenario file. e.g. 
   if common.yml is the included scenario file, scenario.yml is the main scenario file
   and task selected is provision,the provision pipeline is created with provision tasks 
   from included scenario followed by the provision tasks from main scenario.

----

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Option
        - Description
        - Required
        - Default

    *   - task
        - Defines which carbon task to execute the scenario against.
        - No
        - All tasks

    *   - scenario
        - This is the scenario descriptor filename. It can be either a relative
          or absoluate path to the file.
        - Yes
        - N/A

    *   - data-folder
        - The data folder is where all carbon runs are stored. Every carbon
          run will create a unique folder for that run to store its output. By
          default carbon uses /tmp as the data folder to create sub folders for
          each run. You can override this to define the base data folder.
        - No
        - /tmp

    *   - workspace
        - The scenario workspace is the directory where your scenario exists.
          Inside this directory is all the necessary files to run the
          scenario.
        - No
        - ./ (current working directory)

    *   - log-level
        - The log level defines the logging level for messages to be logged.
        - No
        - Info

To run your scenario executing all given tasks, run the following command:

.. code-block:: bash

    $ carbon run --scenario <scenario>

.. code-block:: python

    from yaml import safe_load
    from carbon import Carbon

    cbn = Carbon('carbon')

    with open('<scenario>, 'r') as f:
        cbn.load_from_yaml(list(safe_load(f)))

    cbn.run()


You have the ability to only run a selected task. You can do this by the
following command:

.. code-block:: bash

    # individual task
    $ carbon run --scenario <scenario> --task <task>

    # multiple tasks
    $ carbon run --scenario <scenario> --task <task> --task <task>

.. code-block:: python

    from yaml import safe_load
    from carbon import Carbon

    cbn = Carbon('carbon')

    with open('<scenario>, 'r') as f:
        cbn.load_from_yaml(list(safe_load(f)))

    # individual task
    cbn.run(tasklist=['task'])

    # multiple tasks
    cbn.run(tasklist=['task', 'task'])

.. Mention about how they can pick up at a certain task

Validate
++++++++

The validate command validates the scenario descriptor.

.. code-block:: bash

    $ carbon validate --help
    Usage: carbon validate [OPTIONS]

      Validate a scenario configuration.

    Options:
      -t, --task [validate|provision|orchestrate|execute|report|cleanup]
                                      Select task to run. (default=all)
      -s, --scenario                  Scenario definition file to be executed.
      -d, --data-folder               Directory for saving carbon runtime files.
      -w, --workspace                 Scenario workspace.
      --log-level [debug|info]        Select logging level. (default=info)
      --vars-data                     Pass in variable data to template the
                                      scenario. Can be a file or raw json.
      -l, --labels                    Use only the resources associated with
                                      labels for running the tasks. labels and
                                      skip_labels are mutually exclusive
      -sl, --skip-labels              Skip the resources associated with
                                      skip_labels for running the tasks. labels
                                      and skip_labels are mutually exclusive
      -sn, --skip-notify              Skip triggering the specific notification
                                      defined for the scenario.
      -nn, --no-notify                Disable sending any notifications defined for
                                      the scenario.
      --help                          Show this message and exit.

Notify
++++++

Trigger notifications marked on demand for a scenario configuration.

This is useful when there is a break in the workflow, between when the scenario
completes and the triggering of the notification.

.. code-block:: bash

    carbon notify --help
    Usage: carbon notify [OPTIONS]

        Trigger notifications marked on demand for a scenario configuration.

    Options:
        -s, --scenario            Scenario definition file to be executed.
        -d, --data-folder         Directory for saving carbon runtime files.
        -w, --workspace           Scenario workspace.
        --log-level [debug|info]  Select logging level. (default=info)
        --vars-data               Pass in variable data to template the scenario.
                                  Can be a file or raw json.
        -sn, --skip-notify        Skip triggering the specific notification
                                  defined for the scenario.
        -nn, --no-notify          Disable sending any notifications defined for the
                                  scenario.
        --help                    Show this message and exit.


.. code-block:: bash

    carbon notify -s data_folder/.results/results.yml -w .

Getting Started Examples
~~~~~~~~~~~~~~~~~~~~~~~~

This section contains examples to help get you started with carbon. A
separate `examples <https://gitlab.cee.redhat.com/qeet/carbon/examples.git>`_
repository contains all the examples that will be covered below. Please clone
this repository into your local environment to use.

Provision
+++++++++

Please visit the following `page <https://gitlab.cee.redhat.com/qeet/carbon/
examples/tree/master/provision>`__ for complete examples on using carbons
provision task.

Orchestrate
+++++++++++

Please visit the following `page <https://gitlab.cee.redhat.com/qeet/carbon/
examples/tree/master/orchestrate>`__ for complete examples on using carbons
orchestrate task.

Execute
+++++++

Please visit the following `page <https://gitlab.cee.redhat.com/qeet/carbon/
examples/tree/master/execute>`__ for complete examples on using carbons
execute task.

Report
++++++

Please visit the following `page <https://gitlab.cee.redhat.com/qeet/carbon/
examples/tree/master/report>`__ for complete examples on using carbons
report task.
