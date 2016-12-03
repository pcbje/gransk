#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import unittest

import gransk.core.helper as helper
import gransk.core.tests.test_helper as test_helper
import gransk.plugins.analysis.related_entities as related_entities
import gransk.plugins.analysis.tests.related_documents_test as rtd


class RelatedEntitiesTest(rtd.RelatedDocumentsTest):

  def test_simple(self):
    mock_pipeline = test_helper.get_mock_pipeline([helper.FINISH_DOCUMENT])
    subscriber = related_entities.Subscriber(mock_pipeline)
    self._init(subscriber)

    actual = subscriber.get_related_to('e1', min_shared=2, min_score=0.2)

    self.assertEquals(2, len(actual[0]['shared']))


if __name__ == '__main__':
  unittest.main()
