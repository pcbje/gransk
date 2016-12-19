#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import unittest

import gransk.core.document as document
import gransk.plugins.find.find_names_brute as _find_names
import gransk.core.tests.test_helper as test_helper

logging.getLogger('polyglot').setLevel(logging.ERROR)


class FindNamesBruteTest(unittest.TestCase):

  def test_simple(self):
    config = {
        'code_root': '.',
        'name_model': 'utils/names.gz'
    }
    find_names = _find_names.Subscriber(test_helper.get_mock_pipeline([]))
    find_names.setup(config)
    doc = document.get_document('dummy')
    doc.text = u'Dette  er Tom Martin.'
    find_names.consume(doc, None)
    expected = [(10, {
        u'entity_id': u'tom_martin',
        u'type': u'per',
        u'value': u'Tom Martin'
    })]
    self.assertEqual(expected, doc.entities.get_all())

  def test_bug(self):
    text = u"""MT-2009-12-015-W001 – SIMULATED WARRANT
Computers assigned to Jo Smith from November 13, 2009 to December 12, 2009.
"""
    config = {
        'code_root': '.',
        'name_model': 'utils/names.gz'
    }
    find_names = _find_names.Subscriber(test_helper.get_mock_pipeline([]))
    find_names.setup(config)
    doc = document.get_document('dummy')
    doc.text = text
    find_names.consume(doc, None)
    expected = [(62, {
        u'entity_id': u'jo_smith',
        u'type': u'per',
        u'value': u'Jo Smith'
    })]
    self.assertEqual(expected, doc.entities.get_all())


  def test_bug_2(self):
    text = u""" os setup( name='recgonizer', author='Petter Christian Bjelland', version='0.3',"""
    config = {
        'code_root': '.',
        'name_model': 'utils/names.gz'
    }
    find_names = _find_names.Subscriber(test_helper.get_mock_pipeline([]))
    find_names.setup(config)
    doc = document.get_document('dummy')
    doc.text = text
    find_names.consume(doc, None)
    self.assertEqual(2, len(doc.entities.get_all()))


if __name__ == '__main__':
  unittest.main()
