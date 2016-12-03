# Gransk - Document processing for investigations

A tool for when you have a bunch of documents to figure out of. [Introduction to Gransk (YouTube)](https://youtu.be/RMBiL2NYQFU)

[![Build Status](https://travis-ci.org/pcbje/gransk.svg?branch=master)](https://travis-ci.org/pcbje/gransk) [![Documentation Status](https://readthedocs.org/projects/gransk/badge/?version=latest)](http://gransk.readthedocs.io/?badge=latest)
 [![Coverage Status](https://coveralls.io/repos/github/pcbje/gransk/badge.svg?branch=master)](https://coveralls.io/github/pcbje/gransk?branch=master)

Gransk is an open source tool that aims to be a Swiss army knife of document processing and analysis.
Its primary objective is to quikly provide users with insight to their documents during investigations.
It includes a processing engine written in Python and a web interface. Under the hood it uses Apache Tika for
content extraction, Elasticsearch for data indexing, and dfVFS to unpack disk images.

## Quickstart

##### Using [VirtualBox](https://www.virtualbox.org/wiki/Downloads):

1. Download Gransk VM: https://drive.google.com/uc?export=download&id=0B6iPjQOwe4MKSzl3MEdrajBZdGM
2. Open VirtualBox and click "File" -> "Import appliance". Choose downloaded VM.
3. Double click on the imported machine. (Hold shift to run in background)
4. After a couple of seconds. open a web browser and go to [http://localhost:8084](http://localhost:8084)

##### Using [Docker](https://www.docker.com):

```
curl -o docker-quickstart.sh -X GET https://github.com/pcbje/gransk/raw/master/docker-quickstart.sh
sh ./docker-quickstart.sh
```


## Features

* Unpack disk images with dfVFS and archives with 7zip
* Extract metadata and text from documents with Apache Tika
* Named entity recognition with Polyglot (NER) and Namefinder
* Entity extraction with regular expressions
* Simple data statistics
* Search and explore data with Elasticsearch
* +++

Processing tested on Python 2.7 and 3.4. The web interface requires a modern web browser.

## Processing overview

![](https://pcbje.github.io/images/gransk-overview.png)

## Development

#### Subscribers

Subscribers are registered in config.yml.

```python
import gransk.core.abstract_subscriber as abstract_subscriber
import gransk.core.helper as helper


class Subscriber(abstract_subscriber.Subscriber):
  CONSUMES = [helper.PROCESS_TEXT]

  def consume(self, doc, text):
    doc.meta['num_chars'] = len(text)
```

#### Programmatically adding files

```python
import io

import gransk.api as api
import gransk.core.document as document

gransk = api.API(u'config.yml')

doc = document.get_document(u'filename-or-path.txt')
doc.tag = u'demo'

content = io.BytesIO(b'Data buffer')

gransk.add_file(doc, content)

gransk.stop()
```

## Conventions, code quality and documentation

#### Processing

```
autopep8 --indent-size 2 --max-line-length 80 --in-place --recursive --aggressive gransk
py.test --cov-report html --cov gransk gransk
pylint --rcfile=.pylintrc gransk
```

#### Web interface

```
cd gransk/web/tests && npm install && cd ../../../
gransk/web/tests/node_modules/.bin/karma start gransk/web/tests/cover.conf.js
gransk/web/tests/node_modules/.bin/karma start gransk/web/tests/watch.conf.js
jshint gransk/web/static/modules/* gransk/web/tests/spec/modules/*
```

#### Continuous integration

https://travis-ci.org/pcbje/gransk

Test build:
```
docker build -t gransk-prebuilt -f utils/local-travis/Dockerfile .
docker run -v $PWD:/app --entrypoint=python -it gransk-prebuilt utils/local-travis/mock-travis.py
```

#### Documentation

http://gransk.readthedocs.io

Generate docs locally:
```
pip install sphinx sphinx_rtd_theme
sphinx-build -c docs -b html docs/ local_data/build
```


## Building

```
git clone https://github.com/pcbje/gransk && cd gransk
virtualenv pyenv
source pyenv/bin/activate
pip install -r utils/dfvfs-requirements.txt
pip install -r requirements.txt
python setup.py install
python setup.py download
```


## Processing from command line

```
python -m gransk.boot.run /path/to/data
python -m gransk.boot.run --help
```

Using Docker:

```
docker run -v /path/to/data:/data --entrypoint=python -i -t pcbje/gransk -m gransk.boot.run --workers=4 /data
```

## Starting web UI

```
python -m gransk.boot.web
```

Using Docker:

```
docker run -p 8084:8084 --entrypoint=python -i -t pcbje/gransk -m gransk.boot.ui --host=0.0.0.0
```

## Searching

See [es-auto-query](https://github.com/pcbje/es-auto-query).

## Licenses

* dfVFS: Apache License Version 2.0
* Apache Tika: Apache License Version 2.0
* 7zip: GNU LGPL
* Elasticsearch: Apache License Version 2.0
* Polyglot: GNU GENERAL PUBLIC LICENSE
* Flask: BSD

## Uh, "gransk"?

"Gransk" is imperative form of "investigate" in Norwegian.
