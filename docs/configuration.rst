Configure Carbon
================

This is an optional configuration file to help you adjust your settings you
use when running Carbon.  The default configuration should be sufficient;
however, please read through the options you have.

Where it is loaded from (using precedence low to high):

#. /etc/carbon/carbon.cfg (global configuration file)
#. ./carbon.cfg (current working directory)
#. CARBON_SETTINGS environment variable to the location of the file

Configuration example (with all options):

.. literalinclude:: ../examples/carbon.cfg


.. note::

    Many of the configuration options can be overridden by passing cli options when running
    carbon. See the options in the running carbon `example. <examples.html#run>`__
