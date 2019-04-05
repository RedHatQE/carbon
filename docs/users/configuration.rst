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

The inventory_folder option is not a required option but it is important enough to note its usage.
By default carbon will create an inventory directory containing ansible inventory files in its data
directory. These are used during orchestration and execution. Refer to the `Carbon Output <output.html>`__
page.

Some times this is not desired behavior. This option allows a user to specify a static known directory
that Carbon can use to place the ansible inventory files. If the specified directory does not exist,
carbon will create it and place the ansible inventory files. If it does, carbon will only place the
ansible files in the directory. Carbon will then use this static directory during orchestrate and execution.