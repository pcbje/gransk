#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import logging
import os
import re

import gransk.core.abstract_subscriber as abstract_subscriber
import gransk.core.helper as helper

LOGGER = logging.getLogger('magic')


class Subscriber(abstract_subscriber.Subscriber):
  """Identify extractor subscribers based on file header."""
  CONSUMES = [helper.MAGIC]

  def setup(self, _):
    """Compile file headers for all magic extractors into a regex pattern."""
    self.pattern = re.compile(b'|'.join(list(self.pipeline.magic.keys())))

  def consume(self, doc, payload):
    """
    Identify extractors and call their callback functions.

    :param doc: The document object.
    :param payload: The document object.
    :type doc: ``gransk.core.document.Document``
    :type payload: ``file``
    """
    sample = payload.read(64)
    payload.seek(0)

    hit = self.pattern.match(sample)

    if not hit:
      return

    filename = os.path.basename(doc.path)
    doc.magic_hit = True

    for listener, callback in self.pipeline.magic[hit.group()]:
      LOGGER.debug('magic -> %s (%s)', listener, filename)
      callback(doc, payload)
