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

Configuration example (with all options):

.. literalinclude:: ../.examples/configuration/carbon/carbon.cfg


.. note::

    Many of the configuration options can be overridden by passing cli options when running
    carbon. See the options in the running carbon `example. <quickstart.html#run>`__
