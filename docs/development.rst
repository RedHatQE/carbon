Development
-----------

Commit message guidelines
+++++++++++++++++++++++++

When submitting a patch to carbon project, carbon developers require you to
follow by a set of standard guidelines.

Carbon requires you to use the angular format for all commit messages created.
By using this format, it allows us to generate a changelog that is easy to
read about new changes that went into a specific release.

Lets see what a commit message skeleton should look like:

.. code-block:: bash

    <type>(<scope>): <subject>
    <BLANK LINE>
    <body>
    <BLANK LINE>
    <footer>

**Type** can consist of one of the following:

- feat: New feature being added.
- fix: A fix to resolve a bug found.
- docs: Documentation changes.
- style: Formatting, missing semi colons, etc.
- refactor: Refactor an entire code block.
- tests: Adding new tests.
- chore: Maintain various areas of the code.

**Scope** is optional. This may be useful if you want to include the name of
a module that your code change resides in. If you are working on multiple
modules, you would not want to put a scope (since the scope is too broad). If
you do add a scope, please do not include **carbon**. An example may be as
follows:

.. code-block:: none

    # core is the module name
    feat(core):

**Subject** is the message about the change. This should be a short
description (< 79 characters, this total includes <type>(<scope>)). A few
rules to follow by:

- Use imperative and present tense: "change" not "changed" nor "changes".
- Do not capitalize the first letter.
- Do not add a period "." at the end of the message.

.. code-block:: none

    feat(core): implement new feature x

**Body** is the detailed message about the change. Here you will want to give
more information for the change (comparing to the previous behavior - if
applicable).

.. code-block:: none

    feat(core): subject..

    X feature added..

**Footer** is where you can link an issue connecting to your code patch.

.. code-block:: none

    feat(core): subject..

    body..

    Closes ISSUE-1

Now that we know about how to create our commit message. Lets go through an
example. I just made an update to an existing class method within carbon's core
module to return a boolean value based on the process run. My commit message
would look something like this:

.. code-block:: none

    chore(core): return boolean value based on processing result

    This commit returns a boolean value based on result output.

If these standard guidelines are not followed, your code patch will be
rejected. A comment will be provided asking you to update your commit message
to follow these guidelines.
