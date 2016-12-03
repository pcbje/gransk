#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import unittest

import gransk.boot.run
import gransk.core.helper as helper
import gransk.core.tests.test_helper as test_helper


class RunTest(unittest.TestCase):

  def test_simple(self):
    worker = gransk.boot.run.Worker()
    expected = ['README.md']
    actual = worker.boot(test_helper, {}, 'README.md')
    self.assertEquals(expected, actual)

  def test_max_file_size(self):
    worker = gransk.boot.run.Worker()
    expected = ['README.md']
    actual = worker.boot(test_helper, {'max_file_size': 0.0000001}, 'README.md')
    self.assertEquals(expected, actual)

  def test_parse_args(self):
    parsed_args = gransk.boot.run.parse_args(['-c', 'other.yml', 'mock'])
    self.assertEquals('other.yml', parsed_args.config)
    self.assertEquals('mock', parsed_args.path)

  def test_load_config(self):
    parsed_args = gransk.boot.run.parse_args(['mock'])
    gransk_api = gransk.boot.run.load_config(parsed_args)
    self.assertNotEqual(0, len(gransk_api.config['subscribers']))

  def test_run(self):
    inject = test_helper.MockInjector()
    gransk.boot.run.run(inject, ['mock'])
    self.assertEquals(True, inject.worker.called)


if __name__ == '__main__':
  unittest.main()
