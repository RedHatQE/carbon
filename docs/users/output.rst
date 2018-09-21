Carbon Output
=============

Overview
--------

Carbon produces its output in the data folder, by default this folder will be
the /tmp directory unless specified by the user.

For each task that carbon runs, it will create an updated version of the
descriptor file with results from the task (results.yml), so the user can
continue execution after the last successful task, and not be forced to start over.

Carbon Output Files
-------------------

For each run, carbon will create a folder with a UUID in the data folder path.
The main output will be:

#. logs of the run (under the logs directory of that run). (carbon.log and ansible.log, if set)
#. results.yml (updated descriptor that will be updated after each successful task)

The following is a snippet of results.yml after a provisioning of an OpenStack
system was complete (os_name, os_ip_address, and os_node_id added - shown highlighted)
has been added to the default descriptor:

.. code-block:: bash
  :emphasize-lines: 9,10,12,13

  ...
  name: ffdriver
  os_admin_pass: null
  os_description: null
  os_files: null
  os_flavor: m1.small
  os_floating_ip_pool: 10.8.240.0
  os_image: rhel-7.5-server-x86_64-released
  os_ip_address:
  - 10.8.249.2
  os_keypair: pit-jenkins
  os_name: cbn_ffdriver_agqrs
  os_node_id: 4beb3789-1e61-4f7c-bf9e-722ed480b280
  ...

.. note::

   Each task will also keep overwriting the results.yml in the data folder
   under the .results folder. To help continue on from the last task that
   failed, you can pass the <data_folder>/results.yml as the scenario to
   continue running from where it left off, by selecting to run just the
   remaining tasks.
