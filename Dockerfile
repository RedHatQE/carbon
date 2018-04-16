FROM fedora:27

ADD . /carbon
WORKDIR /carbon

COPY scripts/docker_run_carbon.py /tmp

RUN curl -o /etc/yum.repos.d/beaker-client-Fedora.repo \
https://beaker-project.org/yum/beaker-client-Fedora.repo

RUN dnf install -y python python-pip beaker-client krb5-workstation git wget
RUN pip install beaker-client==23.3

RUN dnf install -y http://hdn.corp.redhat.com/rhel7-csb-stage/RPMS/noarch/\
redhat-internal-cert-install-0.1-7.el7.csb.noarch.rpm

RUN dnf clean all

RUN wget -O oc.tar.gz https://github.com/openshift/origin/releases/download/\
v1.5.0/openshift-origin-client-tools-v1.5.0-031cbe4-linux-64bit.tar.gz && tar \
xvf oc.tar.gz && rm oc.tar.gz && mv openshift-*/oc /usr/bin \
&& rm -rf openshift-*

RUN pip install .

RUN rm -rf /carbon

WORKDIR /
