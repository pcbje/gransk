#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import unittest
import os
import yaml

import gransk.core.document as document
import gransk.core.helper as helper
import gransk.core.tests.test_helper as test_helper
import gransk.plugins.extractors.tika_extractor as tika_extractor


class TikaExtractorTest(unittest.TestCase):

  def get_test_file(self, filename):
    path = os.path.realpath(__file__)
    return os.path.join(
        os.path.abspath(os.path.join(path, os.pardir)), 'test_data', filename)

  def test_simple(self):
    mock_pipeline = test_helper.get_mock_pipeline([
        helper.DOCUMENT, helper.TEXT])

    extractor = tika_extractor.Subscriber(mock_pipeline)

    expected = (
        'This is an unstructured document containing the \nidentifier '
        '"193.34.2.1" (ip address), stored as a PDF document.')

    with open('config.yml') as inp:
      config = yaml.load(inp.read())

    config[helper.DATA_ROOT] = 'local_data'
    config[helper.WORKER_ID] = 1
    config[helper.INJECTOR] = test_helper.MockInjector(response_text=expected)
    extractor.setup(config)

    path = self.get_test_file('document.pdf')

    doc = document.get_document(path)
    doc.meta['Content-Type'] = 'application/pdf'

    with open(doc.path, 'rb') as file_object:
      extractor.consume(doc, file_object)

    actual = doc.text

    self.assertEqual(expected, actual)


if __name__ == '__main__':
  unittest.main()
