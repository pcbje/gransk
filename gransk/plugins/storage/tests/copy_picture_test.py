#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import unittest
try:
  from StringIO import StringIO
except ImportError:
  from io import StringIO
import shutil

import gransk.core.helper as helper
import gransk.core.tests.test_helper as test_helper
import gransk.core.document as document
import gransk.plugins.storage.copy_picture as copy_picture


class CopyPictureTest(unittest.TestCase):

  def get_test_file(self, filename):
    path = os.path.realpath(__file__)
    return os.path.join(
        os.path.abspath(os.path.join(path, os.pardir)), 'test_data', filename)

  def test_simple(self):
    mock_pipeline = test_helper.get_mock_pipeline([])

    data_root = os.path.join('local_data', 'unittests')

    if os.path.exists(data_root):
      shutil.rmtree(data_root)

    _copy_picture = copy_picture.Subscriber(mock_pipeline)
    _copy_picture.setup({
        helper.DATA_ROOT: data_root,
        u'workers': 1,
        u'tag': 'default',
    })

    doc = document.get_document('mock.jpg')
    doc.meta['type'] = 'picture'

    with open(self.get_test_file('gransk-logo.png'), 'rb') as inp:
      _copy_picture.consume(doc, inp)

    expected = '6913571e-mock.jpg'

    actual = os.listdir('local_data/unittests/pictures')

    self.assertEqual([expected], actual)
    self.assertEqual(expected, doc.meta['picture'])


if __name__ == '__main__':
  unittest.main()
