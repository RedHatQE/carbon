FROM fedora:latest

# Download beaker-client repository
RUN curl -o /etc/yum.repos.d/beaker-client-Fedora.repo \
https://beaker-project.org/yum/beaker-client-Fedora.repo

# Install beaker-client and downgrade to set version (issues running latest)
RUN dnf install -y beaker-client
RUN pip install beaker-client==23.3

# Install package dependencies
RUN dnf install -y krb5-workstation

# Install Red Hat certificates
RUN dnf install -y http://hdn.corp.redhat.com/rhel7-csb-stage/RPMS/noarch/\
redhat-internal-cert-install-0.1-7.el7.csb.noarch.rpm

# Copy beaker conf to /etc/beaker/client.conf
RUN cp /usr/share/doc/beaker-client/client.conf.example /etc/beaker/client.conf

# Download SSL certificate for beaker server
RUN curl -o /etc/beaker/RedHatInternalCA.pem https://engineering.redhat.com/\
Eng-CA.crt

# Update SSL CA certificate defaults
RUN sed -i -e 's/HUB_URL.*/HUB_URL = "https:\/\/beaker.engineering.redhat.'\
'com"/g' /etc/beaker/client.conf
RUN sed -i -e 's/#CA_CERT.*/CA_CERT = "\/etc\/beaker\/RedHatInternalCA.'\
'pem"/g' /etc/beaker/client.conf
RUN sed -i -e 's/#KRB_SERVICE.*/KRB_SERVICE = "HTTP"/g' \
/etc/beaker/client.conf
RUN sed -i -e 's/#KRB_REALM.*/KRB_REALM = "REDHAT.COM"/g' \
/etc/beaker/client.conf

# Set entrypoint to beaker-client, which user can override
ENTRYPOINT ['bkr']
