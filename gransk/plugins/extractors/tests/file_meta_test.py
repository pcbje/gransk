#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import unittest
import json

try:
  from StringIO import StringIO
except ImportError:
  from io import StringIO

import gransk.core.helper as helper
import gransk.core.tests.test_helper as test_helper
import gransk.core.document as document
import gransk.plugins.extractors.file_meta as file_meta


class FileMetaTest(unittest.TestCase):

  def test_simple(self):
    _file_meta = file_meta.Subscriber(test_helper.get_mock_pipeline([]))
    response = json.dumps({'Content-Type': 'image/jpeg'}).encode('utf-8')
    _file_meta.setup({
        'code_root': '.',
        'host': 'mock',
        helper.INJECTOR: test_helper.MockInjector(response)
    })

    doc = document.get_document('mock.txt')

    _file_meta.consume(doc, StringIO('mock'))

    expected = 'picture'
    actual = doc.doctype

    self.assertEqual(expected, actual)


if __name__ == '__main__':
  unittest.main()
