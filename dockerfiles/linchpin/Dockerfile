FROM fedora:latest
RUN curl -o /etc/yum.repos.d/beaker-client-Fedora.repo \
https://beaker-project.org/yum/beaker-client-Fedora.repo
RUN dnf install -y beaker-client krb5-workstation python-pip gcc \
redhat-rpm-config python-devel openssl-devel && dnf clean all
RUN pip install linchpin>=1.0.0 beaker-client==23.3
RUN dnf install -y http://hdn.corp.redhat.com/rhel7-csb-stage/RPMS/noarch/\
redhat-internal-cert-install-0.1-7.el7.csb.noarch.rpm
RUN cp /usr/share/doc/beaker-client/client.conf.example /etc/beaker/client.conf
RUN curl -o /etc/beaker/RedHatInternalCA.pem https://engineering.redhat.com/\
Eng-CA.crt
RUN sed -i -e 's/HUB_URL.*/HUB_URL = "https:\/\/beaker.engineering.redhat.'\
'com"/g' /etc/beaker/client.conf
RUN sed -i -e 's/#CA_CERT.*/CA_CERT = "\/etc\/beaker\/RedHatInternalCA.'\
'pem"/g' /etc/beaker/client.conf
RUN sed -i -e 's/#KRB_SERVICE.*/KRB_SERVICE = "HTTP"/g' \
/etc/beaker/client.conf
RUN sed -i -e 's/#KRB_REALM.*/KRB_REALM = "REDHAT.COM"/g' \
/etc/beaker/client.conf
ENTRYPOINT ['linchpin']