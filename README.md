# Carbon Framework

## What is Carbon Framework?

A framework that creates product interoperability scenarios to support
interoperability tests.

## Is it ready?

No. This is an experiment, a prototype.

## Does it look familiar?

Yes, this code started shamelessly by copying few good stuff from Flask
framework - configuration and core object structure. Also, there's a bunch
of code that will be transfered from the old pit framework. The biggest
change is in the architecture of the framework which is now task oriented.

## How is it supposed to work?

Each scenario is a definition written in YAML. The framework loads the
yaml file and build a pipeline of sub-pipelines. Each sub-pipeline will
contain loads of tasks related to the resources. A resource can be a 
scenario, a host or a package. Each resource will contain tasks that the
framework will collect, load into its respective sub-pipeline and run in
the order described in the YAML file. For instance, if a Package has a 
task of type InstallTask, the framework will collect it and add to the
Install pipeline.

Basically, when you run the scenario the framework will:

1. Provision the machines
2. Configure all machines accordingly
3. Install all packages for each host that are related to the products
that will be tested.
4. Run your tests (if you build a TestTask and add into the scenario)
5. Report the results

## Development

Ideally you would create a virtual environment. Download the source
code and follow the commands below:

```
$ pip install -r requirements.txt
```

This is going to install all necessary packages that Carbon depends on.

Next you can install Carbon itself from the source directory so you can
run tests before commit any code:

```
$ pip install --editable .
```

This way any change you do in the source code you don't need reinstall
it and your changes will be reflected right away.

Before run the tests you have to install some tools. Follow the
command below:

```
$ pip install -r test-requirements.txt
```

Now you can run the tests via Makefile:

```
$ make test
```

Before you commit the code, run a full check to make sure the code is
tested and lint'ed':

```
$ make
```

You can find the reports on the tests directory:

 * `tests/flake8-report.txt` - Lint report (PEP8, etc)
 * `tests/junit-report.xml` - Test results in JUnit format (good for Jenkins display)
 * `tests/coverage-report/index.html` - Coverage report

Happy hacking!