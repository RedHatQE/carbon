# Dockerfiles

This folder contains dockerfiles used by carbon.

## How to build an image

First you will want to change directories into the image you would like to
build. Once you are in the directory, you can run the following command to
build a new image:
```
$ docker build -t <repository_name>:<tag> .
```

## How to push an image to the internal docker registry

First you will need to build the image using the steps above. Once the image
is built, please follow the steps in the following link to see how to
login, tag and push the image. The login is your kerberos username/password.

https://registry-console.engineering.redhat.com/registry
