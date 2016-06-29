# Carbon Framework

## What is Carbon Framework?
A framework for creating scenarios to run interoperability tests.

## Is it ready?

No. This is an experiment, a prototype.

## Does it look familiar?

Yes, this code started shamelessly by copying loads of good stuff from Flask
framework.

## How is it supposed to work?

Each scenario is "an app". You instanciate the framework, use the provisioner
extensions to provision and configure your instances, use the tester extentions
to configure your tests and run.

Basically, when you run the scenario the framework will:

1. Provision the machines
2. Configure all machines accordingly
3. Run your tests
4. Report the results


