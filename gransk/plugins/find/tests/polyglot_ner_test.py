#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import unittest

import gransk.core.helper as helper
import gransk.core.document as document
import gransk.plugins.find.polyglot_ner as _find_names
import gransk.core.tests.test_helper as test_helper

logging.getLogger('polyglot').setLevel(logging.ERROR)


class FindNamesNerTest(unittest.TestCase):

  def test_simple(self):
    config = {
        'code_root': '.',
        helper.INJECTOR: test_helper.MockInjector(
            ner_entities=[(10, u'Hans Petter')])
    }
    find_names = _find_names.Subscriber(test_helper.get_mock_pipeline([]))
    find_names.setup(config)
    doc = document.get_document('dummy')
    doc.text = u'Dette  er Hans Petter.'
    find_names.consume(doc, None)
    expected = [(10, {
        'entity_id': u'Hans_Petter',
        'type': u'per',
        'value': u'Hans Petter'
    })]
    self.assertEqual(expected, doc.entities.get_all())


if __name__ == '__main__':
  unittest.main()
