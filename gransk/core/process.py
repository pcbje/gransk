#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json

import gransk.core.abstract_subscriber as abstract_subscriber
import gransk.core.helper as helper


class Subscriber(abstract_subscriber.Subscriber):
  """Module for producing common processing events on a document."""
  CONSUMES = [helper.RUN_PIPELINE]

  def consume(self, doc, _):
    """
    Run a document through processing events.

    :param doc: Document to process.
    :type doc: ``gransk.core.document.Document``
    """
    if doc.meta['size'] < 0:
      doc.set_size(len(doc.text))

    doc.text = '%s\x00%s' % (doc.text, json.dumps(doc.meta, ensure_ascii=False))

    self.produce(helper.PROCESS_TEXT, doc, None)
    self.produce(helper.ANALYZE, doc, None)
    doc.status = 'processed'
    self.produce(helper.FINISH_DOCUMENT, doc, None)
