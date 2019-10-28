Configure Carbon
================

This is a mandatory configuration file, where you set your credentials, and
there are many optional settings to help you adjust your usage of Carbon.
The credentials of the configuration file is the only thing that
is mandatory.  Most of the other default configuration settings should be
sufficient; however, please read through the options you have.

Where it is loaded from (using precedence low to high):

#. ./carbon.cfg (current working directory)
#. CARBON_SETTINGS environment variable to the location of the file

.. important::

   It is important to realize if you have a configuration file set using
   both options, the configuration files will be combined, and common
   key values will be overrided by the higher precedent option, which will
   be the CARBON_SETTINGS environment variable.

Configuration example (with all options):

.. literalinclude:: ../.examples/configuration/carbon/carbon.cfg


.. note::

    Many of the configuration options can be overridden by passing cli options when running
    carbon. See the options in the running carbon `example. <quickstart.html#run>`__

inventory_folder
~~~~~~~~~~~~~~~~

The **inventory_folder** option is not a required option but it is important enough to note its usage.
By default carbon will create an inventory directory containing ansible inventory files in its data
directory. These are used during orchestration and execution. Refer to the `Carbon Output <output.html>`__
page.

Some times this is not desired behavior. This option allows a user to specify a static known directory
that Carbon can use to place the ansible inventory files. If the specified directory does not exist,
carbon will create it and place the ansible inventory files. If it does, carbon will only place the
ansible files in the directory. Carbon will then use this static directory during orchestrate and execution.

task_concurrency
~~~~~~~~~~~~~~~~

The **task_concurrency** option is used to control how tasks are executed by Carbon. Whether it should be sequential
or in parallel/concurrent. Right now this is used to control only the execution of the Provision or Report task.
By default Provision and Report tasks will execute concurrently/parallel independent of each other.

There are cases when provisioning resources of different types that there might be an inter-dependency so executing
the tasks in parallel will not suffice. In that case, set the **provision=False** and arrange the resources defined
in the scenario descriptor file in the proper sequential order.

A valid example is when you want to provision a virtual network and you want to provision a VM attached to that
network. Arrange the resource definition so that the virtual network is provisioned first, and then the VM is
provisioned afterwards.

There are cases when you need to import the same test artifact into separate reporting systems but one reporting
systems needs the data in the test artifact to be modified with metadata before it can be imported. In that case,
set the **report=False** and arrange the resources defined in the scenario descriptor file in the
proper sequential order.

A valid example is when you want to import into Polarion but need to modify the test artifact with Polarion
metadata and then import that same artifact into Report Portal. Arrange the resource definition so that
either the Polarion conversion and import happens before or after the import into Report Portal.

