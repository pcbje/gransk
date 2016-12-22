#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os
import unittest
import shutil

import gransk.core.helper as helper
import gransk.core.tests.test_helper as test_helper
import gransk.core.document as document
import gransk.plugins.storage.store_text as store_text


class StoreTextTest(unittest.TestCase):

  def test_simple(self):
    mock_pipeline = test_helper.get_mock_pipeline([])

    data_root = os.path.join('local_data', 'unittests')

    if os.path.exists(data_root):
      shutil.rmtree(data_root)

    _store_text = store_text.Subscriber(mock_pipeline)
    _store_text.setup({
        helper.DATA_ROOT: data_root,
        'workers': 1
    })

    doc = document.get_document('mock')
    doc.text = 'mock-mock-mock'

    _store_text.consume(doc, None)

    expected = 'local_data/unittests/text/17404a59-mock'
    actual = doc.meta['text_file']

    self.assertEquals(expected, actual)


if __name__ == '__main__':
  unittest.main()
