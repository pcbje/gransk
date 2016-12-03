#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import unittest

try:
  from StringIO import StringIO
except ImportError:
  from io import StringIO

import gransk.core.helper as helper
import gransk.core.tests.test_helper as test_helper
import gransk.core.document as document
import gransk.plugins.extractors.strings as strings


class StringsTest(unittest.TestCase):

  def test_base(self):
    pipe = test_helper.get_mock_pipeline([helper.RUN_PIPELINE])
    _strings = strings.Subscriber(pipe)
    _strings.setup({
        'min_string_length': 4,
        'max_lines': 2
    })

    doc = document.get_document('mock')
    doc.set_size(12345)

    _strings.consume(doc, StringIO('AAAA\x00BBBB\x00CCCC'))

    # Two child documents produced.
    self.assertEquals(2, len(pipe.consumer.produced))

    expected = 'mock.00000.child'
    actual = pipe.consumer.produced[0][0].path

    self.assertEquals(expected, actual)

if __name__ == '__main__':
  unittest.main()
