#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import six
from six import text_type as unicode

import gransk.core.helper as helper
import gransk.core.abstract_subscriber as abstract_subscriber


class Subscriber(abstract_subscriber.Subscriber):
  """Class for finding named entities in text using the Polyglot NER package."""
  CONSUMES = [helper.PROCESS_TEXT]

  def setup(self, config):
    """
    Load Polyglot NER pakcage.

    :param config: Configuration object.
    :type config: ``dict``
    """
    self.polyglot = config[helper.INJECTOR].get_polyglot()

  def consume(self, doc, _):
    """
    Find names in documents using Polyglot NER.

    :param doc: Document object.
    :type doc: ``gransk.core.document.Document``
    """
    if not doc.text:
      return

    parsed = self.polyglot(doc.text.replace('\x00', ' '))

    try:
      entities = parsed.entities
    except ValueError:
      return

    for entity in entities:
      entity_str = ' '.join(entity)

      if entity_str.endswith('’s') or entity_str.endswith('\'s'):
        entity_str = entity_str[0:-2]

      _type = entity.tag.split('-')[-1].lower()

      if entity_str in doc.text:
        doc.entities.add(entity[0].offset, _type, entity_str)
