#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import unittest

import gransk.core.helper as helper
import gransk.core.tests.test_helper as test_helper
import gransk.core.document as document
import gransk.plugins.unpackers.unpack_diskimage as unpack_diskimage


class UnpackDiskimageTest(unittest.TestCase):

  def setUp(self):
    self.mock_pipe = test_helper.get_mock_pipeline(
        [helper.PROCESS_FILE, helper.TEXT])

    self.detector = unpack_diskimage.Subscriber(self.mock_pipe)
    self.detector.setup({
        u'max_file_size': 1,
        helper.DATA_ROOT: 'local_data',
        u'code_root': '.'
    })

  def test_simple(self):
    doc = document.get_document(test_helper.get_test_path('dummy.E01'))
    doc.docid = '4321'

    with open(doc.path) as inp:
      self.detector.consume(doc, inp)

    actual = [doc.path for doc, _ in self.mock_pipe.consumer.produced]

    expected = [
        u'/DUMMY       (Volume Label Entry)',
        u'/test/file-a.txt',
        u'/file-b.txt'
    ]

    self.assertEquals(expected, actual)

  def _test_big(self):
    doc = document.get_document('/data/cfreds_2015_data_leakage_pc.E01')
    doc.docid = '4321'

    with open(doc.path) as inp:
      self.detector.consume(doc, inp)


if __name__ == '__main__':
  unittest.main()
