#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os
import unittest

import gransk.core.helper as helper
import gransk.core.file_collector as file_collector


class FileCollectorTest(unittest.TestCase):

  def setUp(self):
    path = os.path.realpath(__file__)
    self.test_dir = os.path.join(
        os.path.abspath(os.path.join(path, os.pardir)),
        'test_data', 'collector')

  def test_simple(self):
    _collector = file_collector.Collector({})
    expected = ['a.csv', 'b.txt']
    actual = [os.path.basename(x) for x in _collector.collect(self.test_dir)]
    self.assertEquals(expected, actual)

  def test_in_filter(self):
    _collector = file_collector.Collector({helper.IN_FILTER: ['a.']})
    expected = ['a.csv']
    actual = [os.path.basename(x) for x in _collector.collect(self.test_dir)]
    self.assertEquals(expected, actual)

  def test_end_filter(self):
    _collector = file_collector.Collector({helper.END_FILTER: ['txt']})
    expected = ['b.txt']
    actual = [os.path.basename(x) for x in _collector.collect(self.test_dir)]
    self.assertEquals(expected, actual)

  def test_negate(self):
    _collector = file_collector.Collector(
        {helper.END_FILTER: ['txt'], helper.NEGATE: 1})
    expected = ['a.csv']
    actual = [os.path.basename(x) for x in _collector.collect(self.test_dir)]
    self.assertEquals(expected, actual)

  def test_file(self):
    _collector = file_collector.Collector({helper.END_FILTER: ['csv']})
    expected = ['a.csv']
    actual = [
        os.path.basename(x) for x in _collector.collect(
            os.path.join(self.test_dir, 'a.csv'))]
    self.assertEquals(expected, actual)


if __name__ == '__main__':
  unittest.main()
