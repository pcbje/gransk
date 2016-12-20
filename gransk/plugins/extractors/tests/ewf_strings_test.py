#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

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

    expected = ('IDUMMY      FAT12'
                'Non-system disk'
                'Press any key to reboot'

                'DUMMY      ('
                '~1      TRA"'
                'FILE-B  TXT'
                '.          2'
                'Mac OS X'
                'This resource fork intentionally left blank'
                '.          2'
                'FSEVEN~1'
                '000000~1'
                '000000~2'
                'D3E90FC1-F0EF-427D-B874-2BECB6BEA409'
                '.          0'
                'FILE-A  TXT'
                "Hi, I'm file A."
                "And I'm file B.")

    actual = doc.text

    self.assertNotEqual(None, actual)
    self.assertEqual(re.sub(r'\s', '', expected), re.sub(r'\s', '', actual))


if __name__ == '__main__':
  unittest.main()
