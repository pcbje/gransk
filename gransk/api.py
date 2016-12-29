#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import requests
import time
import json
import hashlib
import logging
import threading
import traceback
import yaml
import os
import sys
import shutil

import six.moves.http_client

import gransk.core.compat as _
import gransk.core.pipeline as pipeline
import gransk.core.document as document
import gransk.core.helper as helper
import gransk.core.abstract_subscriber as abstract_subscriber

logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('requests').setLevel(logging.ERROR)
logging.getLogger('polyglot').setLevel(logging.ERROR)
logging.basicConfig(
      format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
      level=logging.INFO,
      datefmt='%Y-%m-%d %H:%M:%S')

LOGGER = logging.getLogger('MAIN')


class Subscriber(abstract_subscriber.Subscriber):
  """For starting the processing of a document."""

  CONSUMES = []

  def setup(self, config):
    """
    Set maximum document size.

    :param config: Configuration object.
    :type config: ``dict``
    """
    super(Subscriber, self).setup(config)
    self.max_size = config.get(helper.MAX_FILE_SIZE, 0) * 1024 * 1024
    self.diskimages = set(
        config.get(helper.EXT_TYPES, {}).get(helper.DISKIMAGE, []))

  def consume(self, doc, file_object=None):
    """
    Run document through pipeline.

    :param doc: Document to process.
    :param file_object: File pointer to doc. If None, param doc.path is opened.
    :type doc: ``gransk.core.document.Document``
    :type file_object: ``file``
    """

    try:
      if self.max_size > 0 and doc.meta['size'] > self.max_size:
        if doc.path.split('.')[-1].lower() in self.diskimages:
          pass
        else:
          doc.status = 'oversized'
          self.produce(helper.OVERSIZED_FILE, doc, None)
          return

      if not file_object:
        file_object = open(doc.path, "rb")

      self.produce(helper.EXTRACT_META, doc, file_object)
      self.produce(helper.PROCESS_FILE, doc, file_object)

      file_object.close()

    except Exception as err:
      doc.meta['gransk_error'] = six.text_type(err)
      traceback.print_exc(file=sys.stdout)


class API(object):
  def __init__(self, injector=None, config_path=None):
    if not injector:
      import gransk.core.injector as _injector
      injector = _injector.Injector()

    code_root = os.path.realpath(
          os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

    if not config_path:
      config_path = os.path.join(code_root, 'config.yml')

    with open(config_path) as inp:
      self.config = yaml.load(inp.read())

    self.config['worker_id'] = 0
    self.config['injector'] = injector
    self.config['injector'].set_config(self.config)

    self.config[helper.CODE_ROOT] = code_root
    self.config[helper.DATA_ROOT] = os.path.join(code_root, 'local_data')
    self.config[helper.WORKERS] = 1
    self.config[helper.TAG] = 'default'
    self.config[helper.MAX_FILE_SIZE] = getattr(self.config, helper.MAX_FILE_SIZE, 0)
    self.config[helper.SUBSCRIBERS].extend([
      'gransk.core.detect_type'
    ])

    self.pipeline = pipeline.build_pipeline(self.config)
    self.entrypoint = Subscriber(self.pipeline)
    self.entrypoint.setup(self.config)
    self.write_lock = threading.Lock()

  def add_file(self, doc, file_object):
    with self.write_lock:
      return self.entrypoint.consume(doc, file_object=file_object)

  def clear_all(self):
    """Clear all processed data."""
    with self.write_lock:
      self._clear_all()

  def _clear_all(self):
    try:
        if os.path.exists(self.config[helper.DATA_ROOT]):
          shutil.rmtree(self.config[helper.DATA_ROOT])
        os.makedirs(self.config[helper.DATA_ROOT])
        os.makedirs(os.path.join(self.config[helper.DATA_ROOT], 'pictures'))
        os.makedirs(os.path.join(self.config[helper.DATA_ROOT], 'files'))
        os.makedirs(os.path.join(self.config[helper.DATA_ROOT], 'archives'))
        os.makedirs(os.path.join(self.config[helper.DATA_ROOT], 'archives', '.tmp'))
    except Exception as err:
       print (">>", err)

    connection = self.config['injector'].get_http_connection('%s:%s' % (self.config['es_host'][0], 9200))
    connection.request('DELETE', '/gransk', '', {})

    if os.path.exists(self.config[helper.DATA_ROOT]):
       shutil.rmtree(self.config[helper.DATA_ROOT])

    # hmm..
    time.sleep(2)

    if self.pipeline.get_service('elasticsearch'):
      self.pipeline.get_service('elasticsearch').create_mapping()
    if self.pipeline.get_service('related_entities'):
      self.pipeline.get_service('related_entities').buckets = {}
    if self.pipeline.get_service('related_documents'):
      self.pipeline.get_service('related_documents').buckets = {}

  def stop(self):
    self.pipeline.stop()
