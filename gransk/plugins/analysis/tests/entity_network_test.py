#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os
import unittest
import shutil

import gransk.core.document as document
import gransk.core.helper as helper
import gransk.core.tests.test_helper as test_helper

import gransk.plugins.analysis.related_documents as related_documents
import gransk.plugins.analysis.related_entities as related_entities
import gransk.plugins.analysis.entity_network as entity_network


class EntityNetworkTest(unittest.TestCase):

  def test_get_network(self):
    mock_pipeline = test_helper.get_mock_pipeline([helper.FINISH_DOCUMENT])

    entities = related_entities.Subscriber(mock_pipeline)
    documents = related_documents.Subscriber(mock_pipeline)
    network = entity_network.Subscriber(mock_pipeline)

    config = {
        helper.DATA_ROOT: 'local_data/network',
        'worker_id': 1
    }

    if os.path.exists(config[helper.DATA_ROOT]):
      shutil.rmtree(config[helper.DATA_ROOT])

    os.makedirs(config[helper.DATA_ROOT])

    entities.setup(config)
    documents.setup(config)
    network.setup(config)

    doc1 = document.get_document('dummy1.txt')
    doc1.entities.add(0, 'mock', 'e1')
    doc1.entities.add(1, 'mock', 'e2')
    doc1.entities.add(2, 'mock', 'e3')
    mock_pipeline.produce(helper.FINISH_DOCUMENT, doc1, None)

    doc1 = document.get_document('dummy2.txt')
    doc1.entities.add(1, 'mock', 'e2')
    doc1.entities.add(2, 'mock', 'e4')
    mock_pipeline.produce(helper.FINISH_DOCUMENT, doc1, None)

    one_hop = network.get_for('e1', hops=1)
    two_hop = network.get_for('e1', hops=2)

    self.assertNotEqual(0, len(one_hop['nodes']))
    self.assertNotEqual(0, len(one_hop['links']))

    self.assertNotEqual(0, len(two_hop['nodes']))
    self.assertNotEqual(0, len(two_hop['links']))


if __name__ == '__main__':
  unittest.main()
