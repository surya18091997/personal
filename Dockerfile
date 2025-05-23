ARG pythonVersion=3.11-slim-bullseye

FROM docker.ci.artifacts.c.com/wce-docker/ca-roots:latest AS roots
FROM docker.ci.artifacts.c.com/hub-docker-release-remote/library/python:${pythonVersion} AS build

ARG runModuleAsEntryPoint
ARG pythonEntryPointFile

# Install c root certificates and tell python to use them
COPY --from=roots /usr/local/share/ca-certificates /usr/local/share/ca-certificates
COPY --from=roots /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
RUN update-ca-certificates

# c PROXY
ENV http_proxy='http://sysproxy.c.com:8080'
ENV https_proxy='http://sysproxy.c.com:8080'

# required packages
RUN apt-get update --allow-releaseinfo-change && apt-get install -y --allow-unauthenticated --no-install-recommends \
   apt-utils \
   apt-transport-https \
   debconf-utils \
   gcc \
   g++ \
   build-essential \
   gnupg \
   rng-tools \
   curl \
   ghostscript \
   sshpass \
   openssh-client \
   openssh-server \
   tzdata \
   wget \
   python3-dev \
   unixodbc \
   unixodbc-dev \
   libxml2 libxml2-dev libxslt-dev \
   openjdk-11-jre-headless \
   && apt-get clean && \
   rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME environment variable for Java (required for PySpark)
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

#Non Root User Configuration
RUN addgroup --system --gid 10001 appgrp && \
   adduser --system --uid 10000 --shell /sbin/nologin --home /opt/app/ --ingroup appgrp app

WORKDIR /etc/ld.so.conf.d

# Set up IBM DB2 driver
RUN wget https://mvn.ci.artifacts.c.com/artifactory/gbs-peoplebenefitsdomain-mvn/com/ibm/odbc-cli/linuxx64_odbc_cli/11.5.5.0/linuxx64_odbc_cli.tar.gz && \
   tar -xf linuxx64_odbc_cli.tar.gz && \
   echo /etc/ld.so.conf.d/clidriver/lib > db2.conf && \
   ldconfig && \
   rm linuxx64_odbc_cli.tar.gz

ENV IBM_DB_HOME=/etc/ld.so.conf.d/clidriver
ENV LD_LIBRARY_PATH=/etc/ld.so.conf.d/clidriver/lib:$LD_LIBRARY_PATH
ENV LIBRARY_PATH=/etc/ld.so.conf.d/clidriver/lib:$LIBRARY_PATH
ENV PATH=/etc/ld.so.conf.d/clidriver/bin:$PATH

## Set Pip Properties
RUN echo "[global]" >> /etc/pip.conf && \
   echo "index-url = https://repository.cache.c.com/repository/pypi-proxy/simple/" >> /etc/pip.conf && \
   echo "trusted-host = repository.c.com" >> /etc/pip.conf

RUN export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt && pip3 --timeout=1000 install --upgrade pip \
   && chmod -R a+rwx /opt/app

ADD . /opt/app
COPY . /opt/app
WORKDIR /opt/app

RUN pwd
RUN ls -ltr
RUN cat /opt/app/requirements.txt

#install requirements
# RUN pip install -i https://pypi.ci.artifacts.c.com/artifactory/api/pypi/gbs-peoplebenefitsdomain-pypi/simple -r requirements.txt
RUN export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt && pip --timeout=1000 install -r requirements.txt

# Set up directories and permissions
RUN chown -R 10000:10001 /opt/app && \
   chown -R 10000:10001 /etc/ld.so.conf.d/clidriver && \
   chmod -R 755 /opt/app && \
   chmod -R 755 /etc/ld.so.conf.d/clidriver

ENV runModuleEntryPoint=${runModuleAsEntryPoint}
ENV pythonEntryPoint=${pythonEntryPointFile}

# Switch to non-root user
USER 10000

# Setup entry point script
RUN if [ "$runModuleEntryPoint" = "true" ]; then \
       echo "#!/bin/sh" > /opt/app/entrypoint.sh && \
       echo "python -m $pythonEntryPoint" >> /opt/app/entrypoint.sh; \
   elif [ "$runModuleEntryPoint" = "false" ] && [ -e /opt/app/app.py ]; then \
       echo "#!/bin/sh" > /opt/app/entrypoint.sh && \
       echo "python app.py" >> /opt/app/entrypoint.sh; \
   elif [ "$runModuleEntryPoint" = "false" ] && [ -e /opt/app/run.py ]; then \
       echo "#!/bin/sh" > /opt/app/entrypoint.sh && \
       echo "python run.py" >> /opt/app/entrypoint.sh; \
   elif [ "$runModuleEntryPoint" = "false" ]; then \
       echo "#!/bin/sh" > /opt/app/entrypoint.sh && \
       echo "$pythonEntryPoint" >> /opt/app/entrypoint.sh; \
   fi

RUN chmod +x /opt/app/entrypoint.sh

##########################################################################################
#Pytet Integration

RUN coverage run --source=src -m pytest --junitxml=reports/xunit-result-app.xml
RUN coverage xml -i -o reports/coverage.xml

#########################################################################################

#Sonar Integration for the coverage
FROM docker.prod.c.com/strati/docker-sonarqube-scanner:latest AS sonar
ARG sonarEnable
ARG eventFlow
ARG eventType
ARG sonarOpts
ARG sonarBranchAnalysis
ARG sonarPRargs
RUN mkdir /opt/app
WORKDIR /opt/app


COPY --from=build /opt/app /opt/app
RUN ls -ltr
RUN echo '===== BEGIN SONAR PHASE =====' && \
    if [ "${sonarEnable}" = "true" ]; then \
      echo "This is the eventFlow ${eventFlow} and eventType ${eventType}" && \
      if [ "${eventFlow}" = "branch" ] && [ "${eventType}" = "push" ]; then \
        echo "sonarBranchAnalysis = ${sonarBranchAnalysis} " && \
        echo "Sonar opts for branch analysis ${sonarOpts} "; \
      else \
        export sonarBranchAnalysis="" ; \
      fi && \
      if [ "${eventType}" = "pr" ]; then \
        echo "sonarPRargs = ${sonarPRargs} " && \
        echo "Sonar opts for pr analysis ${sonarOpts} "; \
      else \
        export sonarPRargs="" ; \
      fi && \
      sonar-scanner --debug ${sonarOpts} ${sonarPRargs} ${sonarBranchAnalysis}; \
    else \
      echo 'SonarQube disabled.'; \
    fi && \
    echo '===== END SONAR PHASE ====='


######################################################################

# Final runtime image
FROM build AS run

# Set up directories and permissions again in runtime stage
RUN chown -R 10000:10001 /opt/app && \
   chown -R 10000:10001 /etc/ld.so.conf.d/clidriver && \
   chmod -R 755 /opt/app && \
   chmod -R 755 /etc/ld.so.conf.d/clidriver && \
   chmod +x /opt/app/entrypoint.sh

# Explicitly switch to non-root user in runtime stage
USER 10000

WORKDIR /opt/app
EXPOSE 8080
ENTRYPOINT ["/bin/sh", "/opt/app/entrypoint.sh"]
