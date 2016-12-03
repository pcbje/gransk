#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import unittest
import logging

import gransk.core.helper as helper
import gransk.core.tests.test_helper as test_helper
import gransk.core.document as document
import gransk.plugins.storage.es_index as index_text


logging.basicConfig(
    format=u'[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
    level=logging.INFO,
    datefmt=u'%Y-%m-%d %H:%M:%S')


class IndexTest(unittest.TestCase):

  def _init(self):
    mock_pipeline = test_helper.get_mock_pipeline([])

    injector = test_helper.MockInjector('{}')

    _index_text = index_text.Subscriber(mock_pipeline)
    _index_text.setup({
        'tag': 'default',
        'context_size': 14,
        helper.INJECTOR: injector
    })

    doc = document.get_document('mock.txt')
    doc.text = u'abcd mock-value efgh'
    doc.entities.add(5, u'mock-type', u'mock-value')

    _index_text.consume(doc, None)

    _index_text.stop()

    return injector.elastic_helper._bulk

  def test_document(self):
    expected_doc = {
        u'_id': 'e0f1e9fe4a2be1e5601679f608632682',
        u'_type': u'document', u'_source': {
                'status': 'unknown', 'parent': None,
                'text': 'abcd mock-value efgh',
                'tag': 'default', 'path': 'mock.txt',
                'id': 'e0f1e9fe4a2be1e5601679f608632682', 'exists': False,
                'doctype': 'unknown', 'filename': 'mock.txt', 'ext': 'txt',
                'meta': {'added': 'mock-time', 'size': -1}
        },
        u'_op_type': u'index', u'_index': u'gransk'}

    bulk = self._init()

    actual_doc = bulk[0]
    actual_doc['_source']['meta']['added'] = 'mock-time'

    self.assertEqual(sorted(expected_doc), sorted(actual_doc))

  def test_entity(self):
    bulk = self._init()

    expected_entity = {
        u'_id': 'mock-value\x00mock-type', u'_type': u'entity',
        u'_source': {
            'entity_id': 'mock-type', 'type': 'mock-value', 'value': 'mock-type'
        },
        u'_op_type': u'index', u'_index': u'gransk'}

    actual_entity = bulk[1]

    self.assertEqual(sorted(expected_entity), sorted(actual_entity))

  def test_in_doc(self):
    bulk = self._init()

    actual_in_doc = bulk[2]

    expected_in_doc = {
        u'_id': '79f608632682\x00mock-type\x00mock-value\x005',
        u'_type': u'in_doc', u'_source': {
            'raw_entity': (
                '{"entity_id": "mock-type", "type": "mock-value",'
                ' "value": "mock-type"}'),
            'entity_id': 'mock-type', 'doc_path': 'mock.txt',
            'context': 'cd mock-value efg', 'doc_filename': 'mock.txt',
            'entity_type': 'mock-value', 'entity_value': 'mock-type',
            'doc_id': 'e0f1e9fe4a2be1e5601679f608632682'
        },
        u'_op_type': u'index', u'_index': u'gransk'}

    self.assertEqual(sorted(expected_in_doc), sorted(actual_in_doc))


if __name__ == '__main__':
  unittest.main()
