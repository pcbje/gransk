#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import gzip
import math
import re as regex
import json
from collections import defaultdict
import os
from six.moves import range

import gransk.core.helper as helper


import gransk.core.abstract_subscriber as abstract_subscriber


class Subscriber(abstract_subscriber.Subscriber):
  """
  Class for finding names in text based on a provided list of tokens. This
  approach has the benefit over other Named Entity Extraction approaches that
  it is independent of the context in which the names are. It may thus be a
  good supplement to improve entity recognition.
  """
  CONSUMES = [helper.PROCESS_TEXT]

  def setup(self, config):
    """
    Load name model (word list) and compile regexes for stop characters.

    :param config: Configuration object.
    :type config: ``dict``
    """
    reference_model = os.path.join(
        config[helper.CODE_ROOT], config[helper.NAME_MODEL])

    self.stopper = regex.compile(('(%s)' % '|'.join([
        'and', 'or', 'og', 'eller', r'\?', '&', '<', '>', '@', ':', ';', '/',
        r'\(', r'\)', 'i', 'of', 'from', 'to', r'\n', '!'])),
        regex.I | regex.MULTILINE)

    self.semistop = regex.compile(
        ('(%s)' % '|'.join([','])), regex.I | regex.MULTILINE)
    self.size_probability = [0.000, 0.000, 0.435, 0.489, 0.472, 0.004, 0.000]
    self.threshold = 0.25
    self.candidates = defaultdict(int)

    with gzip.open(reference_model, 'rb') as inp:
      self.model = json.loads(inp.read().decode('utf-8'))

    self.tokenizer = regex.compile(r'\w{2,20}')

  def _extract(self, text):
    if not text:
      return
    token_buffer = [('', (-1, -1))] * 4

    for index, token in enumerate(self.tokenizer.finditer(text)):
      relative_index = index % len(token_buffer)
      token_buffer[relative_index] = (
          token.group(), (token.start(), token.end()))

      probability = 0
      prev_token_start = -1

      for token_distance in range(len(token_buffer)):
        buffer_index = (relative_index - token_distance) % len(token_buffer)
        buffered_token, (token_start, token_end) = token_buffer[buffer_index]
        is_lowercase = buffered_token == buffered_token.lower()
        token_probability = self.model.get(buffered_token.lower(), 0)

        if is_lowercase or not token_probability:
          break

        if token_distance > 0:
          gap = text[token_end:prev_token_start]

          if self.stopper.search(gap):
            break

          token_probability *= math.sqrt(float(1) / len(gap))

        prev_token_start = token_start
        probability += token_probability
        avg_probability = (probability / (token_distance + 1))
        score = avg_probability * self.size_probability[token_distance + 1]

        if score >= self.threshold:
          yield token_start, text[token_start:token.end()]

        if token_distance > 0 and self.semistop.search(gap):
          break

  def consume(self, doc, _):
    """
    Find names in documents based on the provided word list.

    :param doc: Document object.
    :type doc: ``gransk.core.document.Document``
    """
    entities = doc.entities

    for start, name in self._extract(doc.text):
      entities.add(start, 'per', name)
