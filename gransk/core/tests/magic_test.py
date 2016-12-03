#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import unittest

from io import BytesIO

import gransk.core.tests.test_helper as test_helper
import gransk.core.document as document
import gransk.core.magic as magic


class MagicTest(unittest.TestCase):

  def test_simple(self):
    pipe = test_helper.get_mock_pipeline([])

    mock_mod = test_helper.MockSubscriber()
    mock_mod = test_helper.MockSubscriber()

    pipe.register_magic(b'\xFF\xEE\xDD', ('mock', mock_mod.consume))
    pipe.register_magic(b'\x00\x00\x00', ('mock', mock_mod.consume))

    _magic = magic.Subscriber(pipe)
    _magic.setup(None)

    doc = document.get_document('mock')

    content = b'\xFF\xEE\xDDMOCKMOCKMOCK'

    _magic.consume(doc, BytesIO(content))

    self.assertEquals(True, doc.magic_hit)
    self.assertEquals(1, len(mock_mod.produced))

    expected = content
    actual = mock_mod.produced[0][1].read()

    self.assertEquals(expected, actual)

if __name__ == '__main__':
  unittest.main()
