Using Resource Labels
=====================

Carbon 1.6.0 provides users with the ability to apply labels to each of the resources in the scenario descriptor file
(SDF). This can be done by adding a key **labels** to the resources (assets, actions, executes,reports) in the SDF
This is an optional feature.

While issuing the Carbon run/validate command a user can provide **--labels or -l** or **--skip-labels or -sl**.
Based on the switch provided Carbon will either pick all the resources that belong to that label for a given task
OR skip all the resources that belong to the skip-label

Labels allows Carbon to pick desired resources for a task during carbon run and validate.
For every task Carbon looks for the resources matching every label provided at the cli. If it does
not find any resources for that label, it does not perform that task. If no labels/skip-labels are provided
Carbon considers all the resources that belong to a task

If labels are being used in the SDF and while running a carbon run/validate command a label which is not present in the
SDF is given, Carbon will raise an error and exit.

.. note::

         **--labels and --skip-labels are mutually exclusive. Only one of the either can be used**

Providing labels in the SDF
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Labels can be provided as comma separated values or as a list in the SDF

.. code-block:: yaml

   ---
   provision:

  - name: laptop
    groups: localhost
    ip_address: 127.0.0.1
    ansible_params:
      ansible_connection: local
    labels: abc,pqr

  - name: laptop1
    groups: localhost
    ip_address: 127.0.0.1
    ansible_params:
      ansible_connection: local
    labels: abc

To run a task using labels
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   carbon run -s scenario.yml --labels prod_a -t provision -w . --log-level info

To run a task using skip-labels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   carbon run -s scenario.yml --skip-labels prod_a -t provision -t orchestrate -w . --log-level info

To run a task using more than one labels or skip-labels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You can provide or skip  more than one label at a time

.. code-block:: bash

   carbon run -s scenario.yml --labels prod_a --labels prod_b -t provision -w . --log-level info

   carbon run -s scenario.yml -l prod_a -l prod_b -t provision -w . --log-level info

   carbon run -s scenario.yml -skip-labels prod_a -skip-labels prod_b -t provision -w . --log-level info

   carbon run -s scenario.yml -sl prod_a -sl prod_b -t provision -w . --log-level info


Examples
~~~~~~~~

.. literalinclude:: ../../examples/docs-usage/resource_labels.yml
    :lines: 1-50

Example 1
+++++++++

Using the above SDF example to run provision on resources with labels prod_a and prod_b. Here it will provision
**db2_ci_test_client_a** and **laptop** assets

.. code-block:: bash

   carbon run -s resource_labels.yml --labels prod_a --labels prod_b -t provision -w . --log-level info


Example 2
+++++++++

Using the above SDF example to run provision and orchestrate on resources with labels abc and prod_b.
Here it will provision only asset **laptop** and there will be no provision task for label prod_b
It will then run orchestrate task **ansible/install-certs.yml** with label prod_b only as there is no
orchestrate resource with label abc

.. code-block:: bash

   carbon run -s resource_labels.yml --labels abc --labels prod_b -t provision -t orchestrate -w . --log-level info


Example 3
+++++++++

Using the above SDF example to skip resources with label prod_a
Here carbon will run through all its tasks only on resources which do not match the label prod_a1
So assets **laptop and laptop1** will be provisioned and orchestrate task **ansible/install-certs.yml**
will be executed

.. code-block:: bash

   carbon run -s resource_labels.yml --skip-labels prod_a -w . --log-level info


Example 4
+++++++++

To run a task with wrong label 'prod_c' which does not exist in the SDF along with a correct label .
Here Carbon will throw an error and exit as it does not find the label prod_c

.. code-block:: bash

   carbon run -s resource_labels.yml --labels prod_c -labels prod_a -t provision -w . --log-level info
