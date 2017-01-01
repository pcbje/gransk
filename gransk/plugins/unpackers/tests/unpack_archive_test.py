#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import unittest

import gransk.core.helper as helper
import gransk.core.tests.test_helper as test_helper
import gransk.core.document as document
import gransk.plugins.unpackers.unpack_archive as unpack_archive


class UnapckArchiveTest(unittest.TestCase):

  def test_simple(self):
    mock_pipe = test_helper.get_mock_pipeline(
        [helper.PROCESS_FILE, helper.TEXT])

    detector = unpack_archive.Subscriber(mock_pipe)
    detector.setup({
        helper.DATA_ROOT: 'local_data',
        helper.TAG: 'test',
        helper.WORKER_ID: 0
    })

    doc = document.get_document(test_helper.get_test_path('two_files.zip'))

    doc.docid = '4321'
    doc.meta['Content-Type'] = 'application/zip'

    with open(doc.path, 'rb') as inp:
      detector.consume(doc, inp)

    self.assertEqual(2, len(mock_pipe.consumer.produced))
    self.assertEqual(
        'txt',
        mock_pipe.consumer.produced[1][0].path.split('/')[-1].split('.')[-1])

  def test_encrypted(self):
    mock_pipe = test_helper.get_mock_pipeline(
        [helper.PROCESS_FILE, helper.TEXT])

    detector = unpack_archive.Subscriber(mock_pipe)
    detector.setup({
        helper.DATA_ROOT: 'local_data',
        helper.TAG: 'test',
        helper.WORKER_ID: 0
    })

    doc = document.get_document(test_helper.get_test_path('password-protected.zip'))

    doc.docid = '4321'
    doc.meta['Content-Type'] = 'application/zip'

    with open(doc.path, 'rb') as inp:
      detector.consume(doc, inp)

    self.assertEqual(1, len(mock_pipe.consumer.produced))


if __name__ == '__main__':
  unittest.main()
