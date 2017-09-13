FROM alpine:3.6
RUN apk add --no-cache python py-pip gcc libffi libffi-dev openssl \
    openssl-dev python-dev git curl linux-headers musl-dev make docker
RUN curl -o /usr/local/share/ca-certificates/RH-IT-Root-CA.crt \
    https://password.corp.redhat.com/RH-IT-Root-CA.crt && \
    update-ca-certificates
RUN pip install --no-cache-dir \
    git+https://code.engineering.redhat.com/gerrit/p/carbon.git
