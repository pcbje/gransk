#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import unittest
import re

import gransk.core.document as document
import gransk.plugins.extractors.ewf_strings as ewf_strings


class EwfStringsTest(unittest.TestCase):

  def test_simple(self):
    _strings = ewf_strings.Subscriber(None)
    _strings.setup({'min_string_length': 12})

    doc = document.get_document('mock')

    with open('gransk/plugins/unpackers/tests/test_data/dummy.E01', 'rb') as inp:
      _strings.consume(doc, inp)

    expected = (u"IDUMMY      FAT12"
                u"Non-system disk"
                u"Press any key to reboot"

                u"DUMMY      ("
                u"~1      TRA\""
                u"FILE-B  TXT"
                u".          2"
                u"Mac OS X"
                u"This resource fork intentionally left blank"
                u".          2"
                u"FSEVEN~1"
                u"000000~1"
                u"000000~2"
                u"D3E90FC1-F0EF-427D-B874-2BECB6BEA409"
                u".          0"
                u"FILE-A  TXT"
                u"Hi, I'm file A."
                u"And I'm file B.")

    actual = doc.text

    self.assertNotEqual(None, actual)
    self.assertEqual(re.sub(r'\s', u'', expected), re.sub(r'\s', u'', actual))


if __name__ == '__main__':
  unittest.main()
