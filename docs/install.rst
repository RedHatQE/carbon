Install
=======

To install carbon, make sure your system has the following packages installed:

.. code-block:: bash

    # dnf package manager
    $ sudo dnf install -y python-pip git

    # yum package manager
    $ sudo yum install -y python-pip git

Install carbon from source:

.. code-block:: bash

    $ pip install --user git+https://code.engineering.redhat.com/gerrit/p/carbon.git

It is recommended to install carbon within a virtual environment. This way
it isolates carbon packages from the system site packages.

.. code-block:: bash

    $ virtualenv cbn
    $ source cbn/bin/activate
    (cbn) $ pip install git+https://code.engineering.redhat.com/gerrit/p/carbon.git
