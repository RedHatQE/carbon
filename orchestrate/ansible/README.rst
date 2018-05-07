Ansible Playbooks
=================

Within this directory you will find various Ansible playbooks available to you
when using carbon framework. The purpose of these playbooks is to provide an
easy starting point to build multi product scenarios. It eliminates the need
for engineers to recreate an existing playbook for a new scenario that may
already exists.

Please note these playbooks are high level and generic. If you are looking for
specific low layer playbooks for configuring. You may want to look into
creating custom playbooks for your scenario that carbon will load/run.

Playbooks
=========

install_pip_packages.yml
------------------------

Description
+++++++++++

Install Python packages on remote system(s).

Variables
+++++++++

latest_packages
    List of packages to be installed. (latest version)

version_packages
    List of dictionaries to install packages. (specific versions)

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
        # install python packages (latest version)
        - name: install_pip_packages
          orchestrator: ansible
          hosts: <hosts>
          vars:
            latest_packages:
              - ansible
              - flask

        # install python packages (specific version)
        - name: install_pip_packages
          orchestrator: ansible
          hosts: <hosts>
          vars:
            version_packages:
              - { name: ansible, version: 2.5.2 }
              - { name: flask, version: 1.0.1 }

remove_pip_packages.yml
------------------------

Description
+++++++++++

Remove Python packages on remote system(s).

Variables
+++++++++

packages
    List of packages to be removed.

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
        # remove python packages
        - name: remove_pip_packages
          orchestrator: ansible
          hosts: <hosts>
          vars:
            packages:
              - ansible
              - flask

install_rpm_packages.yml
------------------------

Description
+++++++++++

Install RPM based packages on remote system(s).

Variables
+++++++++

packages
    List of packages to be installed.

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
        # install packages
        - name: install_rpm_packages
          orchestrator: ansible
          hosts: <hosts>
          vars:
            packages:
              - ansible
              - python2-devel
              - python3-devel

remove_rpm_packages.yml
------------------------

Description
+++++++++++

Remove RPM based packages on remote system(s).

Variables
+++++++++

packages
    List of packages to be removed.

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
        # remove packages
        - name: remove_rpm_packages
          orchestrator: ansible
          hosts: <hosts>
          vars:
            packages:
              - ansible
              - python2-devel
              - python3-devel

install_pip.yml
------------------------

Description
+++++++++++

Install Python pip package on remote system(s).

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
        # install pip package
        - name: install_pip
          orchestrator: ansible
          hosts: <hosts>