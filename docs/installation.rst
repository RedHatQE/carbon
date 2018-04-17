Installation
------------

Prerequisites
+++++++++++++

Carbon framework requires the following system packages to be installed.

.. code-block:: bash
    :linenos:

    # Dnf package manager
    $ sudo dnf install -y gcc redhat-rpm-config libffi-devel openssl-devel python-devel

    # Yum package manager
    $ sudo yum install -y gcc redhat-rpm-config libffi-devel openssl-devel python-devel

Install
+++++++

Install the `virtualenv <https://virtualenv.pypa.io/en/stable/>`_ package on
your system.

.. code-block:: bash
    :linenos:

    $ sudo pip install virtualenv

Create a new python virtual environment for carbon. This will isolate carbon
framework from the system level python packages.

.. code-block:: bash
    :linenos:

    $ virtualenv ~/carbon

Once the environment is created, activate the carbon virtual environment.

.. code-block:: bash
    :linenos:

    $ source ~/carbon/bin/activate
    (carbon) $

Install carbon framework.

.. code-block:: bash
    :linenos:

    (carbon) $ pip install git+https://code.engineering.redhat.com/gerrit/p/carbon.git

Carbon framework is now successfully installed on your system! Please visit
the `quickstart guide <quickstart.html>`_ to get started!
