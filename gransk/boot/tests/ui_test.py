#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import unittest
import tempfile
import shutil

import gransk.boot.ui
import gransk.core.helper as helper
import gransk.core.tests.test_helper as test_helper


class MockEntityNetwork(object):

  def get_for(self, entity_id, hops):
    return {'mock': 'mock'}


class MockRelated(object):

  def load_all(self, config):
    pass

  def get_related_to(self, _id):
    return ['mock1', 'mock2', 'mock3']


class MockElasticsearch(object):

  def create_mapping(self):
    pass


class MockPipeline(object):

  def __init__(self):
    self.services = {
        'related_entities': MockRelated(),
        'related_documents': MockRelated(),
        'elasticsearch': MockElasticsearch(),
        'entity_network': MockEntityNetwork()
    }

  def get_service(self, sid):
    return self.services[sid]


class MockPipelineMod(object):
  pipe = MockPipeline()

  @staticmethod
  def build_pipeline(config):
    MockPipelineMod.pipe = MockPipeline()
    return MockPipelineMod.pipe


class MockRunMod(object):

  @staticmethod
  def load_config(args):
    return {
        helper.HOST: 'mock',
        helper.DATA_ROOT: os.path.join('local_data', 'unittests')
    }

  @staticmethod
  def clear_data(config):
    pass


class UiTest(unittest.TestCase):

  def setUp(self):
    gransk.boot.ui.setup(test_helper.MockArgs('config.default.yml'), MockPipelineMod.pipe, MockRunMod, test_helper.MockInjector())
    gransk.boot.ui._globals['test'] = True
    self.app = gransk.boot.ui.app.test_client()
    self.pipe = MockPipelineMod.pipe

  def test_get_index(self):
    rv = self.app.get('/')
    assert b'<title' in rv.data

  def test_clear_data(self):
    self.pipe.get_service('related_entities').buckets = 'MOCK MOCK'
    self.pipe.get_service('related_documents').buckets = 'MOCK MOCK'
    rv = self.app.delete('/data')

    expected = {}
    actual_ents = self.pipe.get_service('related_entities').buckets
    actual_docs = self.pipe.get_service('related_documents').buckets

    self.assertEqual(expected, actual_ents)
    self.assertEqual(expected, actual_docs)

  def test_get_picture(self):
    picture_root = os.path.join(
        MockRunMod.load_config(None)[helper.DATA_ROOT], '..', 'pictures')

    try:
      shutil.rmtree(picture_root)
    except:
      pass

    try:
      os.makedirs(picture_root)
    except:
      pass

    with open(os.path.join(picture_root, 'test.jpg'), 'wb') as out:
      out.write(b'abcde')

    rv = self.app.get('/picture?name=test.jpg&mediatype=image/jpeg')

    expected = b'abcde'
    actual = rv.data

    self.assertEqual(expected, actual)

  def test_get_related_documents(self):
    rv = self.app.get('/related?type=document&id=mock')

    expected = b'["mock1", "mock2", "mock3"]'
    actual = rv.data

    self.assertEqual(expected, actual)

  def test_get_related_entities(self):
    rv = self.app.get('/related?type=entity&id=mock')

    expected = b'["mock1", "mock2", "mock3"]'
    actual = rv.data

    self.assertEqual(expected, actual)

  def test_get_entity_network(self):
    rv = self.app.get('/network?hops=5&entity_id=mock')

    expected = b'{"mock": "mock"}'
    actual = rv.data

    self.assertEqual(expected, actual)


if __name__ == '__main__':
  unittest.main()
