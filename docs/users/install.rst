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

Linchpin Requirements
~~~~~~~~~~~~~~~~~~~~~

As of 1.2.0, carbon will install Linchpin and Linchpin's Beaker & Libvirt python dependencies but Linchpin also needs certain requirements that need to be met
so that this can be installed correctly.


     * Please refer to the `minimum requirements <https://linchpin.readthedocs.io/en/latest/installation.html#minimal-software-requirements>`_
       section in the Linchpin Installation guide.

     * Please refer to the `additional dependencies <https://linchpin.readthedocs.io/en/latest/libvirt.html#additional-dependencies>`_ section
       of the Libvirt provider page for the necessary requirements to support Libvirt.

.. note::

   Linchpin python 3 support is still experimental and not fully compatible so it will not be installed in this environment.
   To take advantage of Linchpin you must be using python 2.7 environment.  

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

Report Portal Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~

Carbon installs CCIT Report Portal client as an extra requirement. To know more
about Report Portal Client, please refer
`here <https://docs.engineering.redhat.com/pages/viewpage.action?pageId=81876674>`_

To install users can do the following

.. code-block:: python

   pip install carbon[rp-preproc]


.. NOTE::
    The client is supported only on Python 3 environments.