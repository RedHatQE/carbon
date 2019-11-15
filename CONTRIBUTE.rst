Welcome!

The carbon development team welcomes your contributions to the project. Please
use this document as a guide to working on proposed changes to carbon. We ask
that you read through this document to ensure you understand our development
model and best practices before submitting changes.

Branch Model
------------

Carbon has two branches
 - develop - all work is done here
 - master - stable tagged release that users can use

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

Let's create our new branch from develop

.. code-block:: bash

    (carbon) $ git checkout -b <new branch>

Finally install the carbon package itself using editable mode.

.. code-block:: bash

    (carbon) $ pip install -e carbon/.

You can verify carbon is installed by running the following commands.

.. code-block:: bash

    (carbon) $ carbon
    (carbon) $ carbon --version



How to run tests locally
------------------------

We have the following standards and guidelines

 - All tests must pass
 - Code coverage must be above 50%
 - Code meets PEP8 standards

Before any change is proposed to carbon we ask that you run the tests
to verify the above standards. If you forget to run the tests,
we have a Jenkins job that runs through these on any changes.
This allows us to make sure each patch meets the standards.

We also highly encourage developers to be looking to provide more tests
or enhance existing tests for fixes or new features they maybe submitting.
If there is a reason that the changes don't have any accompanying tests
we should be annotating the code changes with TODO comments with the
following information:

 - State that the code needs tests coverage
 - Quick statement of why it couldn't be added.

.. code-block:: bash

    #TODO: This needs test coverage. No mock fixture for the Carbon Orchestrator to test with.


How to run unit tests
~~~~~~~~~~~~~~~~~~~~~

You can run the unit tests and verify pep8 by the following command:

.. code-block:: bash

    (carbon) $ make test-functional

This make target is actually executing the following tox environments:

.. code-block:: bash

    (carbon) $ tox -e py27-unit
    (carbon) $ tox -e py3-unit

.. note::
    we use a generic tox python 3 environment to be flexible towards developer
    environments that might be using different versions of python 3. Note the
    minimum supported version of python is python 3.6.

How to run localhost scenario tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The local scenario test verify your changes don't impact core functionality in the framework
during provision, orchestrate, execute, or report. It runs a scenario descriptor file using
localhost, a carbon.cfg, some dummy ansible playbooks/scripts, and dummy test artifacts.
It does NOT run integration to real external system like OpenStack or Polarion.

.. code-block:: bash

    (carbon) $ make test-scenario

This make target is actually executing the following tox environments:

.. code-block:: bash

    (carbon) $ tox -e py27-scenario
    (carbon) $ tox -e py3-scenario

.. note::
    If there is a need to test an integration with a real external system
    like OpenStack or Polarion, you could use this scenario as a basis of a
    more thorough integration test of your changes. It would require modifying
    the scenario descriptor and carbon.cfg file with the necessary parameters and
    information. But it is not recommended to check in this modified scenario
    as part of your patch set.

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
code changes, ran through the unit tests and pep8 validation. Before you submit
your changes you should check a few things

If the develop branch has changed since you last pulled it down it
is important that you get the latest changes in your branch.
You can do that in two ways:

Rebase using the local develop branch

.. code-block:: bash

    (carbon) $ git checkout develop
    (carbon) $ git pull origin develop
    (carbon) $ git checkout <branch>
    (carbon) $ git rebase develop

Rebase using the remote develop branch

.. code-block:: bash

    (carbon) $ git pull --rebase origin/develop

Finally, if you have mutiple commits its best to squash them into a single commit.
The interactive rebase menu will appear and guide you with what you need to do.

.. code-block:: bash

    (carbon) $ git rebase -i HEAD~<the number of commits to latest develop commit>

Once you've completed the above you're good to go! All that is left is
to submit your change. You can do that by the following command:

.. code-block:: bash

    (carbon) $ git review

Feature Toggles
---------------

Although this doesn't happen very often this does warrant a mention. If a feature
is too big to, where it would better suited to merge incrementally in a
'trunk' style of development. Then we should consider utilizing
feature toggles so as the develop branch can stay releasable at all times.

The carbon.cfg is capable of reading feature toggles and utilizing them.
It's a very rudimentary implementation of a feature toggle mechanism but it has worked in
the past on short notice. Below is the process when working at adding functionality to
one of the main resources (Host, Actions, Executions, Reports).


To the resource we are working on define the following feature toggle method

.. code-block:: python

    def __set_feature_toggles_(self):

    self._feature_toggles = None

    for item in self.config['TOGGLES']:
        if item['name'] == '<name of resource the feature belongs to>':
            self._feature_toggles = item


Then in the __init__ function of the resource you are working on add the
following lines of code. This will help to keep carbon running original code
path unless explicitly told to use the new feature

.. code-block:: python

    if self._feature_toggles is not None and self._feature_toggles['<name of new feature toggle>'] == 'True':
        <new feature path>
    else:
        <original code path>


Now in your carbon config file when you want to use the new code path
for testing or continued development you can do the following:

.. code-block:: bash

    [orchestrator:ansible]
    log_remove=False
    verbosity=v

    [feature_toggle:<resource name from step 1>]
    <feature toggle name specified in step 2>=True
