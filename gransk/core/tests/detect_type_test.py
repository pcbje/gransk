#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os
import unittest
from six import StringIO

import yaml

import gransk.core.helper as helper
import gransk.core.detect_type as detect_type
import gransk.core.tests.test_helper as test_helper
import gransk.core.document as document


class DetectTypeTest(unittest.TestCase):

  def get_test_file(self, filename):
    path = os.path.realpath(__file__)
    return os.path.join(
        os.path.abspath(os.path.join(path, os.pardir)), 'test_data', filename)

  def _run_test(self, filename):
    mock_pipeline = test_helper.get_mock_pipeline([
        helper.DOCUMENT, helper.PICTURE,
        helper.ARCHIVE, helper.DISKIMAGE])

    detector = detect_type.Subscriber(mock_pipeline)

    with open('config.yml') as inp:
      detector.setup(yaml.load(inp.read()))

    doc = document.get_document(filename)

    detector.consume(doc, StringIO('dummy'))

    return doc

  def test_detect_picture(self):
    self.assertEquals(self._run_test('dummy.png').meta['type'], helper.PICTURE)

  def test_detect_archive(self):
    self.assertEquals(self._run_test('dummy.zip').meta['type'], helper.ARCHIVE)

  def test_detect_blob(self):
    self.assertEquals(self._run_test(
        self.get_test_file('blob.bin')).meta['type'], helper.DISKIMAGE)

  def test_not_accepted(self):
    self.assertEquals(
        self._run_test('.DS_Store').status, helper.IGNORED)


if __name__ == '__main__':
  unittest.main()
