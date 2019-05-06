Report
======

Overview
--------

Carbon's report section declares which test artifacts collected during execution 
are to be imported into a Report & Analysis system. The input for artifact import
will depend on the destination system. The current support for Reporting systems are:
:ref:`Polarion<polarion_importing>`

First, let's go over the basic structure that defines a Report resource.

.. code-block:: yaml

    ---
    report:
      - name: <name>
        description: <description>
        executes: <execute>
        importer: <importer>
        provider: <dict_key_values>

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - name
        - The name of the test artifact to import.
        - String
        - True

    *   - description
        - A description of the artifact being imported
        - String
        - False

    *   - executes
        - The name of the execute block that collected
          the artifact.
        - List
        - True

    *   - importer
        - The name of the importer to perform the import process.
        - String
        - False

    *   - provider
        - Dictionary of the specific provider key/values.
        - Dict
        - True

If you are familiar with the structure of Provision then the same
concept of Provider has been utilized in the Report. We will dive 
into the Polarion Provider parameters below.

.. _polarion_importing:

Importing artifacts into Polarion
---------------------------------

Credentials
+++++++++++

To authenticate with Polarion, you will need to have your Polarion credentials
in your carbon.cfg file, see `Polarion Credentials
<credentials.html#polarion-credentials>`_ for more details.

Polarion Artifact
++++++++++++++++++

The following shows all the possible keys for defining the artifact import
for the Polarion xUnit Importer:

.. code-block:: yaml

    ---
    report:
      - name: <name>
        description: <description>
        executes: <execute name>
        importer: <importer>
        provider:
          credential: polarion-creds
          name: polarion
          project_id: <project_id>
          testsuite_properties: <ts_properties>
          testcase_properties: <tc_properties>
          testcase_csv_file: <path_to_csv>

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - name
        - The name of the provider (polarion).
        - String
        - True

    *   - credential
        - The name of the credentials to use to import the artifact
          into polarion. This is the one defined in the credentials 
          section of the carbon config file.
        - String
        - True

    *   - project_id
        - The Polarion project id
        - String
        - False (True for xUnit conversion)

    *   - testsuite_properties
        - These are the specific Polarion test suite
          properties to apply to the xUnit file before 
          importing. Any polarion-custom property can be used as well.
          format: <polarion-ts-property>: <value> 
        - Dictionary
        - False

    *   - testcase_properties
        - These are the specific testcases in the xUnit file and 
          associated Polarion test cases properties to apply to 
          the xUnit file before importing. Any polarion-custom 
          property can be used as well. format:
          <test_classname>.<name_attribute>: 
          <polarion-tc-property>: <value>
        - Dictionary
        - False

    *   - testcase_csv_file
        - An export csv file from Polarion that contains testcase
          work item fields - id, title, and testcaseid. Using this
          will allow carbon to dynamically assign the testcases
          the proper polarion-testcase-id based on the specified lookup
          method specified in testsuite_properties
        - String
        - False

.. attention::
   It's important to note when project_id, testsuite_properties, testcase_properties
   and/or testcase_csv_file are specified the importer will take those parameters and
   attempt to do the xUnit conversion. When supplying these provider
   parameters a minimum required parameter for xUnit conversion is project_id.

   If project_id, testsuite_properties, testcase_properties, and testcase_csv_file are
   not specified carbon will not perform the xUnit conversion. It will proceed with
   importing the artifact and monitoring for import status.

xUnit Test Case Properties
++++++++++++++++++++++++++
For the xUnit conversion process there are two options for tagging test cases with the
appropriate id, **testcase_properties** or **testcase_csv_file**. Carbon has opted to follow
the general guidelines set forth by Polarion.

testcase_csv_file
+++++++++++++++++
For a dynamic approach a user can export a csv file from Polarion containing the *id*, *title*,
and *testcaseid* fields. This file is used in conjunction with a lookup-method. The *testcaseid*
field is enabled by default in Polarion but is not available in the Form UI until it has been
explicitly enabled by a project administrator. Once enabled the field should contain the name
of the xUnit test case in the format of **<testclassname>.<name attribute>**.  For more
information about the *testcaseid* field refer to the following Polarion
documentation `<https://mojo.redhat.com/docs/DOC-1073077#jive_content_id_Polarion_Configuration>`_

