Contributing
============

This page provides you with helpful information regarding carbon development.

Environment Setup
-----------------

Carbon is written 100% in Python. We highly recommend that you use virtual
environments so you can isolate system site packages from carbons required
packages. Please follow the steps below to get carbon up and running in your
local environment:

1. Create a virtual environment

.. code-block:: bash
    :linenos:

    $ virtualenv carbon
    $ source carbon/bin/activate

2. Install development packages. These packages are needed for running tests,
building documentation, etc.

.. code-block:: bash
    :linenos:

    (carbon) $ pip install -r carbon/test-requirements.txt

3. Install carbon using editable mode. This allows your local changes to take
effect right away. Setuptools calls this "develop mode".

.. code-block:: bash
    :linenos:

    (carbon) $ pip install --editable .

4. You now have carbon installed. You can run carbon from command line or a
Python module.

.. code-block:: bash
    :linenos:

    (carbon) $ carbon
    (carbon) $ carbon --version

How to run Carbon
-----------------

It is assumed that you have your environment setup and carbon installed. To
run a scenario descriptor file, you can issue the following command below.

.. code-block:: bash
    :linenos:

    (carbon) $ carbon -v run -s /path/to/scenario/descriptor

The command above will run through all tasks. If you wish to run a certain
task you can declare that in your carbon command. Use the --help option to
view the available tasks.

.. code-block:: bash
    :linenos:

    (carbon) $ carbon -v run -s /path/to/scenario/descriptor --task validate

How to run Carbon Functional Tests
----------------------------------

Carbon provides a Makefile which has targets for easily executing tests. To
run the functional tests, issue the following command:

.. code-block:: bash
    :linenos:

    (carbon) $ make
    # -- or --
    (carbon) $ make test-functional

Underneath the make target, it is actually executing a tox command. You could
run the following if you only want to test a certain version of Python:

.. code-block:: bash
    :linenos:

    (carbon) $ tox -e py27-functional
    # -- or --
    (carbon) $ tox -e py36-functional

How to run Carbon Integration Tests
-----------------------------------

Carbon provides a Makefile which has targets for easily executing tests. To
run the integration tests, issue the following command:

.. code-block:: bash
    :linenos:

    (carbon) $ make test-integration

Underneath the make target, it is actually executing a tox command. You could
run the following if you only want to test a certain version of Python:

.. code-block:: bash
    :linenos:

    (carbon) $ tox -e py27-integration
    # -- or --
    (carbon) $ tox -e py36-integration

How to build Carbon Devel Container Image
-----------------------------------------

Sometimes it may be useful to run carbon within a container. Carbon provides
a dockerfile which defines all packages required for running carbon. The
Makefile contains a target for building the image. To build a new image
based on the source code cloned locally with devel tag. Run the following
command:

.. code-block:: bash
    :linenos:

    (carbon) $ make build-image-devel

How to build Carbon Latest Container Image
------------------------------------------

Sometimes it may be useful to run carbon within a container. Carbon provides
a dockerfile which defines all packages required for running carbon. The
Makefile contains a target for building the image. To build a new image
based on the source code cloned locally with latest tag. Run the following
command:

.. code-block:: bash
    :linenos:

    (carbon) $ make build-image-latest

How to deploy Carbon Devel Container Image
------------------------------------------

To deploy your newly created carbon container image, you can run the
following command to deploy to a remote registry.

.. code-block:: bash
    :linenos:

    (carbon) $ make deploy-image-devel

.. note::
    You will be asked to provide username/password for authenticating to the
    registry.

How to deploy Carbon Latest Container Image
-------------------------------------------

To deploy your newly created carbon container image, you can run the
following command to deploy to a remote registry.

.. code-block:: bash
    :linenos:

    (carbon) $ make deploy-image-latest

.. note::
    You will be asked to provide username/password for authenticating to the
    registry.

For any other questions regarding development of carbon, please feel free to
reach out to any maintainers of the project.