Best Practices
==============

Data pass-through
-----------------

Please visit the following `page <data_pass_through.html>`_ to understand how
you can pass data within carbon tasks.

Scenario Structure
------------------

.. attention::

    This document is out dated and will be updated soon! Some of this content
    will be the same just revisions are needed.

The intended focus of this section is to provide a standard structure for
building multi product scenarios. This is just a standard that can be adopted,
as a best practice, but is not required for running carbon. Having a solid
structure as a foundation will help lead to easier maintenance during the
scenarios lifespan. Along with faster turn around for creating new multi
product scenarios.

.. note::

    The advantage to a standard structure allows for other users to easily
    re-run a scenario in their environment with minimal effort.

Below is a tree formatted scenario structure for a multi product scenario.

.. code-block:: bash

    template/
    ├── ansible
    │   ├── configure_product1.yml
    │   ├── configure_product2.yml
    │   ├── install_product1.yml
    │   └── install_product2.yml
    ├── ansible.cfg
    ├── assets
    │   └── keypair
    ├── Dockerfile
    ├── Jenkinsfile
    ├── job.yml
    ├── main.yml
    ├── misc
    │   ├── build_job
    │   │   ├── ansible.cfg
    │   │   ├── group_vars
    │   │   │   └── local
    │   │   ├── inventory
    │   │   ├── jenkins.ini
    │   │   └── site.yml
    │   └── jenkins-jobs.sh
    └── README.md

The above scenario structure has additional files that are not required for
executing carbon. The extra files are used for easily running the scenario
from a Jenkins job. Below are two sections which go into more detail regarding
each file.

Carbon Files
~~~~~~~~~~~~

Based on the standard scenario structure, lets review the directories and files
which carbon consumes.

.. code-block:: bash

    template/
    ├── ansible
    │   ├── configure_product1.yml
    │   ├── configure_product2.yml
    │   ├── install_product1.yml
    │   └── install_product2.yml
    ├── ansible.cfg
    ├── assets
    │   └── keypair
    └── main.yml

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Name
        - Description
        - Required

    *   - ansible
        - The ansible directory is where you can define any ansible files
          (roles, playbooks, etc) that your scenario needs to use. Carbon will
          load and use these files as stated within your scenario descriptor
          file.
        - No

    *   - ansible.cfg
        - The ansible.cfg defines any settings for ansible that you wish to
          override their default values. It is **highly** recommend for each
          scenario to define their own file.
        - No **

    *   - assets
        - The assets directory is where you can store any sort of files that
          your scenario may require. i.e. you can store your machines private
          ssh keys there for ansible to consume.
        - No **

    *   - main.yml
        - The main.yml is your scenario descriptor. This file describes your
          entire E2E multi product scenario.
        - Yes

With this scenario structure you can easily run carbon. You will learn
more about running carbon in the running section shortly.

.. code-block:: bash

    # this assumes you have installed carbon!

    (cbn) $ cd ./template
    (cbn) $ carbon run --scenario main.yml --log-level debug \
    --assets-path ./assets

Carbon Jenkins Files
~~~~~~~~~~~~~~~~~~~~

Based on the standard scenario structure, lets review the directories and files
which are used to configure a Jenkins job for running the scenario using
carbon. The files below is just an example on how you could use carbon from
Jenkins to run multi product scenarios. There can be many different ways to run
from Jenkins. This is just one possible option.

.. code-block:: bash

    template/
    ├── Dockerfile
    ├── Jenkinsfile
    ├── job.yml
    └── misc
        ├── build_job
        │   ├── group_vars
        │   │   └── local
        │   ├── inventory
        │   ├── jenkins.ini
        │   └── site.yml
        └── jenkins-jobs.sh

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Name
        - Description
        - Required

    *   - Dockerfile
        - The dockerfile defines everything for carbon to run. The jenkins
          job uses the dockerfile to build a new container to be used as the
          agent. The agent is where everything will be run from within Jenkins.
        - No

    *   - Jenkinsfile
        - The jenkinsfile defines all tasks to be performed within the Jenkins
          job.
        - Yes

    *   - job.yml
        - The job.yml file is the jenkins job configuration formatted in yaml
          for Jenkins job builder. It is used for deploying the job.
        - Yes

    *   - misc
        - The misc directory contains scripts to help deploy your multi product
          scenario job to Jenkins. In this example there is a main shell script
          which calls an ansible playbook to install jenkins job builder and
          create the jenkins job from the job.yml file.
        - No **

Source
~~~~~~

The source for this template scenario structure can be found here: `template
<https://code.engineering.redhat.com/gerrit/gitweb?p=carbon-scenarios.git;
a=tree;f=template;h=e8701850ac0959b1278bdd88ed3d94b76f630bb0;hb=refs/heads
/master>`_.

.. note::

    ** It is highly recommended that you include both of these within your
    scenario.
