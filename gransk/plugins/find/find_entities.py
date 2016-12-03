#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import re as regex
import socket

import gransk.core.helper as helper
import gransk.core.abstract_subscriber as abstract_subscriber


class Subscriber(abstract_subscriber.Subscriber):
  """Class for finding entities in text based on regular expressions."""

  CONSUMES = [helper.PROCESS_TEXT]

  def setup(self, config):
    """
    Compile configured regular expressions.

    :param config: Configuration object.
    :type config: ``dict``
    """
    self.matches = {}

    patterns = []

    for entity_type, pattern_conf in config.get(helper.ENTITIES, {}).items():
      patterns.append(
          u'(?P<{}>{})'.format(entity_type, pattern_conf[helper.PATTERN]))

    self.pattern = regex.compile(
        u'(?:\s|^|[^a-z0-9]){}(?:\s|$|[^a-z0-9])'.format('|'.join(patterns)),
        regex.I)

  def consume(self, doc, _):
    """
    Find entities in documents matching compiled regular expression.

    :param doc: Document object.
    :type doc: ``gransk.core.document.Document``
    """
    if not doc.text:
      return

    entities = doc.entities

    for result in self.pattern.finditer(doc.text):
      entity_value = result.group(result.lastgroup)

      if result.lastgroup == u'ip_addr':
        try:
          socket.inet_aton(entity_value)
        except socket.error:
          continue

      entities.add(
          result.start(result.lastgroup), result.lastgroup, entity_value)
