#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import inspect
from collections import defaultdict
from collections import namedtuple
import os
import sys
from io import BytesIO

from six import text_type as unicode


class MockPipeline(object):

  def __init__(self):
    self.listeners = defaultdict(list)
    self.services = {}
    self.magic = defaultdict(list)
    self.log = sys.stdout
    self.produced_topics = []

  def register_listener(self, topic, callback):
    self.listeners[topic].append(callback)

  def register_service(self, service_id, service):
    self.services[service_id] = service

  def get_service(self, service_id):
    return self.services[service_id]

  def register_magic(self, magic, subscriber):
    self.magic[magic].append(subscriber)

  def produce(self, topic, doc, payload):
    self.produced_topics.append(topic)

    for _, callback in self.listeners.get(topic, []):
      callback(doc, payload)


class MockSubscriber(object):

  def __init__(self):
    self.produced = []

  def consume(self, doc, data):
    self.produced.append((doc, data))


class MockHttpConnection(object):

  def __init__(self, response_text):
    self.response_text = response_text

  def request(self, method, uri, payload, headers):
    pass

  def getresponse(self):
    return BytesIO(self.response_text)


class MockElasticsearchIndex(object):

  def create(self, index, ignore, body):
    pass


class MockElasticsearch(object):
  indices = MockElasticsearchIndex()


class MockElasticsearchHelper(object):

  def __init__(self):
    self._bulk = []

  def bulk(self, _, bulk):
    self._bulk.extend(bulk)


class MockEntityPart(unicode):

  def __init__(self, offset_string):
    offset, string = offset_string

    try:
      # python2
      super(MockEntityPart, self).__init__(string)
    except:
      # python3
      super(MockEntityPart, self).__init__()

    self.offset = offset
    self.string = string


class MockEntity(object):

  def __init__(self, tag, parts):
    self.tag = tag
    self.parts = parts

  def __iter__(self):
    return iter([p.string for p in self.parts])

  def __getitem__(self, key):
    return self.parts[key]

  def __len__(self):
    return len(self.parts)


class MockPolyglot(object):

  ner_entities = []

  def __init__(self, text):
    self.entities = []
    for entity in self.ner_entities:
      parts = []
      offset, string = entity
      for part in string.split():
        parts.append(MockEntityPart((offset, part)))
        offset += len(part) + 1

      self.entities.append(MockEntity('I-PER', parts))



class MockWorker(object):

  def __init__(self):
    self.called = False

  def boot(self, inject, config, path):
    # Ignore.
    _ = (inject, config, path)
    self.called = True
    return []

class MockInjector(object):

  def __init__(self, response_text=None, ner_entities=[]):
    self.response_text = response_text
    self.elastic = MockElasticsearch()
    self.elastic_helper = MockElasticsearchHelper()
    self.polyglot = MockPolyglot
    self.polyglot.ner_entities = ner_entities
    self.worker = MockWorker()

  def set_config(self, config):
    pass

  def get_worker(self):
    return self.worker

  def get_http_connection(self, url=None):
    return MockHttpConnection(self.response_text)

  def get_elasticsearch(self):
    return self.elastic

  def get_elasticsearch_helper(self):
    return self.elastic_helper

  def get_polyglot(self):
    return self.polyglot


def get_mock_pipeline(listen_to):
  mock = MockPipeline()
  mock_module = MockSubscriber()
  if not isinstance(listen_to, list):
    listen_to = [listen_to]
  for listen in listen_to:
    mock.register_listener(listen, ('mock', mock_module.consume))
  mock.consumer = mock_module
  return mock


def get_test_path(filename):
  frame = inspect.stack()[1]
  module = inspect.getmodule(frame[0])
  path = os.path.realpath(module.__file__)
  root = os.path.abspath(os.path.join(path, os.pardir))
  return os.path.join(root, 'test_data', filename)
