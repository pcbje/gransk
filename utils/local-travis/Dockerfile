FROM ubuntu:14.04
MAINTAINER Petter Chr. Bjelland <post@pcbje.com>

ADD gransk/web/tests/package.json /app/gransk/web/tests/package.json
ADD utils/dfvfs-requirements.txt /app/utils/
ADD requirements.txt /app/
WORKDIR /app

RUN apt-get update
RUN apt-get install --force-yes -y build-essential make curl git
RUN curl -sL https://deb.nodesource.com/setup_0.12 | sudo bash -
RUN apt-get install --force-yes -y \
    python-pip python3.4 python3-pip nodejs python-dev \
    zlib1g-dev unzip p7zip-full p7zip-rar libicu-dev poppler-utils ghostscript \
    fontconfig rubygems-integration

RUN gem install coveralls-lcov

# libewf bzip2 dependency error hack
RUN apt-get remove --purge -y bzip2 libbz2-dev
RUN pip install -r utils/dfvfs-requirements.txt
RUN pip3 install -r utils/dfvfs-requirements.txt
RUN apt-get install --force-yes -y bzip2 libbz2-dev

RUN pip install -r requirements.txt
RUN pip3 install -r requirements.txt

RUN cp gransk/web/tests/package.json /opt && npm install --prefix=/opt /opt
