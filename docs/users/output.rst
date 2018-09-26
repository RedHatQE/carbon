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

The following is a snippet of results.yml after provisioning an OpenStack
system was complete.  As you can see, the ip_address was added to the top level
of the resource definition and hostname and node_id were added under the
provider, the added data has been highlighted.

.. code-block:: bash
  :emphasize-lines: 7,13,14

  ...
  name: ffdriver
  provider:
    credential: openstack
    flavor: m1.small
    floating_ip_pool: <definied ip pool>
    hostname: ffdriver_l3zqh
    image: rhel-7.5-server-x86_64-released
    keypair: pit-jenkins
    name: openstack
    networks:
    - pit-jenkins
    node_id: 4beb3789-1e61-4f7c-bf9e-722ed480b280
  ip_address: 10.8.249.2
  ...

.. note::

   Each task will also keep overwriting the results.yml in the data folder
   under the .results folder. To help continue on from the last task that
   failed, you can pass the <data_folder>/results.yml as the scenario to
   continue running from where it left off, by selecting to run just the
   remaining tasks.
