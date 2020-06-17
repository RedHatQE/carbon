Install Carbon
==============

Requirements
++++++++++++

Your system requires the following packages to install carbon:

.. code-block:: bash

    # To install git using dnf package manager
    $ sudo dnf install -y git

    # To install git using yum package manager
    $ sudo yum install -y git

    # Install python pip: https://pip.pypa.io/en/stable/installing
    $ sudo curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    $ sudo python get-pip.py

    # Recommend installation of virtualenv using pip
    $ sudo pip install virtualenv

.. note::

   To install Carbon version 1.1.0 and above, pip version 18.1 or higher is required

Install
+++++++

Install carbon from source:

.. code-block:: bash

    # for ansible modules requiring selinux, you will need to enable system site packages
    $ virtualenv --system-site-packages carbon
    $ source carbon/bin/activate
    (carbon) $ pip install git+https://code.engineering.redhat.com/gerrit/p/carbon.git

Post Install
++++++++++++

If you require carbon to interface with beaker using the bkr-client provisioner,
you will need to enable the beaker client repository/install the beaker-client package.
Carbon uses the beaker client package to provision physical machines in beaker.

.. code-block:: bash

    # https://beaker-project.org/download.html
    $ sudo curl -o /etc/yum.repos.d/bkr-client.repo \
    https://beaker-project.org/yum/beaker-client-<DISTRO>.repo

    # To install beaker-client using dnf package manager
    $ sudo dnf install -y beaker-client

    # To install beaker-client using yum package manager
    $ sudo yum install -y beaker-client

.. note::

    Beaker-client could be installed from PyPI rather than RPM. Installing from
    pip fails in Python 3. Beaker client is not compatible with Python 3
    currently. Once compatibile it can be installed with carbon. Carbon is
    Python 2.7 & Python 3.6 compatible.

.. _cbn_importer_plugin:

Carbon Importer Plugin Requirements
+++++++++++++++++++++++++++++++++++

Installing Carbon's Importer Plugins
------------------------------------

Carbon is currently supporting two importer plugins

 * 1
   carbon_polarion_plugin
   `repo link <https://gitlab.cee.redhat.com/ccit/carbon_polarion_plugin>`__
 * 2
   carbon_rppreproc_plugin
   `repo link <https://gitlab.cee.redhat.com/ccit/carbon_rppreproc_plugin>`__

Install the importer plugin from source
---------------------------------------

For Report Portal Plugin
~~~~~~~~~~~~~~~~~~~~~~~~

.. NOTE::
    This plugin is supported only on Python 3 environments.

.. code-block:: bash

    # for ansible modules requiring selinux, you will need to enable system site packages
    $ virtualenv --system-site-packages reportportal
    $ source reportportal/bin/activate
    (reportportal) $ pip install carbon_rppreproc_plugin@git+https://gitlab.cee.redhat.com/ccit/carbon_rppreproc_plugin.git@master

For Polarion Plugin
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # for ansible modules requiring selinux, you will need to enable system site packages
    $ virtualenv --system-site-packages polarion
    $ source polarion/bin/activate
    (polarion) $ pip install carbon_polarion_plugin@git+https://gitlab.cee.redhat.com/ccit/carbon_polarion_plugin.git@master


Linchpin Requirements
~~~~~~~~~~~~~~~~~~~~~

The Linchpin plugin will be available as an extra. To install Linchpin certain requirements need to be
met so that it can be installed correctly. Please refer to the
`pre-install section <https://gitlab.cee.redhat.com/ccit/carbon/plugins/carbon_linchpin_plugin/blob/develop/docs/user.md#installation>`_
of the plugin documentation on how to install them.

Once installed, you can install Linchpin from Carbon

.. code-block:: bash

    $ pip install carbon[linchpin-wrapper]

Once Linchpin is installed, you will get support for all providers. Although there are
some providers that require a few more dependencies to be installed. Refer to the
`post-install section <https://gitlab.cee.redhat.com/ccit/carbon/plugins/carbon_linchpin_plugin/blob/develop/docs/user.md#post-install>`__
of the plugin document for methods on how to install those dependencies.

.. _cbn_plugin_matrix:

Carbon Matrix for Plugins
+++++++++++++++++++++++++

The table below lists out the released Carbon version and supported carbon plugin versions. This matrix will track
n and n-2 carbon releases

.. list-table:: Carbon plugin matrix for n and n-2 releases
    :widths: auto
    :header-rows: 1

    *   - Carbon Release
        - Rppreproc Plugin
        - Polarion Plugin
        - Linchpin Plugin
        - Openstack Client Plugin
        - Polar
        - Rp_preproc
        - Ansible

    *   - **1.8.0**
        - 1.1.1
        - 1.1.0
        - 1.0.1
        - 0.2.0
        - 1.2.1
        - 0.1.3
        - >=2.5.0

    *   - **1.7.0**
        - >=1.1.0
        - 1.1.0
        - 1.0.0
        - --
        - 1.2.1
        - 0.1.3
        - >=2.5.0

    *   - **1.6.0**
        - 1.0.1
        - 1.0.1
        - 1.0.0
        - --
        - 1.2.1
        - 0.1.3
        - >=2.5.0, <=2.9.0
