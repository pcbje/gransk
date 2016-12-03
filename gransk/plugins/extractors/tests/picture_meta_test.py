#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import unittest
import os

import gransk.core.helper as helper
import gransk.core.tests.test_helper as test_helper
import gransk.core.document as document
import gransk.plugins.extractors.picture_meta as picture_meta


class PictureMetaTest(unittest.TestCase):

  def get_test_file(self, filename):
    path = os.path.realpath(__file__)
    return os.path.join(
        os.path.abspath(os.path.join(path, os.pardir)), 'test_data', filename)

  def test_match(self):
    _picture_meta = picture_meta.Subscriber(None)
    _picture_meta.setup({})

    doc = document.get_document('mock')

    with open(self.get_test_file('picture.jpg'), 'rb') as file_object:
      _picture_meta.consume(doc, file_object)

    self.assertEqual(640, doc.meta.get('img_width'))
    self.assertEqual(480, doc.meta.get('img_height'))

  def test_no_match(self):
    _picture_meta = picture_meta.Subscriber(None)
    _picture_meta.setup({})

    doc = document.get_document('mock')

    with open(self.get_test_file('document.pdf'), 'rb') as file_object:
      _picture_meta.consume(doc, file_object)

    self.assertEqual(None, doc.meta.get('img_width'))
    self.assertEqual(None, doc.meta.get('img_height'))


if __name__ == '__main__':
  unittest.main()
