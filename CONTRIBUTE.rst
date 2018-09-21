Welcome!

The carbon development team welcomes your contributions to the project. Please
use this document as a guide to working on proposed changes to carbon. We ask
that you read through this document to ensure you understand our development
model and best practices before submitting changes.

Branch Model
------------

The master branch is a protected branch. We do not allow commits directly to
it. Master branch contains the latest stable release. The develop branch is
where all active development takes place for the next upcoming release. All
contributions are made to the develop branch.

Most contributors create a new branch based off of develop to create their
changes.

How to setup your dev environment
---------------------------------

Lets first clone the source code. We will clone from the develop branch.

.. code-block:: bash

    $ git clone https://code.engineering.redhat.com/gerrit/p/carbon.git -b develop

Next lets create a Python virtual environment for carbon. This assumes you
have virtualenv package installed.

.. code-block:: bash

    $ mkdir ~/.virtualenvs
    $ virtualenv ~/.virtualenvs/carbon
    $ source ~/.virtualenvs/carbon/bin/activate

Now that we have our virtual environment created. Lets go ahead and install
the Python packages used for development.

.. code-block:: bash

    (carbon) $ pip install -r carbon/test-requirements.txt

Finally install the carbon package itself using editable mode.

.. code-block:: bash

    (carbon) $ pip install -e carbon/.

You can verify carbon is installed by running the following commands.

.. code-block:: bash

    (carbon) $ carbon
    (carbon) $ carbon --version

How to run unit tests
---------------------

Before any change is proposed to carbon. We ask that you run the unit tests
and verify your change meets the pep8 standards set. If you forget to run
these, we have a job that runs through these on any changes. This allows us to
make sure each patch meets the standards.

You can run the unit tests and verify pep8 by the following command:

.. code-block:: bash

    (carbon) $ make test-functional

This make target is actually executing the following tox environments:

.. code-block:: bash

    (carbon) $ tox -e py27
    (carbon) $ tox -e py36

How to build documentation
--------------------------

If you are working on documentation changes, you probably will want to build
the documentation locally. This way you can verify your change looks good. You
can build the docs locally by running the following command:

.. code-block:: bash

    (carbon) $ make docs

This make target is actually executing the following tox environments:

.. code-block:: bash

    (carbon) $ tox -e docs

How to propose a new change
---------------------------

The carbon project currently resides in Red Hat's internal gerrit server. We
use this to handle our code reviews. When installing the test requirements, it
will install the **git-review** package. This package is needed for proposing
a new review.

At the root of the project is a **.gitreview** file. You can see the file
content below. It just defines the details where to push your review too.

.. literalinclude:: ../../.gitreview

At this point you have your local development environment setup. You made some
code changes, ran through the unit tests and pep8 validation. Your good to go!
All that is left is to submit your change. You can do that by the following
command:

.. code-block:: bash

    (carbon) $ git review
