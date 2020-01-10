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


Carbon Importer Plugin Requirements
+++++++++++++++++++++++++++++++++++

Installing Carbon's Importer Plugins
------------------------------------

Carbon is currently supporting two importer plugins

 * 1
   carbon_polarion_plugin
   `repo link <https://gitlab.cee.redhat.com/ccit/carbon_polarion_plugin>`_
 * 2
   carbon_rppreproc_plugin
   `repo link <https://gitlab.cee.redhat.com/ccit/carbon_rppreproc_plugin>`_

These plugins have Carbon installation as a part of the setup. So if user wants to just use any of the above plugin with
carbon, we can install only the plugin, and carbon will be installed with it as well.
If the plugin is installed in an environment where carbon is already present , plugin will skip carbon installation

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

As of 1.4.0, Linchpin will be an extra. To install Linchpin certain requirements need to be
met so that it can be installed correctly. Please refer to the
`minimum requirements <https://linchpin.readthedocs.io/en/latest/installation.html#minimal-software-requirements>`_
section in the Linchpin Installation guide.

Once installed, you can install Linchpin from Carbon

.. code-block:: bash

    $ pip install carbon[linchpin-wrapper]

Once Linchpin is installed, you will get OpenStack and AWS support through Carbon for both python 2 and 3.
If you want Beaker or Libvirt, there are some additional package dependencies that are required.

 * Please refer to the
   `additional dependencies <https://linchpin.readthedocs.io/en/latest/beaker.html#additional-dependencies>`_
   section of the Beaker provider page for the necessary requirements to support Beaker.

 * Please refer to the
   `additional dependencies <https://linchpin.readthedocs.io/en/latest/libvirt.html#additional-dependencies>`_
   section of the Libvirt provider page for the necessary requirements to support Libvirt.

Luckily, Linchpin has automated this process for users using their **setup** command. This command will
install the required dependencies for each of the providers

.. code-block:: bash

    $ linchpin setup beaker
    $ linchpin setup libvirt [--ask-sudo-pass]

Please refer to the Linchpin
`installation guide <https://linchpin.readthedocs.io/en/latest/installation.html#linchpin-setup-automatic-dependency-
installation>`_ for more information on the setup command.

Once the dependencies are installed you will get Beaker support through Carbon for python 2 and
Libvirt support through Carbon for python 2 and 3.

.. note::

   Linchpin python 3 support is still not available with Beaker. They are investigating support
   for Beaker 27 client to enable python 3 support.