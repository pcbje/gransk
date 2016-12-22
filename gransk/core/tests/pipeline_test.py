#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import unittest

import gransk.core.pipeline as pipeline


class PipelineTest(unittest.TestCase):

  def test_build_pipeline(self):
    config = {
        'subscribers': ['gransk.core.detect_type']
    }

    pipe = pipeline.build_pipeline(config)

    self.assertEquals(len(pipe.subscribers), 1)

    pipe.stop()


if __name__ == '__main__':
  unittest.main()
