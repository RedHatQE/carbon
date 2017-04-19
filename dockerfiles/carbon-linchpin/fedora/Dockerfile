# Dockerfile based on Fedora latest which has carbon devel and linch-pin
# devel installed and ready to use for cloud and beaker providers.

FROM fedora:latest

# Install Red Hat Certificates
RUN dnf install -y http://hdn.corp.redhat.com/rhel7-csb-stage/RPMS/noarch/\
redhat-internal-cert-install-0.1-7.el7.csb.noarch.rpm

# Install system dependencies for linch-pin
RUN dnf install -y \
python-virtualenv \
libffi-devel \
openssl-devel \
libyaml-devel \
gmp-devel \
libselinux-python \
make \
krb5-workstation \
krb5-devel \
git \
gcc \
redhat-rpm-config \
libxslt \
libxml2 \
libxml2-devel \
libxslt \
libxslt-devel \
python-libxml2 \
libxslt-python

# Create virtual environment, install carbon and linch-pin
RUN virtualenv ~/carbon; \
source ~/carbon/bin/activate; \
git clone https://code.engineering.redhat.com/gerrit/p/carbon.git -b develop \
~/carbon-source; \
git clone https://github.com/CentOS-PaaS-SIG/linch-pin --recursive \
~/linchpin-source; \
cd ~/carbon-source; \
pip install -r requirements.txt; \
pip install --editable .; \
carbon --version; \
pip install requests==2.10.0; \
pip install jinja2==2.8; \
pip install pbr==2.0.0; \
cd ~/linchpin-source; \
pip install pip --upgrade; \
pip install setuptools --upgrade; \
pip install .; \
pip install beaker-common==24.1; \
pip install beaker-client==23.3; \
pip install python-krbv; \
linchpin --version
