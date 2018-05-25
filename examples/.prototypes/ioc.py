"""
Why I was wrong about adapter pattern?

Adapter pattern is a structural design that helps
us make two incompatible interfaces compatible.
For this reason we would have to have our own provisioner
which does not make sense to what we want to achieve.

+---------------+                              +---------------+
|               |         +---------+          |               |
|    Carbon     |         |         |          |     Some      |
|  Provisioner  +-------> | Adapter +--------> |  Provisioner  |
|               |         |         |          |               |
+---------------+         +---------+          +---------------+

For using an adapter pattern we have to implent our own
provisioner and translate that to some other provisioner.
That's not the case! I was wrong.

What works best then, in my view?

Inversion of control. Why?

As a framework, we want to define the overall structure, classes
and objects, key responsibilities, how classes collaborate with
each other, thread control etc. A framework has these parameters
predefined, so the quality engineer concentrates on the specifics
of the testing scenario.

We define the design decision through the framework, that is common
to the interop. testing scenarios domain. Therefore we do design reuse
over code reuse. (think about that!)

Reuse on this level leads to an inversion of control between the
application and the software on which it's based. Our current framework
is more considered to a toolkit than to a framework, because we use it
by writing the main body of the application (override.py for example)
and we call the code we want to reuse. A framework we reuse the main
body and write the code it calls. The operations we have to write have
particular names and calling conventions, but that reduces the design
decisions the qe engineer has to make.

+------------------------+                        +----------------------------------------+
| core.CarbonProvisioner +-----------------------^+resources.Host                          |
++------+----------------+                        +----------------------------------------+
 ^      ^                                         |# __provisioner = core.CarbonProvisioner|
 |      |                                         +----------------------------------------+
 |      |                                         || __init__(provisioner) = None          |
 |     ++------------------------------+          +----------------------------------------+
 |     | provisioners.CiopsProvisioner |
 |     +-------------------------------+
 |
++---------------------------------+
| provisioners.LinchpinProvisioner |
+----------------------------------+


What we gain with inversion control for provisioners:

    * prevent issues if we switch provisioner
    * we focus on the task of provisioning instead of the provisioner
    * decouple the task execution from the implementation
    * carbon relies on "contracts" with these providers and it does not
      need to know how these provisioners do what they do.

"""


class CarbonProvisioner(object):
    """
    This is the base class for all provisioners for provisioning machines
    This is where the contract is written
    """
    def create(self):
        raise NotImplementedError


class CiopsProvisioner(CarbonProvisioner):
    """
    Ciops version 1 for provisioning machines
    This is where we use Ciops tools to provisioning the
    machines and we implement the functions from the CarbonProvisioner
    contract we created above.
    """

    def create(self):
        print('  Provisioning from {klass}'
              .format(klass=self.__class__))


class LinchpinProvisioner(CarbonProvisioner):
    """
    Ciops version 2 for provisioning machines
    This is where we use Linchpin tool for provisioning the
    machines and we implement the functions from the CarbonProvisioner
    contract we created above.
    """

    def create(self):
        print('  Provisioning from {klass}'
              .format(klass=self.__class__))


class Host(object):
    """ Example of a host object """
    __provisioner = None

    def __init__(self, name, provisioner=None):
        if provisioner is None:
            raise Exception('A provisioner needs to be specified')
        self.__provisioner = provisioner
        self.__name = name

    def create_host(self):
        print('{0}:'.format(self.__name))
        self.__provisioner.create()

    def get_name(self):
        return self.__name


PROVISIONER = 'aa'

if __name__ == '__main__':

    # Default is Linchpin provisioner
    prov = LinchpinProvisioner()
    if PROVISIONER == 'ciops':
        prov = CiopsProvisioner()

    instances = []
    # Suppose run through YAML and we have 5 machines
    for i in range(3):
        instances.append(Host('machine_{0}'.format(i), provisioner=prov))

    h = Host('hw_machine', provisioner=CiopsProvisioner())

    # This function now could send each instance to list
    # of workers (think something like Celery or RabbitMQ etc)
    for instance in instances:
        instance.create_host()

    h.create_host()
