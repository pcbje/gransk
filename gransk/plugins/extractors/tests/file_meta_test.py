#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import unittest
import json

from io import BytesIO

import gransk.core.helper as helper
import gransk.core.tests.test_helper as test_helper
import gransk.core.document as document
import gransk.plugins.extractors.file_meta as file_meta


class FileMetaTest(unittest.TestCase):

  def test_simple(self):
    _file_meta = file_meta.Subscriber(test_helper.get_mock_pipeline([]))
    response = json.dumps({'Content-Type': 'image/jpeg'}).encode('utf-8')
    _file_meta.setup({
        'data_root': 'local_data',
        'code_root': '.',
        'worker_id': 1,
        'host': 'mock',
        helper.INJECTOR: test_helper.MockInjector(response)
    })

    doc = document.get_document('mock.txt')

    _file_meta.consume(doc, BytesIO(b'mock'))

    expected = 'picture'
    actual = doc.doctype

    self.assertEqual(expected, actual)


if __name__ == '__main__':
  unittest.main()
