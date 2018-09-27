Quick Start
-----------

.. attention::

       Quickstart examples need to be added!, coming soon.

Carbon Installation
~~~~~~~~~~~~~~~~~~~

Requirements
++++++++++++

Your system requires the following packages to install carbon:

.. code-block:: bash

    # To install git using dnf package manager
    $ sudo dnf install -y git

    # To install git using yum package manager
    $ sudo yum install -y git

    # Install python pip: https://pip.pypa.io/en/stable/installing
    $ sudo curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    $ sudo python get-pip.py

    # Recommend installation of virtualenv using pip
    $ sudo pip install virtualenv

Installation
++++++++++++

Install carbon from source:

.. code-block:: bash

    # for ansible modules requiring selinux, you will need to enable system site packages
    $ virtualenv --system-site-packages carbon
    $ source carbon/bin/activate
    (carbon) $ pip install git+https://code.engineering.redhat.com/gerrit/p/carbon.git

Post Install
++++++++++++

If you require carbon to interface with beaker, you will need to enable the
beaker client repository/install the beaker-client package. Carbon uses the
beaker client package to provision physical machines in beaker.

.. code-block:: bash

    # https://beaker-project.org/download.html
    $ sudo curl -o /etc/yum.repos.d/bkr-client.repo \
    https://beaker-project.org/yum/beaker-client-<DISTRO>.repo

    # dnf package manager
    $ sudo dnf install -y beaker-client

.. note::

    Beaker-client could be installed from PyPI rather than RPM. Installing from
    pip fails in Python 3. Beaker client is not compatible with Python 3
    currently. Once compatibile it can be installed with carbon. Carbon is
    Python 2.7 & Python 3.6 compatible.


Carbon Configuration
~~~~~~~~~~~~~~~~~~~~

This is an optional configuration file to help you adjust your settings you
use when running Carbon.  The default configuration should be sufficient;
however, please read through the options you have.

Where it is loaded from (using precedence low to high):

#. ./carbon.cfg (current working directory)
#. CARBON_SETTINGS environment variable to the location of the file

Configuration example (with all options):

.. literalinclude:: ../.examples/configuration/carbon/carbon.cfg


.. note::

    Many of the configuration options can be overridden by passing cli options when running
    carbon. See the options in the running carbon `example. <examples.html#run>`__

Running Carbon
~~~~~~~~~~~~~~

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
++++++

The create command provides a helper for dynamically creating your scenario
descriptor.  This command is currently not implemented.

Validate
++++++++

The validate command validates the scenario descriptor.

.. code-block:: bash

    $ carbon validate --help
    Usage: carbon validate [OPTIONS]

      Validate a scenario configuration.

    Options:
      -s, --scenario                  Scenario definition file to be executed.
      -d, --data-folder               Directory for saving carbon runtime files.
      -w, --workspace                 Scenario workspace.
      --log-level [debug|info|warning|error|critical]
                                      Select logging level. (default=info)
      --help                          Show this message and exit.

