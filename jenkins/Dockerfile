FROM docker-registry.engineering.redhat.com/centralci/jnlp-slave-base:1.5
#Carbon general requirements
RUN yum install -y gcc python-devel \
 && curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py" \
 && python get-pip.py \ 
 && yum install -y https://centos7.iuscommunity.org/ius-release.rpm \
 && yum install -y python36 \
 && pip install virtualenv
#Carbon beaker requirements
RUN curl -o /etc/yum.repos.d/bkr-client.repo https://beaker-project.org/yum/beaker-client-CentOS.repo \
 && yum install -y beaker-client
ENV LANG=en_US.utf8 LC_ALL=en_US.utf8
