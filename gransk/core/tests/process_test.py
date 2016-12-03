#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import unittest

import gransk.core.process as process
import gransk.core.helper as helper
import gransk.core.document as document
import gransk.core.tests.test_helper as test_helper


class BootstrapTest(unittest.TestCase):

  def test_simple(self):
    mock_pipeline = test_helper.get_mock_pipeline(
        [helper.PROCESS_TEXT, helper.ANALYZE, helper.FINISH_DOCUMENT])

    _process = process.Subscriber(mock_pipeline)
    _process.setup({})

    doc = document.get_document('mock')
    doc.status = 'untouched'
    doc.text = 'abcd'

    _process.consume(doc, None)

    self.assertNotEqual('untouched', doc.status)
    self.assertEquals(4, doc.meta['size'])
    self.assertNotEqual(0, len(mock_pipeline.consumer.produced))

  def test_size_not_overriden(self):
    mock_pipeline = test_helper.get_mock_pipeline(
        [helper.PROCESS_TEXT, helper.ANALYZE, helper.FINISH_DOCUMENT])

    _process = process.Subscriber(mock_pipeline)
    _process.setup({})

    doc = document.get_document('mock')
    doc.set_size(100)
    doc.text = 'dcba'

    _process.consume(doc, None)

    self.assertEquals(100, doc.meta['size'])

if __name__ == '__main__':
  unittest.main()
