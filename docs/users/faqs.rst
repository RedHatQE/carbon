FAQS
====

The following are some answers to frequently asked questions about Carbon.

How Do I...
-----------

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

... pass data from playbook to playbook using carbon?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See the `Data Pass-through Section
<data_pass_through.html#data-pass-through>`_

... see the current issues logged against carbon?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See the list of current `Issues
<https://projects.engineering.redhat.com/secure/CreateIssue!default.jspa>`_
logged against carbon.
