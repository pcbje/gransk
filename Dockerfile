FROM ubuntu:14.04
MAINTAINER Petter Chr. Bjelland <post@pcbje.com>

ADD gransk /app/gransk
ADD utils /app/utils
ADD config.yml /app/config.yml
ADD requirements.txt /app/requirements.txt
ADD run_tests.py /app/run_tests.py
ADD setup.py /app/setup.py
ADD README.md /app/README.md
WORKDIR /app

RUN apt-get update
RUN apt-get install --force-yes -y \
      python-dev python-setuptools zlib1g-dev unzip p7zip-full p7zip-rar \
      python-pip libicu-dev poppler-utils ghostscript && \
  pip install -r utils/dfvfs-requirements.txt && \
  pip install -r requirements.txt && \
  python setup.py install && \
  python setup.py download

RUN python run_tests.py

RUN apt-get install --force-yes -y \
    nodejs nodejs-legacy npm openjdk-7-jdk fontconfig && \
    cd gransk/web/tests/ && rm -rf node_modules && npm install && cd ../../../ && \
    gransk/web/tests/node_modules/.bin/karma start gransk/web/tests/cover.conf.js && \
    rm -rf gransk/web/tests/node_modules && \
    apt-get remove --force-yes -y --purge \
        nodejs nodejs-legacy npm default-jre openjdk-7-jdk fontconfig && \
    apt-get --force-yes -y autoremove

ENTRYPOINT ["python", "-m", "gransk.boot.ui", "--host=0.0.0.0"]
