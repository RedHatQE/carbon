FAQS
====

The following are some answers to frequently asked questions about Carbon.

How Do I...
-----------

Provision
+++++++++

... call carbon using static machines?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You need to define the machine as a static machine in the carbon definition
file.  See `Defining Static Machines
<definitions/provision.html#definining-static-machines>`_ for details.

... run scripts on my local system?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You need to define your local system as a static resource.
See `The localhost example for provisioning
<definitions/provision.html#localhost-example>`_ for details.

... run carbon and not delete my machines at the end of the run?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default when running carbon, you will run all of carbon's tasks; however,
you also have the option to pick and choose which tasks you would like to run,
and you can specify it with -t or --task.  By using this option, you can
specify, all tasks, and just not specify cleanup.  See `Running Carbon
<quickstart.html#run>`_ for more details.

... know whether to use the Linchpin provisioner?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Its recommended new users onbaording with carbon or new scenarios
being developed to use the Linchpin provisioner. Its being adopted as
the standard provisioning tool and supports a lot more resource providers
that can be enabled in carbon. If you have a pre-existing scenario that is
not using a carbon native provisioner specific parameter is also a good
candidate to migrate over to using the Linchpin provisioner.

If the pre-existing scenarios use carbon native provisioner specific parameters
that Linchpin does not support you will need to continue to use those until Lincphin
supports the parameter. Linchpin's python 3 support is still experimental and not
fully supported so Linchpin will not be installed by carbon in python 3 environments.

... know if my current scenarios will work with the new Linchpin provisioner?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You can add the provisioner key to use the linchpin-wrapper and run the validate
command

.. code-block:: bash

    carbon validate -s <scenario.yml>

This will diplay warnings on which resource parameters may be supported
and error out on parameters that are not supported by the provisioner. Resolve
any of the warnings and failures. Once validate passes then the scenario should
be Linchpin compatible.


Orchestrate
+++++++++++

... pass data from playbook to playbook using carbon?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See the `Data Pass-through Section
<data_pass_through.html#data-pass-through>`_


Miscellaneous
+++++++++++++

... see the current issues logged against carbon?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See the list of current `Issues
<https://projects.engineering.redhat.com/secure/CreateIssue!default.jspa>`_
logged against carbon.
