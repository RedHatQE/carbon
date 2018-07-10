Running
=======

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
      create    Create a scenario configuration.
      run       Run a scenario configuration.
      validate  Validate a scenario configuration.

Run
---

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
      -d, --data-folder               Scenario workspace path.
      -a, --assets-path               Scenario workspace path.
      --log-level [debug|info|warning|error|critical]
                                      Select logging level. (default=info)
      --help                          Show this message and exit.

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

    *   - assets-path
        - The assets path is the directory path to where all assets are for
          your scenario. Assets may include SSH private keys, etc.
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
        cbn.load_from_yaml(safe_load(f))

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
        cbn.load_from_yaml(safe_load(f))

    # individual task
    cbn.run(tasklist=['task'])

    # multiple tasks
    cbn.run(tasklist=['task', 'task'])

.. Mention about how they can pick up at a certain task

Create
------

The create command provides a helper for dynamically creating your scenario
descriptor.  This command is currently not implemented.

Validate
--------

The validate command validates the scenario descriptor.

.. code-block:: bash

    $ carbon validate --help
    Usage: carbon validate [OPTIONS]

      Validate a scenario configuration.

    Options:
      -s, --scenario                  Scenario definition file to be executed.
      -d, --data-folder               Scenario workspace path.
      --log-level [debug|info|warning|error|critical]
                                      Select logging level. (default=info)
      -a, --assets-path               Scenario workspace path.
      --help                          Show this message and exit.
