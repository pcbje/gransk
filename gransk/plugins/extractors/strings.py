#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import string

import gransk.core.abstract_subscriber as abstract_subscriber
import gransk.core.helper as helper
import gransk.core.document as document


class Subscriber(abstract_subscriber.Subscriber):
  """
  Class for extracting raw content from documents when no other extractor
  has succeeded. Imitated Unix 'strings' command.
  """
  CONSUMES = [helper.RAW]

  def setup(self, config):
    """
    Load configuration.

    :param config: Configuration object.
    :type config: ``dict``
    """
    self.buffer_size = 4096
    self.min_string_length = config.get(helper.MIN_STRING_LENGTH, 8)
    self.max_lines = config.get(helper.MAX_LINES, 1000)
    self.printable = set(
        '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r')

  def __strings(self, payload):
    result = ''
    data = payload.read(self.buffer_size)
    while data:
      for char in data:
        if isinstance(char, int):
          char = chr(char)
        if char in self.printable:
          result += char
          continue
        if len(result) >= self.min_string_length:
          yield result
        result = ''
      data = payload.read(self.buffer_size)

    if len(result) >= self.min_string_length:
      yield result

  def _produce_child_doc(self, doc, text, offset):
    base = '%%s.%%0%sd.child' % max(len('%s' % doc.meta['size']), 1)
    new_doc = document.get_document(base % (doc.path, offset), parent=doc)
    new_doc.tag = doc.tag
    new_doc.text = text
    doc.children += 1
    self.produce(helper.RUN_PIPELINE, new_doc, new_doc.text)

  def consume(self, doc, payload):
    """
    Extract raw content from document file object.

    :param doc: Document object.
    :param payload: File pointer beloning to document.
    :type doc: ``gransk.core.document.Document``
    :type payload: ``file``
    """
    text = []

    offset = payload.tell()

    for line in self.__strings(payload):
      text.append(line)
      if len(text) == self.max_lines:
        self._produce_child_doc(doc, '\n'.join(text), offset)
        text = []
        offset = payload.tell()

    if len(text) > 0:
      if doc.children > 0:
        self._produce_child_doc(doc, '\n'.join(text), offset)
      else:
        doc.text = '\n'.join(text)

    payload.seek(0)
