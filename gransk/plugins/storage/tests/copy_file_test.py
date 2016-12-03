#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import unittest

from io import BytesIO
import shutil

import gransk.core.helper as helper
import gransk.core.tests.test_helper as test_helper
import gransk.core.document as document
import gransk.plugins.storage.copy_file as copy_file


class CopyFileTest(unittest.TestCase):

  def get_test_file(self, filename):
    path = os.path.realpath(__file__)
    return os.path.join(
        os.path.abspath(os.path.join(path, os.pardir)), 'test_data', filename)

  def test_simple(self):
    mock_pipeline = test_helper.get_mock_pipeline([])

    data_root = os.path.join('local_data', 'unittests')

    if os.path.exists(data_root):
      shutil.rmtree(data_root)

    _copy = copy_file.Subscriber(mock_pipeline)
    _copy.setup({
        helper.DATA_ROOT: data_root,
        u'workers': 1,
        u'tag': 'default',
        helper.COPY_EXT: ['xyz']
    })

    _copy.consume(document.get_document('mock.xyz'), BytesIO(b'juba.'))
    _copy.consume(document.get_document('ignore.doc'), BytesIO(b'mock'))

    expected = ['39bbf948-mock.xyz']

    actual = os.listdir(os.path.join(data_root, 'files', 'xyz'))

    self.assertEqual(expected, actual)


if __name__ == '__main__':
  unittest.main()
