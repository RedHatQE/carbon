Carbon + Linchpin dockerfiles
=============================

A folder containing dockerfiles for operating systems to use carbon and
linch-pin tool. This README will will go through the following actions:

1. Create an image from dockerfile
2. Start a container based on image created
3. Run carbon and linch-pin from the container

Prerequisite
============

You will need to have docker installed on your machine and the service is
running. If you do not have docker installed, please refer to their
documentaton to get started: https://docs.docker.com/engine/getstarted/

Create an image from dockerfile
==================================

First change directories into the operating system you would like to have the
container based on. For this example I will be using Fedora.
```
$ cd ./dockerfiles/carbon-linchpin/fedora
```

You will see a file named "Dockerfile". If you view the content, you will see
it has various commands to setup the system with linch-pin. Run the following
command to build your image:
```
$ docker build -t carbon-linchpin:fedora .
```

You can give whatever name you want for the (-t) name:tag. This command may
take a few minutes to complete. If it is successful, you should see something
like "successfully built 623c332...".

Start a container based on the image created
============================================

Lets view the image that we built in the last step. Run the following command
to view all images on your machine:
```
$ docker images
[output snippet]
REPOSITORY                                TAG                 IMAGE ID            CREATED             SIZE
carbon-linchpin                           fedora              f112990ef93a        25 hours ago        997MB
```

As you can see from the output snippet there is our image we just created.
Lets start a new container in an interactive mode. This will allow us to have
a shell prompt into the container.
```
$ docker run -it carbon-linchpin:fedora /bin/bash
[root@01512f78146e /]#
```

You will notice your terminal prompt changes to the one for the container. All
commands run from here on are within the container.

Run carbon and linch-pin from the container
=========================================

Now that we have our container up and running. Lets run carbon and linchpin.
First we will need to activate the python virtual environment that was created
when the image was built.
```
[root@01512f78146e /]# source ~/carbon/bin/activate
(carbon) [root@01512f78146e ~]#
```

Now that the virtual environment is activated, we can call carbon & linchpin.
```
(carbon) [root@01512f78146e ~]# carbon --version
0.0.0
(carbon) [root@01512f78146e ~]# linchpin --version
LinchpinCLI v1.0.0
WORKSPACE = /root/
```

You can now begin to use carbon and linch-pin tool within the container.
Containers are a nice way to development and test without adding lots of
packages to your host machine.

Helpful docker commands
=======================

1. List all images
```
$ docker images
```

2. List running containers
```
$ docker ps
```

3. List all containers
```
$ docker ps -a
```

4. Remove a stopped container
```
$ docker rm <container_id>
```

5. Remove a image
```
$ docker rmi <image_id>
```

6. Copy files to a running container
```
$ docker cp ~/file <container_id>:/
```

7. Start a container
```
$ docker start <container_id>
```

8. Run a command in a running container with interactive mode
```
$ docker exec -it <container_id> /bin/bash
```
