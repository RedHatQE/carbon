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
Group Packages can be specified by preceding Group name with '@'.
Environmental Group Packages may be specified by preceding Environmental Group name with '@^'.
Group Names should be enclosed in quotes

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

        # install Group Package
        - name: install_rpm_packages
          orchestrator: ansible
          hosts: <hosts>
          vars:
            packages:
              - "@Development Tools"

        # install Environmental Group Package
        - name: install_rpm_packages
          orchestrator: ansible
          hosts: <hosts>
          vars:
            packages:
              - "@^gnome-desktop-environment"


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

install_nvr.yml
------------------------

Description
+++++++++++

Given an name-value-release value of a package on a brew system, this playbook
will install the correct arch version of the package on your specified host.

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
        # install a package from a brew system
        - name: install_nvr
          orchestrator: ansible
          hosts: <hosts>
          vars:
            brew_root: <brew_url>/brewroot
            nvr: <package>
            dest: /home/test/aut

rhn_subscribe.yml
------------------------

Description
+++++++++++

Subscribe to RedHat Network using subscription-manager.
May auto subscribe or specify pool ids.

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
        # auto subscribe to RHN using subscription-manager
        - name: rhn_subscribe
          orchestrator: ansible
          hosts: <hosts>
          vars:
            rhn_hostname: subscription.rhsm.redhat.com
            rhn_user: <subscription_manager user>
            rhn_password: <subscription_manager password>
            auto: True

        # auto subscribe to RHN using subscription-manager
        - name: rhn_subscribe
          orchestrator: ansible
          hosts: <hosts>
          vars:
            rhn_hostname: subscription.rhsm.redhat.com
            rhn_user: <subscription_manager user>
            rhn_password: <subscription_manager password>
            pool_ids:
              - 0123456789abcdef0123456789abcdef
              - 1123456789abcdef0123456789abcdef

rhn_unsubscribe.yml
------------------------

Description
+++++++++++

Unsubscribe to RedHat Network using subscription-manager.

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
        # Unsubscribe from RHN using subscription-manager
        - name: rhn_unsubscribe
          orchestrator: ansible
          hosts: <hosts>

rhsm_add_repos.yml
------------------------

Description
+++++++++++

Add/Enable channels through subscription manager

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
        # Add Repo channels through subscription-manager
        - name: rhsm_add_repos
          orchestrator: ansible
          hosts: <hosts>
          vars:
            channel_list:
              - rhel-7-server-rpms
              - rhel-7-server-supplementary-rpms
              - rhel-7-server-rhv-4.1-rpms
              - jb-eap-7-for-rhel-7-server-rpms
              - rhel-7-server-rhv-4-tools-rpms

rhsm_remove_repos.yml
------------------------

Description
+++++++++++

Remove/Disable Repo channels through subscription manager

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
        # Remove Repo channels through subscription-manager ex. All channels
        - name: rhsm_remove_repos
          orchestrator: ansible
          hosts: <hosts>
          vars:
            channel_list: "*"

set_selinux.yml
------------------------

Description
+++++++++++

Set mode for selinux
Modes are diabled, permissive or enabled

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
        # Set mode for selinux
        - name: set_selinux
          orchestrator: ansible
          hosts: <hosts>
          vars:
            mode: disabled

system_check.yml
------------------------

Description
+++++++++++

Check system reachable through ping.
Will check for five minutes until successful.
Delay of 20 seconds between attempts.
If unable to reach after 5 minutes fails.

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
        # Check system reachable
        - name: system_check
          orchestrator: ansible
          hosts: <hosts>

update_rpm_packages.yml
------------------------

Description
+++++++++++

Update packages or system through yum

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
        # System update of rpm packages
        - name: update_rpm_packages
          orchestrator: ansible
          hosts: <hosts>
          vars:
            packages: "*"

    orchestrate:
        # Update specific rpm packages
        - name: update_rpm_packages
          orchestrator: ansible
          hosts: <hosts>
          vars:
            packages:
              - ansible
              - python2-devel
              - python3-devel

yum_disable_repos.yml
------------------------

Description
+++++++++++

Disable rpm Repos through yum

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
        # Disable all repos on system
        - name: yum_disable_repos
          orchestrator: ansible
          hosts: <hosts>
          vars:
            repo_list: "*"

    orchestrate:
        # Disable specific rpm repos
        - name: yum_disable_repos
          orchestrator: ansible
          hosts: <hosts>
          vars:
            repo_list:
              - epel
              - qa-tools

enable_firewall.yml
------------------------

Description
+++++++++++

Enable and configure Firewall

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
        # Enable firewall
        - name: enable_firewall
          orchestrator: ansible
          hosts: <hosts>

    orchestrate:
        # Enable firewall and set configuration
        - name: enable_firewall
          orchestrator: ansible
          hosts: <hosts>
          vars:
            fw_cmds: <list of firewall rules>


disable_firewall.yml
------------------------

Description
+++++++++++

Disable Firewall

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
        # Disable firewall
        - name: disable_firewall
          orchestrator: ansible
          hosts: <hosts>

network_time_service.yml
------------------------

Description
+++++++++++

Setup Network Time service through ntp or chrony

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
        # Setup/run Network Time Service
        - name: network_time_service
          orchestrator: ansible
          hosts: <hosts>

    orchestrate:
        # Setup/run Network Time Service specifying ntp time hosts
        - name: network_time_service
          orchestrator: ansible
          hosts: <hosts>
          vars:
            ntp_list: < list of time server hosts >

add_yum_repositories.yml
------------------------

Description
+++++++++++

Add yum repositories to remote systems

Examples
++++++++

Carbon scenario descriptor examples

.. code-block::

    ---
    orchestrate:
      # add a yum repository
      - name: add_yum_repositories
        orchestrator: ansible
        hosts: <hosts>
        vars:
          repositories:
            - name: repo01
              description: repo01
              baseurl: https://hostname
              gpgcheck: no
              enabled: yes

      # add multiple yum repositories
      - name: add_yum_repositories
        orchestrator: ansible
        hosts: <hosts>
        vars:
          repositories:
            - name: repo01
              description: repo01
              baseurl: https://hostname
              gpgcheck: no
              enabled: yes
            - name: repo02
              description: repo02
              baseurl: https://hostname
              gpgcheck: no
              enabled: yes

install_restraint.yml
---------------------

Description
+++++++++++

Install restraint framework on test clients.

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
      # install restraint on clients
      - name: install_restraint
        orchestrator: ansible
        hosts: <hosts>

create_ssh_keypair.yml
----------------------

Description
+++++++++++

Create SSH keys on test clients for testing purposes.

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
      # create ssh key on clients
      - name: create_ssh_keypair
        orchestrator: ansible
        hosts: <hosts>
        vars:
          user: centos

inject_pub_key
--------------

Description
+++++++++++

Inject SSH public key between machines for ssh communication.

Examples
++++++++

Carbon scenario descriptor examples.

.. code-block::

    ---
    orchestrate:
      # inject public ssh key between machines for ssh communication
      - name: inject_pub_key
        orchestrator: ansible
        hosts: <hosts>
        vars:
          user: centos
          machine: test_client_01