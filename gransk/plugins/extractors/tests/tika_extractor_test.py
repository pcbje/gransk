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
        b'This is an unstructured document containing the \nidentifier '
        b'"193.34.2.1" (ip address), stored as a PDF document.')

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

    self.assertEqual(expected.decode('utf-8'), actual)

  def test_scanned_pdf(self):
    mock_pipeline = test_helper.get_mock_pipeline([
        helper.DOCUMENT, helper.TEXT])
    mock_injector = test_helper.MockInjector()

    extractor = tika_extractor.Subscriber(mock_pipeline)

    expected_headers = {
      'Content-Disposition': 'attachment; filename=scanned.pdf.tiff',
      'Content-type': 'image/tiff',
      'X-Tika-OCRLanguage': 'eng+rus'
    }

    with open('config.yml') as inp:
      config = yaml.load(inp.read())

    config[helper.DATA_ROOT] = 'local_data'
    config[helper.WORKER_ID] = 1
    config[helper.OCR_LANGUAGES] = 'eng+rus'
    config[helper.INJECTOR] = mock_injector
    extractor.setup(config)

    path = self.get_test_file('scanned.pdf')

    doc = document.get_document(path)
    doc.meta['Content-Type'] = 'application/pdf'

    with open(doc.path, 'rb') as file_object:
      extractor.consume(doc, file_object)

    actual_headers = mock_injector.http_connection.request_headers

    self.assertEqual(expected_headers, actual_headers)


if __name__ == '__main__':
  unittest.main()