If no lookup method is specified in the testsuite_properties the Polarion xUnit Importer will
default to looking for test cases using its id. Carbon will parse the *testcaseid* from the csv file
and see if it is in the xUnit file. When found it will add the **polarion-testcase-id** property value
to the *id*. The same applies if the lookup method was explicitly set to *id*.

If the lookup method is set to *custom*. Carbon will parse the *testcaseid* from the csv file and see if
it is in the xUnitfile. When found it will add the **polarion-testcase-id** property value to the
*testcaseid*.

If the lookup method is set to *name*. There is no need to specify this parameter since the Polarion
xUnit Importer will search for the test case by the *title* and a **polarion-testcase-id** is not required.
In order for Polarion to successfully find the test case the *title* has to be in the
**<testclassname>.<name attribute>** format.

testcase_properties
+++++++++++++++++++
This a static approach to defining what tags are to be applied to the xUnit test case. This
is the recommended approach when a test case needs to have iterations added before the import.
This is also the recommended method if Polarion projects have not enabled and are not using the
testcaseid field for automated test cases being imported.

 
Carbon Polarion Configuration
+++++++++++++++++++++++++++++

In the carbon configuration file, you can set some options related to Polarion.
These values should be set in the **[importer:polarion]** section of the
config file.  The following are the settings.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Default

    *   - save_file
        - configuration option to save a copy of the xUnit file
          before performing the xUnit conversion.
        - By default this is set to true to make a copy.

    *   - wait_timeout
        - configuration option to set how long carbon should 
          wait for the import process to complete.
        - By default, carbon will set the timeout to 15 minutes.
          This value can be overwritten but must be specified in
          seconds, i.e. 15 minutes = 900 seconds.
   
    *   - poll_interval
        - configuration option to set how often carbon should check 
          with the Polarion xUnit queue for import process status. 
        - By default, carbon will poll the xUnit queue every 1 minute.
          This value can be overwritten but must be specified in seconds
          i.e. 1 minute = 60 seconds.


Examples
--------

Lets dive into a couple different examples.

Example 1
+++++++++

You have an xUnit artifact that has already gone through conversion as part of 
the test process and needs to be imported into Polarion.

.. literalinclude:: ../../../examples/docs-usage/report.yml
    :lines: 1-8

Example 2
+++++++++

You have an xUnit artifact that needs just some testsuite properties applied,
where the lookup method is set to name. Then the artifact is imported afterwards.

.. literalinclude:: ../../../examples/docs-usage/report.yml
    :lines: 10-23

Example 3
+++++++++

You have an xUnit artifact that needs a full set of properties applied and  
imported afterwards. No lookup method is supplied because the id for the
test case has been explicitly defined and an iteration.

.. literalinclude:: ../../../examples/docs-usage/report.yml
    :lines: 25-41

Example 4
+++++++++

You have an xUnit artifact that was named using Carbon's data pass-through in 
the execute phase that needs to have some testsuite properties applied to it and
imported afterwards.

.. literalinclude:: ../../../examples/docs-usage/report.yml
    :lines: 43-54

Example 5
+++++++++

You have a set of xUnit files that have already gone through conversion 
during the test process and just need to be bulk imported.

.. literalinclude:: ../../../examples/docs-usage/report.yml
    :lines: 56-63

Example 6
+++++++++

You have a set of xUnit files that have the same name
that have already gone through conversion during the test process 
but you only need one from a specific host in carbon's artifact directory.

.. literalinclude:: ../../../examples/docs-usage/report.yml
    :lines: 65-72

Example 7
+++++++++

You have an xUnit file that needs to be properly tagged with testsuite
properties and the testcases should dynamically tagged with their polarion
id using the contents of the csv file. Then imported afterwards.

.. literalinclude:: ../../../examples/docs-usage/report.yml
   :lines: 74-87