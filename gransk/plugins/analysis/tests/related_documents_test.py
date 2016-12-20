#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import unittest
import os
import shutil

import gransk.core.document as document
import gransk.core.helper as helper
import gransk.core.tests.test_helper as test_helper
import gransk.plugins.analysis.related_documents as related_documents


class RelatedDocumentsTest(unittest.TestCase):

  def _init(self, subscriber):
    config = {
        helper.DATA_ROOT: 'local_data/related',
        'worker_id': 0
    }

    if os.path.exists(config[helper.DATA_ROOT]):
      shutil.rmtree(config[helper.DATA_ROOT])

    os.makedirs(config[helper.DATA_ROOT])

    subscriber.setup(config)

    doc1 = document.get_document('dummy1.txt')
    doc1.docid = 'mock'
    doc1.entities.add(0, 'mock1', 'e1')
    doc1.entities.add(1, 'mock2', 'e2')
    doc1.entities.add(2, 'mock3', 'e3')
    subscriber.consume(doc1, None)

    doc2 = document.get_document('dummy2.txt')
    doc2.entities.add(0, 'mock1', 'e1')
    doc2.entities.add(1, 'mock2', 'e2')
    doc2.entities.add(2, 'mock3', 'e4')
    subscriber.consume(doc2, None)

    doc3 = document.get_document('dummy3.txt')
    doc3.entities.add(0, 'mock1', 'e1')
    subscriber.consume(doc3, None)

    subscriber.stop()

  def test_simple(self):
    mock_pipeline = test_helper.get_mock_pipeline([helper.FINISH_DOCUMENT])
    subscriber = related_documents.Subscriber(mock_pipeline)
    self._init(subscriber)

    expected = [
        '{"entity_id": "e1", "type": "mock", "value": "e1"}',
        '{"entity_id": "e2", "type": "mock", "value": "e2"}'
    ]

    actual = subscriber.get_related_to('mock', min_shared=2, min_score=0.2)

    self.assertEqual(1, len(actual))
    self.assertEqual(2, len(actual[0]['shared']))


if __name__ == '__main__':
  unittest.main()
