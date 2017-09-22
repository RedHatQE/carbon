# Carbon Framework

[![Commitizen friendly](https://img.shields.io/badge/commitizen-friendly-brightgreen.svg)](http://commitizen.github.io/cz-cli/)

## What is Carbon Framework?

A framework that creates product interoperability scenarios to support
interoperability tests.

## Is it ready?

No. This is an experiment and it is on heavily development.

## Does it look familiar?

Yes, this code started shamelessly by copying few good stuff from Flask
framework - configuration and few core object structures. Also, there's
a bunch of code that will be transfered from the old pit framework. The
biggest change is in the architecture of the framework which is now task
oriented and carry many design patterns that sustain framework principles.
More to come...

## How is it supposed to work?

Each scenario is a definition written in YAML. The framework loads the
yaml file and build a list of pipelines. Each pipeline will contain lots
of tasks related to the resources. A resource can be a scenario, a host
an action or a report. Each resource will contain many tasks that the
framework will collect, load into its respective pipelines and run in
the order described in the YAML file. For instance, if an action has a
task of type ValidateTask, the framework will collect it and add to the
Validate pipeline.

Basically, when you run the scenario the framework will:

1. Validate your scenario attributes (All Resources)
2. Provision the machines (Hosts)
3. Configure all machines accordingly (Actions)
4. Install all packages for each host (Actions)
4. Run your tests (Executes)
5. Report the results (Reports)

## Development

Ideally you would create a virtual environment with python 3.6. The
framework has been developed to run with python 2.7.x and above.
Download the source code and follow the commands below:

```commandline
$ pip install -r requirements/dev.txt
```

This is going to install the necessary packages to develop/contribute to Carbon.

Next you can install Carbon itself from the source directory so you can
run tests before commit any code:

```commandline
$ pip install --editable .
```

This way any change you do in the source code you don't need reinstall
it and your changes will be reflected right away.

You want to have a configuration file set so you can turn ON and OFF debugging,
and set other development variables. See `examples/my_config.cfg` for an example
how to create a configuration file. (_configuration is still something to be done,
only DEBUG is used at the moment._)

Set the configuration in your environment. You can chose one of the ways below:

1. Create a file at `/etc/carbon/carbon.cfg`
2. Create a environment variable called `CARBON_SETTINGS` and add the path for
   your configuration file.
3. Crate a file called `carbon.cfg` within the same directory you are running
   the carbon scenario or the carbon app.

You can run the command below to test a scenario example (examples/ffinterop.yaml):

```commandline
$ carbon -vvv run --scenario examples/ffinterop.yaml --cleanup always
```

You can also '_develop_' a scenario. Check out the `examples/scenario_app.py`.
To run this scenario, go to the `examples/` folder and run:

```commandline
$ python scenario_app.py
```

Now you can run the tests via Makefile:

```commandline
$ make test
```

Before you commit the code, run a full check to make sure the code is
tested and lint'ed':

```commandline
$ make
```

You can find the reports on the tests directory:

 * `tests/flake8-report.txt` - Lint report (PEP8, etc)
 * `tests/junit-report.xml` - Test results in JUnit format (good for Jenkins display)
 * `tests/coverage-report/index.html` - Coverage report

If your code introduces a new package needed by Carbon. Please read the
short synopsis below to see where you should declare the package name/version:

**setup.py**

Carbon's setup.py module declares packages needed by carbon in order to run.
What does this mean? If you were to install carbon (pip install carbon) in a
fresh environment. It would install all of its required package dependencies.

**requirements/*.txt**

Carbon project has a folder which holds all its requirements files.
Within this folder you will find different requirements files for
development purposes. What does this mean? If you wanted to run carbon's
unit tests, you would need to install the packages declared inside the
tests.txt. This file contains packages such as sphinx or nose as an
example. They are not required in order to run carbon. To
development for carbon, you would want to install the packages from
dev.txt.

## Run carbon framework within a container

This section will explain how you can run carbon framework within a container.
At the root of the project you will find a Dockerfile. You will need to build
a carbon image before running. To build an image, run the following commands:

```commandline
$ cd /path/to/carbon-project
# replace <tag> with the tag name you wish to give
$ docker build -t carbon:<tag> .
```

Once the image is successfully built, you can start the container:

```commandline
# replace <tag> with the tag name you gave to the image when created
$ docker run --name carbon -it carbon:<tag> /bin/sh
/ # carbon --version
carbon, version 0.3.2
```

If you are looking to use beaker and openshift providers you should run this
comamnd when starting container. These providers spawn containers to perform
provisioning. It will mount the docker socket of the host which allows carbon
container to spawn containers on the host system:

```commandline
# replace <tag> with the tag name you gave to the image when created
$ docker run --name carbon -it -v /var/run/docker.sock:/var/run/docker.sock \
carbon:<tag> /bin/sh
```

If you wish to install the develop version of carbon in a new container image.
You will need to append @develop to the end of the git url within the
dockerfile. Then rebuild a new image.

Happy hacking!